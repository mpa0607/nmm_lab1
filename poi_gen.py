"""Сетка точек интереса и точные значения U → parameters.json.

Запуск: python poi_gen.py [mesh0.msh | mesh1.msh | mesh2.msh]
Для сеток вне DIVISIONS точки берутся из parameters.json как есть.
Номер функции U берётся из materials.json (f_fun), чтобы true_values
совпадали с функцией, для которой считается МКЭ.
"""
import json
import sys

from test_functions import u_func

DIVISIONS = {"two_triangles.msh": 3, "mesh0.msh": 6, "mesh1.msh": 12, "mesh2.msh": 24}


def grid_points(n):
    steps = [round(-1 + i / n, 10) for i in range(1, 2 * n)]
    return [[x, y] for x in steps for y in steps]


def generate(mesh=None):
    with open("parameters.json", "r", encoding="utf-8") as f:
        params = json.load(f)
    mesh = mesh or params["mesh_file"]
    with open("materials.json", "r", encoding="utf-8") as f:
        func_num = json.load(f)[0]["f_fun"]

    pois = grid_points(DIVISIONS[mesh]) if mesh in DIVISIONS else params["points_of_interest"]
    params.update({
        "mesh_file": mesh,
        "poi_values_file": f"{mesh}_poi_values.json",
        "points_of_interest": pois,
        "true_values": [u_func(func_num, x, y) for x, y in pois],
    })
    with open("parameters.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)
    print(f"{mesh}: {len(pois)} точек, U №{func_num}")


if __name__ == "__main__":
    generate(sys.argv[1] if len(sys.argv) > 1 else None)
