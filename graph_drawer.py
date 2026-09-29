import json

import matplotlib.pyplot as plt

from splain_maker import form_elements, load_mesh
from test_functions import du_dx_func, du_dy_func, u_func


def linear_value(element, point, q_vec):
    l_vals = element.l_values_at(point)
    return sum(l_vals[i] * q_vec[element.nodes[i]] for i in range(3))


def linear_derivative(element, q_vec, axis):
    """axis: 1 — ∂/∂x, 2 — ∂/∂y (коэффициенты L-функций постоянны на элементе)."""
    return sum(element.functions[i][axis] * q_vec[element.nodes[i]] for i in range(3))


class Solution:
    def __init__(self, elements, fem_q, spline_q):
        self.elements = elements
        self.fem_q = fem_q
        self.spline_q = spline_q

    def find_element(self, point):
        for el in self.elements:
            if el.is_in(point):
                return el
        return None

    def get_value(self, point):
        el = self.find_element(point)
        if el is None:
            return None
        return [
            linear_value(el, point, self.fem_q),
            linear_derivative(el, self.fem_q, 1),
            linear_derivative(el, self.fem_q, 2),
            el.return_value(point, self.spline_q),
            el.return_derivative_x(point, self.spline_q),
            el.return_derivative_y(point, self.spline_q),
        ]


def sample_line(solution, func_num, start, stop, n_ints):
    t_mass, true_v, rows = [], [], []
    for t in range(n_ints + 1):
        point = [
            start[0] + t * (stop[0] - start[0]) / n_ints,
            start[1] + t * (stop[1] - start[1]) / n_ints,
        ]
        values = solution.get_value(point)
        if values is None:
            continue
        t_mass.append(t)
        true_v.append([
            u_func(func_num, *point),
            du_dx_func(func_num, *point),
            du_dy_func(func_num, *point),
        ])
        rows.append(values)
    return t_mass, true_v, rows


def plot(t_mass, true_v, rows):
    fig, axes = plt.subplots(1, 3)
    fig.suptitle("Изменение величин на прямой t")
    titles = ["Значение", "Производная по x", "Производная по y"]
    for k, ax in enumerate(axes):
        ax.plot(t_mass, [v[k] for v in true_v])
        ax.plot(t_mass, [r[k] for r in rows])
        ax.plot(t_mass, [r[k + 3] for r in rows])
        ax.grid(True, alpha=0.3)
        ax.set_title(titles[k])
    plt.legend(["Функция U", "МКЭ решение", "Сплайн"], loc="upper right")
    plt.show()


if __name__ == "__main__":
    with open("graph_parameters.json", "r", encoding="utf-8") as infile:
        data = json.load(infile)
    mesh_name = data["mesh_file"]
    nodes, elems = load_mesh(mesh_name)
    with open(data.get("solution_values_file", mesh_name + "_values.json"), "r") as in_sol:
        solution_q = json.load(in_sol)
    with open(data.get("splain_values_file", mesh_name + "_splain_values.json"), "r") as in_spl:
        spline_q = json.load(in_spl)

    solution = Solution(form_elements([{}], elems, nodes), solution_q, spline_q)
    plot(*sample_line(solution, data["func_num"], data["start"], data["stop"], data["n_ints"]))
