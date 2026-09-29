"""
Вариант 11. Уточнение линейного МКЭ сглаживающим кубическим сплайном Эрмита (2D).

Функционал:
  F(q) = Σ ω_k (P(x_k) - f_k)^2
       + α ∬ (|∇P|^2) dΩ
       + β ∬ (P_xx^2 + P_yy^2) dΩ

Локальные матрицы регуляризации считаются через L-координаты
и формулу интегрирования (5.76) из учебника.
"""

from __future__ import annotations

import copy
import json
import math
from collections import defaultdict

import gmsh

from sparse_matrix import Matrix


# ---------------------------------------------------------------------------
# Многочлены от L1, L2, L3 + точное интегрирование (5.76)
# ---------------------------------------------------------------------------

class LPoly:
    """Σ c_{abc} L1^a L2^b L3^c."""

    __slots__ = ("terms",)

    def __init__(self, terms=None):
        self.terms = defaultdict(float)
        if terms:
            for key, value in terms.items():
                if abs(value) > 1e-30:
                    self.terms[key] += value

    def copy(self):
        return LPoly(self.terms)

    def __add__(self, other):
        out = self.copy()
        for key, value in other.terms.items():
            out.terms[key] += value
        return out

    def __sub__(self, other):
        out = self.copy()
        for key, value in other.terms.items():
            out.terms[key] -= value
        return out

    def scale(self, coefficient):
        if abs(coefficient) < 1e-30:
            return LPoly()
        return LPoly({key: value * coefficient for key, value in self.terms.items()})

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.scale(other)
        out = LPoly()
        for (a1, b1, c1), v1 in self.terms.items():
            for (a2, b2, c2), v2 in other.terms.items():
                out.terms[(a1 + a2, b1 + b2, c1 + c2)] += v1 * v2
        return out

    def __rmul__(self, other):
        return self.__mul__(other)

    def diff(self, dL):
        """Производная по направлению: dL = (∂L1, ∂L2, ∂L3) — константы."""
        out = LPoly()
        d1, d2, d3 = dL
        for (a, b, c), coeff in self.terms.items():
            if a:
                out.terms[(a - 1, b, c)] += coeff * a * d1
            if b:
                out.terms[(a, b - 1, c)] += coeff * b * d2
            if c:
                out.terms[(a, b, c - 1)] += coeff * c * d3
        return out

    def integrate(self, det_abs):
        """∬ poly dΩ = Σ c * a!b!c! / (a+b+c+2)! * |det D|."""
        total = 0.0
        for (a, b, c), coeff in self.terms.items():
            if abs(coeff) < 1e-30:
                continue
            total += (
                coeff
                * math.factorial(a)
                * math.factorial(b)
                * math.factorial(c)
                / math.factorial(a + b + c + 2)
                * det_abs
            )
        return total


def _L(i):
    powers = [0, 0, 0]
    powers[i] = 1
    return LPoly({tuple(powers): 1.0})


def build_hermite_polys(nodes_coords):
    """
    10 локальных базисных функций Эрмита как многочлены от L (уч. стр. 296–297).
    Индексы: 0..2 — значения в вершинах, 3 — центр,
    4..6 — ∂/∂x в вершинах, 7..9 — ∂/∂y в вершинах.
    """
    x1, y1 = nodes_coords[0]
    x2, y2 = nodes_coords[1]
    x3, y3 = nodes_coords[2]

    L1, L2, L3 = _L(0), _L(1), _L(2)

    psi = [None] * 10

    psi[0] = (L1 * L1 * 3) - (L1 * L1 * L1 * 2) - (L1 * L2 * L3 * 7)
    psi[1] = (L2 * L2 * 3) - (L2 * L2 * L2 * 2) - (L1 * L2 * L3 * 7)
    psi[2] = (L3 * L3 * 3) - (L3 * L3 * L3 * 2) - (L1 * L2 * L3 * 7)
    psi[3] = L1 * L2 * L3 * 27

    # ψ5 = L1[(x1-x2)L2(L3-L1) + (x1-x3)L3(L2-L1)]
    psi[4] = L1 * (
        (L2 * (L3 - L1)) * (x1 - x2) + (L3 * (L2 - L1)) * (x1 - x3)
    )
    # ψ6 = L2[(x2-x3)L3(L1-L2) + (x2-x1)L1(L3-L2)]  — исправлено по учебнику
    psi[5] = L2 * (
        (L3 * (L1 - L2)) * (x2 - x3) + (L1 * (L3 - L2)) * (x2 - x1)
    )
    # ψ7 = L3[(x3-x1)L1(L2-L3) + (x3-x2)L2(L1-L3)]
    psi[6] = L3 * (
        (L1 * (L2 - L3)) * (x3 - x1) + (L2 * (L1 - L3)) * (x3 - x2)
    )

    psi[7] = L1 * (
        (L2 * (L3 - L1)) * (y1 - y2) + (L3 * (L2 - L1)) * (y1 - y3)
    )
    psi[8] = L2 * (
        (L3 * (L1 - L2)) * (y2 - y3) + (L1 * (L3 - L2)) * (y2 - y1)
    )
    psi[9] = L3 * (
        (L1 * (L2 - L3)) * (y3 - y1) + (L2 * (L1 - L3)) * (y3 - y2)
    )

    return psi


def regularization_local_matrices(nodes_coords, L_coeffs, det_abs, alpha, beta):
    """
    Локальные 10×10 матрицы штрафов.
    L_coeffs[i] = [α0, α1, α2] для Li = α0 + α1 x + α2 y.
    """
    psi = build_hermite_polys(nodes_coords)
    dLx = (L_coeffs[0][1], L_coeffs[1][1], L_coeffs[2][1])
    dLy = (L_coeffs[0][2], L_coeffs[1][2], L_coeffs[2][2])

    dpx = [p.diff(dLx) for p in psi]
    dpy = [p.diff(dLy) for p in psi]
    dpxx = [p.diff(dLx) for p in dpx]
    dpyy = [p.diff(dLy) for p in dpy]

    A_alpha = [[0.0] * 10 for _ in range(10)]
    A_beta = [[0.0] * 10 for _ in range(10)]

    if abs(alpha) > 0.0:
        for i in range(10):
            for j in range(i + 1):
                value = (dpx[i] * dpx[j] + dpy[i] * dpy[j]).integrate(det_abs)
                A_alpha[i][j] = alpha * value
                A_alpha[j][i] = A_alpha[i][j]

    if abs(beta) > 0.0:
        for i in range(10):
            for j in range(i + 1):
                value = (dpxx[i] * dpxx[j] + dpyy[i] * dpyy[j]).integrate(det_abs)
                A_beta[i][j] = beta * value
                A_beta[j][i] = A_beta[i][j]

    return A_alpha, A_beta


# ---------------------------------------------------------------------------
# Конечноэлементный треугольник с базисом Эрмита
# ---------------------------------------------------------------------------

class Element:
    def __init__(self, nodes, number, center_number):
        self.nodes = nodes
        self.functions = [[0.0, 0.0, 0.0] for _ in range(3)]
        self.number = number
        self.center_number = center_number
        self.det_d = 0.0
        self.det_signed = 0.0
        self.nodes_coords = []
        self.loc_pois = []
        self.loc_l_vals = []
        self._psi_cache = None
        self._dLx = None
        self._dLy = None

    def local_to_global(self, local_index):
        if 0 <= local_index <= 2:
            return self.nodes[local_index] * 3
        if local_index == 3:
            return self.center_number - 1
        if 4 <= local_index <= 6:
            return self.nodes[local_index - 4] * 3 + 1
        return self.nodes[local_index - 7] * 3 + 2

    def check_triangle(self, nodes_global):
        self.nodes_coords = [nodes_global[n] for n in self.nodes]
        nodes = self.nodes_coords
        # Знаковый det D (5.74); для площади/интегралов берём модуль.
        self.det_signed = (
            (nodes[1][0] - nodes[0][0]) * (nodes[2][1] - nodes[0][1])
            - (nodes[1][1] - nodes[0][1]) * (nodes[2][0] - nodes[0][0])
        )
        self.det_d = abs(self.det_signed)
        if self.det_d < 1e-15:
            return 1
        self._build_L_coeffs()
        return 0

    def _build_L_coeffs(self):
        nodes = self.nodes_coords
        # D^{-1} по (5.75): делим на знаковый det D, не на модуль.
        det = self.det_signed
        raw = [
            [
                nodes[1][0] * nodes[2][1] - nodes[2][0] * nodes[1][1],
                nodes[1][1] - nodes[2][1],
                nodes[2][0] - nodes[1][0],
            ],
            [
                nodes[2][0] * nodes[0][1] - nodes[0][0] * nodes[2][1],
                nodes[2][1] - nodes[0][1],
                nodes[0][0] - nodes[2][0],
            ],
            [
                nodes[0][0] * nodes[1][1] - nodes[1][0] * nodes[0][1],
                nodes[0][1] - nodes[1][1],
                nodes[1][0] - nodes[0][0],
            ],
        ]
        self.functions = [[raw[i][j] / det for j in range(3)] for i in range(3)]
        self._dLx = (self.functions[0][1], self.functions[1][1], self.functions[2][1])
        self._dLy = (self.functions[0][2], self.functions[1][2], self.functions[2][2])
        self._psi_cache = build_hermite_polys(self.nodes_coords)

    def l_values_at(self, point):
        return [
            self.functions[i][0]
            + self.functions[i][1] * point[0]
            + self.functions[i][2] * point[1]
            for i in range(3)
        ]

    def ret_ermit_value(self, index, l_values):
        """Значение базисной функции (формулы учебника, ψ6/ψ9 исправлены)."""
        L1, L2, L3 = l_values
        nodes = self.nodes_coords
        if index == 0:
            return L1 * (3 * L1 - 2 * L1 ** 2 - 7 * L2 * L3)
        if index == 1:
            return L2 * (3 * L2 - 2 * L2 ** 2 - 7 * L3 * L1)
        if index == 2:
            return L3 * (3 * L3 - 2 * L3 ** 2 - 7 * L1 * L2)
        if index == 3:
            return 27 * L1 * L2 * L3
        if index == 4:
            return L1 * (
                (nodes[0][0] - nodes[1][0]) * L2 * (L3 - L1)
                + (nodes[0][0] - nodes[2][0]) * L3 * (L2 - L1)
            )
        if index == 5:
            return L2 * (
                (nodes[1][0] - nodes[2][0]) * L3 * (L1 - L2)
                + (nodes[1][0] - nodes[0][0]) * L1 * (L3 - L2)
            )
        if index == 6:
            return L3 * (
                (nodes[2][0] - nodes[0][0]) * L1 * (L2 - L3)
                + (nodes[2][0] - nodes[1][0]) * L2 * (L1 - L3)
            )
        if index == 7:
            return L1 * (
                (nodes[0][1] - nodes[1][1]) * L2 * (L3 - L1)
                + (nodes[0][1] - nodes[2][1]) * L3 * (L2 - L1)
            )
        if index == 8:
            return L2 * (
                (nodes[1][1] - nodes[2][1]) * L3 * (L1 - L2)
                + (nodes[1][1] - nodes[0][1]) * L1 * (L3 - L2)
            )
        if index == 9:
            return L3 * (
                (nodes[2][1] - nodes[0][1]) * L1 * (L2 - L3)
                + (nodes[2][1] - nodes[1][1]) * L2 * (L1 - L3)
            )
        raise IndexError(index)

    def _eval_poly_at_L(self, poly, l_values):
        L1, L2, L3 = l_values
        total = 0.0
        for (a, b, c), coeff in poly.terms.items():
            total += coeff * (L1 ** a) * (L2 ** b) * (L3 ** c)
        return total

    def ret_ermit_derivative(self, index, l_values, which):
        """which: 'x' | 'y' | 'xx' | 'yy'."""
        psi = self._psi_cache[index]
        if which == "x":
            return self._eval_poly_at_L(psi.diff(self._dLx), l_values)
        if which == "y":
            return self._eval_poly_at_L(psi.diff(self._dLy), l_values)
        if which == "xx":
            return self._eval_poly_at_L(psi.diff(self._dLx).diff(self._dLx), l_values)
        if which == "yy":
            return self._eval_poly_at_L(psi.diff(self._dLy).diff(self._dLy), l_values)
        raise ValueError(which)

    def add_to_A(self, G_global, pois, weiuse, weifact, alpha=0.0, beta=0.0):
        loc_pois = []
        inds = []
        for pt in range(len(pois["poi"])):
            if self.is_in(pois["poi"][pt]) and not weiuse[pt]:
                weiuse[pt] = True
                loc_pois.append(pois["poi"][pt])
                inds.append(pt)
        print(f"Элемент {self.number}, Попаданий {len(loc_pois)}")
        self.loc_pois = inds

        l_func_values = [self.l_values_at(p) for p in loc_pois]
        self.loc_l_vals = l_func_values

        A = [[0.0] * 10 for _ in range(10)]

        # МНК по точкам измерений
        for i in range(10):
            for j in range(10):
                for k, l_vals in enumerate(l_func_values):
                    wi = weifact[inds[k]]
                    A[i][j] += (
                        wi
                        * self.ret_ermit_value(i, l_vals)
                        * self.ret_ermit_value(j, l_vals)
                    )

        # Регуляризация α (∇) и β (P_xx, P_yy) — точные интегралы через L
        A_alpha, A_beta = regularization_local_matrices(
            self.nodes_coords, self.functions, self.det_d, alpha, beta
        )
        for i in range(10):
            for j in range(10):
                A[i][j] += A_alpha[i][j] + A_beta[i][j]

        for i in range(10):
            igl = self.local_to_global(i)
            for j in range(10):
                jgl = self.local_to_global(j)
                G_global.add_to_elem(igl, jgl, A[i][j])

    def add_to_b(self, b_global, poi_vals, weifact):
        b = [0.0] * 10
        for i in range(10):
            for j, global_idx in enumerate(self.loc_pois):
                b[i] += (
                    weifact[global_idx]
                    * self.ret_ermit_value(i, self.loc_l_vals[j])
                    * poi_vals[global_idx]
                )
        for i in range(10):
            b_global[self.local_to_global(i)] += b[i]

    def is_in(self, point):
        x1 = self.nodes_coords[0][0] - point[0]
        y1 = self.nodes_coords[0][1] - point[1]
        x2 = self.nodes_coords[1][0] - point[0]
        y2 = self.nodes_coords[1][1] - point[1]
        x3 = self.nodes_coords[2][0] - point[0]
        y3 = self.nodes_coords[2][1] - point[1]
        if (not x1 and not y1) or (not x2 and not y2) or (not x3 and not y3):
            return True
        n1 = (x1 ** 2 + y1 ** 2) ** 0.5
        n2 = (x2 ** 2 + y2 ** 2) ** 0.5
        n3 = (x3 ** 2 + y3 ** 2) ** 0.5
        if n1 < 1e-15 or n2 < 1e-15 or n3 < 1e-15:
            return True
        angle1 = math.acos(max(-1.0, min(1.0, round((x1 * x2 + y1 * y2) / (n1 * n2), 14))))
        angle2 = math.acos(max(-1.0, min(1.0, round((x2 * x3 + y2 * y3) / (n2 * n3), 14))))
        angle3 = math.acos(max(-1.0, min(1.0, round((x1 * x3 + y1 * y3) / (n1 * n3), 14))))
        return round(abs(angle1 + angle2 + angle3), 7) == round(2 * math.pi, 7)

    def return_value(self, point, q_vec):
        l_vals = self.l_values_at(point)
        value = 0.0
        for i in range(10):
            value += q_vec[self.local_to_global(i)] * self.ret_ermit_value(i, l_vals)
        return value

    def return_derivative_x(self, point, q_vec):
        l_vals = self.l_values_at(point)
        value = 0.0
        for i in range(10):
            value += q_vec[self.local_to_global(i)] * self.ret_ermit_derivative(i, l_vals, "x")
        return value

    def return_derivative_y(self, point, q_vec):
        l_vals = self.l_values_at(point)
        value = 0.0
        for i in range(10):
            value += q_vec[self.local_to_global(i)] * self.ret_ermit_derivative(i, l_vals, "y")
        return value


# ---------------------------------------------------------------------------
# Сборка портрета / элементов / решение
# ---------------------------------------------------------------------------

def generate_portrait(nodes_global, elements_data):
    n_dof = len(nodes_global) * 3 + len(elements_data)
    b_global = [0.0] * n_dof
    di = [0.0] * n_dof
    ig = [0] * (n_dof + 1)
    jg = []
    elemn = 0
    for elemd in elements_data:
        elem = [
            elemd[0] * 3,
            elemd[1] * 3,
            elemd[2] * 3,
            elemd[0] * 3 + 1,
            elemd[1] * 3 + 1,
            elemd[2] * 3 + 1,
            elemd[0] * 3 + 2,
            elemd[1] * 3 + 2,
            elemd[2] * 3 + 2,
            len(nodes_global) * 3 + elemn,
            elemd[3],
        ]
        elemn += 1
        for i in range(len(elem) - 2):
            for j in range(1 + i, len(elem) - 1):
                pair = [elem[i], elem[j]]
                if pair[0] < pair[1]:
                    pair[0], pair[1] = pair[1], pair[0]
                start = ig[pair[0]]
                end = ig[pair[0] + 1]
                break_flag = False
                for num in range(start, end):
                    if jg[num] == pair[1]:
                        break_flag = True
                        break
                    if jg[num] > pair[1]:
                        jg = jg[:num] + [pair[1]] + jg[num:]
                        for k in range(pair[0] + 1, len(ig)):
                            ig[k] += 1
                        break_flag = True
                        break
                if not break_flag:
                    jg = jg[:end] + [pair[1]] + jg[end:]
                    for k in range(pair[0] + 1, len(ig)):
                        ig[k] += 1

    ggl = [0.0] * ig[-1]
    ggu = [0.0] * ig[-1]
    return [ig, jg, di, ggl, ggu, b_global]


def form_elements(areas_data, elements_data, nodes_global):
    elements = []
    i = 1
    for el_dt in elements_data:
        el = Element(el_dt[:3], i, len(nodes_global) * 3 + i)
        if el.check_triangle(nodes_global):
            print(f"Элемент {i} вырожден")
            return []
        i += 1
        elements.append(el)
    return elements


def get_m_g_matrix(elements_data, G_global, poi_d, weu, wef, alpha, beta):
    for el in elements_data:
        el.add_to_A(G_global, poi_d, weu, wef, alpha=alpha, beta=beta)


def get_b_vector(elements, b_global, poi_vals, weif):
    for el in elements:
        el.add_to_b(b_global, poi_vals, weif)


def solve_slae(A_global, b_global, los_data, dmsrf):
    x = [0.0] * len(b_global)
    A_global.msg(b_global, x, los_data["max_iterations"], los_data["max_mismatch"], dmsrf)
    return x


class Solution:
    def __init__(self, elems, qs):
        self.elements = elems
        self.q_vec = qs

    def get_value(self, point):
        for el in self.elements:
            if el.is_in(point):
                return [
                    el.nodes_coords,
                    el.return_value(point, self.q_vec),
                    el.return_derivative_x(point, self.q_vec),
                    el.return_derivative_y(point, self.q_vec),
                ]
        return None


def load_mesh(msh):
    gmsh.initialize()
    gmsh.open(msh)

    nodes = gmsh.model.mesh.getNodes(-1, -1)
    new_nodes = []
    for i in range(len(nodes[0])):
        new_nodes.append([nodes[1][i * 3], nodes[1][i * 3 + 1]])

    phys_groups = gmsh.model.getPhysicalGroups(2)
    new_elements = []
    for group in phys_groups:
        surfs = gmsh.model.getEntitiesForPhysicalGroup(2, group[1])
        for sf in surfs:
            triangles = gmsh.model.mesh.getElements(2, sf)[1][0]
            for i in triangles:
                elem = gmsh.model.mesh.getElement(i)
                new_elem = [
                    int(elem[1][0]) - 1,
                    int(elem[1][1]) - 1,
                    int(elem[1][2]) - 1,
                    int(group[1]) - 1,
                ]
                new_elements.append(new_elem)

    gmsh.finalize()
    return new_nodes, new_elements


def solve_system(
    msh,
    poi=None,
    dmsmsrfr=False,
    trvls=None,
    alpha=1.0,
    beta=0.0,
    poi_values_file=None,
):
    if poi is None:
        poi = []
    if trvls is None:
        trvls = []

    nodes_glb, elements_data = load_mesh(msh)

    with open("los_data.json", "r", encoding="utf-8") as los_file:
        los_data = json.load(los_file)

    poi_path = poi_values_file or (msh + "_poi_values.json")
    with open(poi_path, "r", encoding="utf-8") as pois:
        pois_data = json.load(pois)

    weight_factor = [1.0] * len(pois_data["poi"])
    weight_use = [False] * len(weight_factor)
    matrix_data = generate_portrait(nodes_glb, elements_data)

    print("Инициализация матрицы и вектора...")
    a_glb = Matrix(matrix_data[0], matrix_data[1], matrix_data[3], matrix_data[4], matrix_data[2])
    b_glb = copy.copy(matrix_data[-1])
    print(f"Инициализация завершена\nФормирование СЛАУ (alpha={alpha}, beta={beta})...")

    # areas_data в сплайне не используется; передаём заглушку
    elements = form_elements([{}], elements_data, nodes_glb)
    q_new = None
    interest_values = []
    interest_derivs_x = []
    interest_derivs_y = []

    if elements:
        get_m_g_matrix(elements, a_glb, pois_data, weight_use, weight_factor, alpha, beta)
        get_b_vector(elements, b_glb, pois_data["vals"], weight_factor)
        print("СЛАУ сформировано\nРешение СЛАУ...")
        q_new = solve_slae(a_glb, b_glb, los_data, dmsmsrfr)
        print("СЛАУ решено")
        solution = Solution(elements, q_new)
        result = ""
        for cnt, p in enumerate(poi):
            value = solution.get_value(p)
            if value is not None:
                interest_values.append(value[1])
                interest_derivs_x.append(value[2])
                interest_derivs_y.append(value[3])
                coords = [[float(crd[0]), float(crd[1])] for crd in value[0]]
                true_v = trvls[cnt] if cnt < len(trvls) else 0.0
                if true_v:
                    mism = abs(value[1] - true_v) * 100 / abs(true_v)
                else:
                    mism = 0.0
                print(
                    f"Точка {p}:\nКоординаты точек элемента: {coords}\n"
                    f"Значение: {value[1]}\nПроцент ошибки: {mism}"
                )
                result += (
                    f"{cnt + 1}\t{p[0]}\t{p[1]}\t{value[1]:e}\t"
                    f"{true_v:e}\t{(value[1] - true_v):e}\t{mism}\n"
                )
            else:
                interest_values.append(None)
                interest_derivs_x.append(None)
                interest_derivs_y.append(None)
                print(f"Не удалось определить значение в точке {p}")

        with open(f"{msh}_splain_results.txt", "w", encoding="utf-8") as res_file:
            res_file.write(result)

    return q_new, interest_values, interest_derivs_x, interest_derivs_y, nodes_glb


def nodal_values_from_q(q_vec, n_nodes):
    """Значения сплайна в вершинах сетки (DOF значения)."""
    return [q_vec[i * 3] for i in range(n_nodes)]


def main(pause=True):
    try:
        with open("parameters.json", "r", encoding="utf-8") as infile:
            data = json.load(infile)
        mesh_name = data["mesh_file"]
        points_of_interest = data["points_of_interest"]
        alpha = float(data.get("alpha", 1.0))
        beta = float(data.get("beta", 0.0))

        q_vec, v_poi, poi_der_x, poi_der_y, nodes = solve_system(
            mesh_name,
            points_of_interest,
            data.get("do_mismatch_refresh", True),
            data.get("true_values", []),
            alpha=alpha,
            beta=beta,
            poi_values_file=data.get("poi_values_file", mesh_name + "_poi_values.json"),
        )

        if q_vec is not None:
            with open(mesh_name + "_splain_values.json", "w", encoding="utf-8") as q_out:
                json.dump(q_vec, q_out)
            with open(mesh_name + "_splain_poi_values.json", "w", encoding="utf-8") as v_out:
                json.dump(
                    {
                        "poi": points_of_interest,
                        "vals": v_poi,
                        "ders_x": poi_der_x,
                        "ders_y": poi_der_y,
                        "alpha": alpha,
                        "beta": beta,
                    },
                    v_out,
                )
            with open(mesh_name + "_splain_nodal_values.json", "w", encoding="utf-8") as n_out:
                json.dump(nodal_values_from_q(q_vec, len(nodes)), n_out)
            print(
                f"Готово. alpha={alpha}, beta={beta}.\n"
                f"Полный q: {mesh_name}_splain_values.json\n"
                f"Узловые значения: {mesh_name}_splain_nodal_values.json\n"
                f"Контрольные точки: {mesh_name}_splain_poi_values.json"
            )
    except Exception as e:
        print(e)
        if not pause:
            raise
    if pause:
        input("Нажмите Enter для закрытия...")


if __name__ == "__main__":
    main()
