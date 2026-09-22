import math
import json
import copy
import gmsh

def lam_func(f, x=0, y=0):
    if f == 0:
        return 1
    else:
        return 0

def gamm_func(f, x=0, y=0):
    if f == 0:
        return 1
    else:
        return 0

def f_func(f, x=0, y=0):
    if f == 0:
        return x + y
    elif f == 1:
        return 4 + x ** 2 + y ** 2
    elif f == 2:
        return 6 * x + 6 * y + x ** 3 + y ** 3
    elif f == 3:
        return 12 * x ** 2 + 12 * y ** 2 + x ** 4 + y ** 4
    elif f == 4:
        return -math.sin(x) - math.sin(y) + math.sin(x) + math.sin(y)
    else:
        return 0

def u_func(f, x=0, y=0):
    if f == 0:
        return x + y
    elif f == 1:
        return x ** 2 + y ** 2
    elif f == 2:
        return x ** 3 + y ** 3
    elif f == 3:
        return x ** 4 + y ** 4
    elif f == 4:
        return math.sin(x) + math.sin(y)
    else:
        return 0

class Matrix:
    def __init__(self, ig, jg, ggl, ggu, di):
        self.ig = copy.copy(ig)
        self.jg = copy.copy(jg)
        self.ggl = copy.copy(ggl)
        self.ggu = copy.copy(ggu)
        self.di = copy.copy(di)

    def get_elem(self, i, j):
        if i == j:
            return self.di[i]
        elif i > j:
            start = self.ig[i]
            end = self.ig[i + 1]
            for e in range(start, end):
                if self.jg[e] == j:
                    return self.ggl[e]
        else:
            start = self.ig[j]
            end = self.ig[j + 1]
            for e in range(start, end):
                if self.jg[e] == i:
                    return self.ggu[e]
        return 0

    def add_to_elem(self, i, j, n):
        if n == 0:
            return 0
        if i == j:
            self.di[i] += n
            return 0
        elif i > j:
            start = self.ig[i]
            end = self.ig[i + 1]
            for e in range(start, end):
                if self.jg[e] == j:
                    self.ggl[e] += n
                    return 0
        else:
            start = self.ig[j]
            end = self.ig[j + 1]
            for e in range(start, end):
                if self.jg[e] == i:
                    self.ggu[e] += n
                    return 0
        return 1

    def matrix_mult_vextor(self, x, y, n):
        for i in range(n):
            y[i] = x[i] * self.di[i]
        for i in range(n):
            for j in range(self.ig[i + 1] - self.ig[i]):
                y[i] += self.ggl[self.ig[i] + j] * x[self.jg[self.ig[i] + j]]
                y[self.jg[self.ig[i] + j]] += self.ggu[self.ig[i] + j] * x[i]
        return 0

    def scalar_multiply(self, x, y, n):
        sum = 0
        for i in range(n):
            sum += x[i] * y[i]
        return sum

    def msg(self, pr, x, max_k, mismax, dmsrf):
        n = len(pr)
        r = [0 for i in range(n)]
        z = [0 for i in range(n)]
        az = [0 for i in range(n)]
        ar = [0 for i in range(n)]
        norm_pr = self.scalar_multiply(pr, pr, n)
        self.matrix_mult_vextor(x, ar, n)
        for i in range(n):
            r[i] = pr[i] - ar[i]
            z[i] = r[i]
        r_norm = self.scalar_multiply(r, r, n)
        mism = math.sqrt(r_norm / norm_pr)
        k1 = 0
        for k in range(1, max_k + 1):
            print(f"Начало итерации {k}...")
            self.matrix_mult_vextor(z, az, n)
            a = self.scalar_multiply(r, r, n) / self.scalar_multiply(az, z, n)
            for i in range(n):
                x[i] += a * z[i]
                r[i] -= a * az[i]
            r_norm_new = self.scalar_multiply(r, r, n)
            b = -(r_norm_new / r_norm)
            r_norm = r_norm_new
            for i in range(n):
                z[i] = r[i] + b * z[i]
            mism = math.sqrt(r_norm / norm_pr)
            k1 += 1
            if k1 % 10 == 0 and dmsrf:
                vec = [0 for i in range(n)]
                self.matrix_mult_vextor(x, vec, n)
                for vc in range(len(vec)):
                    vec[vc] = pr[vc] - vec[vc]
                mism = math.sqrt(self.scalar_multiply(vec, vec, n) / norm_pr)
            print(f"Итерация {k} завершена\nНевязка: {mism}")
            if mism <= mismax:
                break
        print(f"Число итераций: {k1}; Невязка: {mism}")

class Element:
    def __init__(self, nodes, lam, f_fun, gamm, number):
        self.nodes = nodes
        self.functions = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.lam = lam
        self.f_fun = f_fun
        self.gamm = gamm
        self.number = number
        self.det_t = 0
        self.nodes_coords = []

    def add_to_G_and_M(self, G_global):
        nodes = self.nodes_coords
        self.det_d = abs((nodes[1][0] - nodes[0][0]) * (nodes[2][1] - nodes[0][1]) - (nodes[1][1] - nodes[0][1]) * (
                nodes[2][0] - nodes[0][0]))
        self.functions = [
            [nodes[1][0] * nodes[2][1] - nodes[2][0] * nodes[1][1], nodes[1][1] - nodes[2][1],
             nodes[2][0] - nodes[1][0]],
            [nodes[2][0] * nodes[0][1] - nodes[0][0] * nodes[2][1], nodes[2][1] - nodes[0][1],
             nodes[0][0] - nodes[2][0]],
            [nodes[0][0] * nodes[1][1] - nodes[1][0] * nodes[0][1], nodes[0][1] - nodes[1][1],
             nodes[1][0] - nodes[0][0]]
        ]
        for i in range(3):
            for j in range(3):
                self.functions[i][j] /= self.det_d

        G = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        df_cf = lam_func(self.lam)
        for i in range(3):
            for j in range(3):
                k = self.functions[i][1] * self.functions[j][1] + self.functions[i][2] * self.functions[j][2]
                G[i][j] = k * df_cf * self.det_d / 2.0

        for i in range(3):
            for j in range(3):
                G_global.add_to_elem(self.nodes[i], self.nodes[j], G[i][j])

        M = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        gamm_cf = gamm_func(self.gamm)
        for i in range(3):
            for j in range(3):
                M[i][j] = (gamm_cf * self.det_d * (1.0 + float(i == j)) / 24.0)

        for i in range(3):
            for j in range(3):
                G_global.add_to_elem(self.nodes[i], self.nodes[j], M[i][j])

    def add_to_b(self, b_global):
        b = [0, 0, 0]
        for i in range(3):
            for j in range(3):
                b[i] += (f_func(self.f_fun, self.nodes_coords[j][0], self.nodes_coords[j][1]) * self.det_d * (1.0 + float(i == j)) / 24.0)
        for i in range(3):
            b_global[self.nodes[i]] += b[i]

    def is_in(self, point):
        x1 = self.nodes_coords[0][0] - point[0]
        y1 = self.nodes_coords[0][1] - point[1]
        x2 = self.nodes_coords[1][0] - point[0]
        y2 = self.nodes_coords[1][1] - point[1]
        x3 = self.nodes_coords[2][0] - point[0]
        y3 = self.nodes_coords[2][1] - point[1]
        if not x1 and not y1 or not x2 and not y2 or not x3 and not y3:
            return True
        angle1 = math.acos(
            round((x1 * x2 + y1 * y2) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x2 ** 2 + y2 ** 2) ** 0.5), 14))
        angle2 = math.acos(
            round((x2 * x3 + y2 * y3) / ((x2 ** 2 + y2 ** 2) ** 0.5 * (x3 ** 2 + y3 ** 2) ** 0.5), 14))
        angle3 = math.acos(
            round((x1 * x3 + y1 * y3) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x3 ** 2 + y3 ** 2) ** 0.5), 14))

        return round(abs(sum([angle1, angle2, angle3])), 7) == round(2 * math.pi, 7)

    def return_value(self, point, q_vec):
        value = 0
        for i in range(3):
            value += q_vec[self.nodes[i]] * (
                        self.functions[i][0] + self.functions[i][1] * point[0] + self.functions[i][2] * point[1])
        return value

    def return_derivative_x(self, q_vec):
        value = 0
        for i in range(3):
            value += q_vec[self.nodes[i]] * self.functions[i][1]
        return value

    def return_derivative_y(self, q_vec):
        value = 0
        for i in range(3):
            value += q_vec[self.nodes[i]] * self.functions[i][2]
        return value

    def check_triangle(self, nodes_global):
        self.det_t = 0
        self.nodes_coords = []
        for n in self.nodes:
            self.nodes_coords.append(nodes_global[n])
        nodes = self.nodes_coords
        self.det_d = abs((nodes[1][0] - nodes[0][0]) * (nodes[2][1] - nodes[0][1]) - (nodes[1][1] - nodes[0][1]) * (
                nodes[2][0] - nodes[0][0]))
        if self.det_d < 1e-15:
            return 1
        return 0

class Edge_Condition:
    def __init__(self, parametres, lines):
        self.parametres = parametres
        self.lines = lines

    def analise(self, A_global, b_global, nodes_global):
        nodes = self.lines[self.parametres["line"] - 1]
        for n in range(len(nodes)):
            u_num = u_func(self.parametres["u_fun"], nodes_global[nodes[n]][0], nodes_global[nodes[n]][1])
            for j in range(len(nodes_global)):
                A_global.add_to_elem(nodes[n], j, -A_global.get_elem(nodes[n], j) + int(nodes[n] == j))
                if nodes[n] != j:
                    b_global[j] -= u_num * A_global.get_elem(j, nodes[n])
                    A_global.add_to_elem(j, nodes[n], -A_global.get_elem(j, nodes[n]))
            b_global[nodes[n]] = u_num

def generate_portrait(nodes_global, elements_data):
    b_global = [0 for b in range(len(nodes_global))]
    di = [0 for d in range(len(nodes_global))]
    ig = [0 for ige in range(len(nodes_global) + 1)]
    jg = []
    for elem in elements_data:
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
                        jg_end = jg[num:]
                        jg = jg[:num]
                        jg.append(pair[1])
                        jg.extend(jg_end)
                        for k in range(pair[0] + 1, len(ig)):
                            ig[k] += 1
                        break_flag = True
                        break
                if not break_flag:
                    jg_end = jg[end:]
                    jg = jg[:end]
                    jg.append(pair[1])
                    jg.extend(jg_end)
                    for k in range(pair[0] + 1, len(ig)):
                        ig[k] += 1

    ggl = [0 for gl in range(ig[-1])]
    ggu = [0 for gl in range(ig[-1])]
    return [ig, jg, di, ggl, ggu, b_global]

def form_elements(areas_data, elements_data, nodes_global):
    elements = []
    i = 1
    for el_dt in elements_data:
        area = areas_data[el_dt[3]]
        el = Element(el_dt[:3], area["lam"], area["f_fun"], area["gamm"], i)
        if el.check_triangle(nodes_global):
            print(f"Элемент {i} вырожден")
            return []
        i += 1
        elements.append(el)
    return elements

def get_m_g_matrix(elements_data, G_global):
    for el in elements_data:
        el.add_to_G_and_M(G_global)

def get_b_vector(elements, b_global):
    for el in elements:
        el.add_to_b(b_global)


def solve_edge_conditions(edge_conditions, A_global, b_global, nodes_global, borders):
    for c in edge_conditions:
        edge_cond = Edge_Condition(c, borders)
        edge_cond.analise(A_global, b_global, nodes_global)


def solve_slae(A_global, b_global, los_data, nodes_global, dmsrf):
    x = [0 for i in range(len(nodes_global))]
    A_global.msg(b_global, x, los_data["max_iterations"], los_data["max_mismatch"], dmsrf)
    return x

class Solution:
    def __init__(self, elems, qs):
        self.elements = elems
        self.q_vec = qs

    def get_value(self, point):
        for el in self.elements:
            if el.is_in(point):
                pt = el.nodes_coords
                return [pt, el.return_value(point, self.q_vec), el.return_derivative_x(self.q_vec), el.return_derivative_y(self.q_vec)]


def solve_system(msh, poi=[], dmsmsrfr=False, trvls=[]):
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
                new_elem = [int(elem[1][0]) - 1, int(elem[1][1]) - 1, int(elem[1][2]) - 1, int(group[1]) - 1]
                new_elements.append(new_elem)

    new_borders = {}
    borders = gmsh.model.getEntitiesForPhysicalGroup(1, 1)
    for brd in borders:
        lines = gmsh.model.mesh.getElements(1, brd)[1][0]
        for i in lines:
            line = gmsh.model.mesh.getElement(i)
            new_line = [int(line[1][0]) - 1, int(line[1][1]) - 1]
            if line[3] in new_borders.keys():
                if new_line[0] not in new_borders[line[3]]:
                    new_borders[line[3]].append(new_line[0])
                if new_line[1] not in new_borders[line[3]]:
                    new_borders[line[3]].append(new_line[1])
            else:
                new_borders[line[3]] = new_line


    gmsh.finalize()

    nodes_glb = new_nodes
    elements_data = new_elements
    borders_data = []
    for kk in new_borders.keys():
        borders_data.append(new_borders[kk])
    with open("materials.json", "r") as areas_file:
        areas_data = json.load(areas_file)
    with open("mag_edge_conditions.json", "r") as edge_cond_file:
        edge_conditions = json.load(edge_cond_file)
    with open("los_data.json", "r") as los_file:
        los_data = json.load(los_file)
    matrix_data = generate_portrait(nodes_glb, elements_data)

    print("Инициализация матрицы и вектора...")
    a_glb = Matrix(matrix_data[0], matrix_data[1], matrix_data[3], matrix_data[4], matrix_data[2])
    b_glb = copy.copy(matrix_data[-1])
    print("Инициализация завершена\nФормирование СЛАУ...")
    elements = form_elements(areas_data, elements_data, nodes_glb)
    if len(elements):
        get_m_g_matrix(elements, a_glb)
        get_b_vector(elements, b_glb)
        solve_edge_conditions(edge_conditions, a_glb, b_glb, nodes_glb, borders_data)
        print("СЛАУ сформировано\nРешение СЛАУ...")
        q_new = solve_slae(a_glb, b_glb, los_data, nodes_glb, dmsmsrfr)
        print(f"СЛАУ решено")
        solution = Solution(elements, q_new)
        cnt = 0
        result = ""
        interest_values = []
        interest_derivs_x = []
        interest_derivs_y = []
        for p in poi:
            value = solution.get_value(p)
            coords = []
            if value is not None:
                interest_values.append(value[1])
                interest_derivs_x.append(value[2])
                interest_derivs_y.append(value[3])
                for crd in value[0]:
                    coords.append([float(crd[0]), float(crd[1])])
                if trvls[cnt]:
                    mism = abs(value[1] - trvls[cnt]) * 100 / abs(trvls[cnt])
                else:
                    mism = 0
                print(
                    f"Точка {p}:\nКоординаты точек элемента: {coords}\nЗначение: {value[1]}\nПроцент ошибки: {mism}")
                result += f"{cnt+1}\t{p[0]}\t{p[1]}\t{value[1]:e}\t{trvls[cnt]:e}\t{(value[1] - trvls[cnt]):e}\t{mism}\n"
            else:
                interest_values.append(None)
                interest_derivs_x.append(None)
                interest_derivs_y.append(None)
                print(f"Не удалось определить значение в точке {p}")
            cnt += 1
        with open(f"{msh}_results.txt", "w") as res_file:
            res_file.write(result)
    input("Нажмите любую клавишу для закрытия программы...")
    return q_new, interest_values, interest_derivs_x, interest_derivs_y

with open("parameters.json", "r") as infile:
    try:
        data = json.load(infile)
        mesh_name = data["mesh_file"]
        points_of_interest = data["points_of_interest"]
        true_values=data["true_values"]
        do_mismatch_refresh = data["do_mismatch_refresh"]
        q_vec, v_poi, poi_der_x, poi_der_y = solve_system(mesh_name, points_of_interest, do_mismatch_refresh, true_values)
        with open(mesh_name + "_values.json", "w") as q_out:
            json.dump(q_vec, q_out)
        with open(mesh_name + "_poi_values.json", "w") as v_out:
            dt = {"poi": points_of_interest, "vals": v_poi, "ders_x": poi_der_x, "ders_y": poi_der_y}
            json.dump(dt, v_out)
    except Exception as e:
        print(e)
        input("Press enter to close...")