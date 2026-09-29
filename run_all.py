"""Полная цепочка: точки интереса → линейный МКЭ → сплайн Эрмита.

Запуск: python run_all.py mesh0.msh [mesh1.msh mesh2.msh ...]
Без аргументов — сетка из parameters.json.
"""
import sys

import magnetic_main
import poi_gen
import splain_maker


def run(mesh=None):
    poi_gen.generate(mesh)
    magnetic_main.main(pause=False)
    splain_maker.main(pause=False)


if __name__ == "__main__":
    for mesh_name in sys.argv[1:] or [None]:
        run(mesh_name)
