try:
    import json
    import gmsh
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.tri import Triangulation
    from matplotlib import ticker
    from matplotlib.colors import Normalize


    def is_cw(element, pointsx, pointsy):
        sm = 0

        point1 = [pointsx[element[0]], pointsy[element[0]]]
        point2 = [pointsx[element[1]], pointsy[element[1]]]
        point3 = [pointsx[element[2]], pointsy[element[2]]]

        xa = point1[0] - point2[0]
        ya = point1[1] - point2[1]
        xb = point2[0] - point3[0]
        yb = point2[1] - point3[1]
        sm -= xa * yb - xb * ya

        xa = point2[0] - point3[0]
        ya = point2[1] - point3[1]
        xb = point3[0] - point1[0]
        yb = point3[1] - point1[1]
        sm -= xa * yb - xb * ya

        xa = point3[0] - point1[0]
        ya = point3[1] - point1[1]
        xb = point1[0] - point2[0]
        yb = point1[1] - point2[1]
        sm -= xa * yb - xb * ya

        return sm


    def draw_everything(parameters):
        # values_file: узловые значения (линейный МКЭ или splain_nodal).
        # Если не указан — старый формат <mesh>_values.json.
        values_path = parameters.get(
            "values_file", f"{parameters['mesh_file']}_values.json"
        )
        with open(values_path, encoding="utf-8") as q_file:
            q_vec = json.load(q_file)

        gmsh.initialize()

        gmsh.open(parameters["mesh_file"])

        nodes = gmsh.model.mesh.getNodes(-1, -1)
        nodes_x = []
        nodes_y = []
        for i in range(len(nodes[0])):
            nodes_x.append(nodes[1][i * 3])
            nodes_y.append(nodes[1][i * 3 + 1])

        phys_groups = gmsh.model.getPhysicalGroups(2)
        total_elements = []
        for group in phys_groups:
            surfs = gmsh.model.getEntitiesForPhysicalGroup(2, group[1])
            for sf in surfs:
                triangles = gmsh.model.mesh.getElements(2, sf)[1][0]
                for i in triangles:
                    elem = gmsh.model.mesh.getElement(i)
                    new_elem = [int(elem[1][0]) - 1, int(elem[1][1]) - 1, int(elem[1][2]) - 1]
                    if not is_cw(new_elem, nodes_x, nodes_y) < 0:
                        new_elem.reverse()
                    total_elements.append(new_elem)

        new_borders = {}
        borders = gmsh.model.getEntitiesForPhysicalGroup(1, 2)
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
        all_borders = []
        for kk in new_borders.keys():
            border_data = [[], []]
            for pt in new_borders[kk]:
                border_data[0].append(nodes_x[pt])
                border_data[1].append(nodes_y[pt])
            all_borders.append(border_data)

        gmsh.finalize()

        qmin = np.min(q_vec)
        qmax = np.max(q_vec)
        norm = Normalize(vmin=qmin, vmax=qmax)
        fig, ax = plt.subplots(figsize=(10, 8))
        if parameters["gouraud_shading"]:
            shading = "gouraud"
        else:
            shading = "flat"

        triang = Triangulation(nodes_x, nodes_y, total_elements)
        if parameters["draw_grad"]:
            tpc = ax.tripcolor(triang, q_vec, shading=shading, cmap=parameters["cmap"], norm=norm,
                               alpha=parameters["grad_alpha"])
        if parameters["draw_izo"]:
            tc = ax.tricontour(triang, q_vec, levels=parameters["levels"], colors=parameters["izo_color"],
                               linewidths=parameters["izo_width"], alpha=parameters["izo_alpha"])
        if parameters["draw_cont"]:
            for ln in all_borders:
                ax.plot(ln[0], ln[1], color=parameters["cont_color"], alpha=parameters["cont_alpha"])
        ticks = np.linspace(qmin, qmax, num=10)
        if parameters["draw_izo"] and parameters["show_izo_values"]:
            ax.clabel(tc, fontsize=8, fmt="%.5e", inline=False)
        if parameters["draw_grad"]:
            cb = fig.colorbar(tpc, ax=ax, ticks=ticks)
            cb.set_label("Значения")
            cb.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%e'))
        ax.set_aspect("equal")
        ax.set_xlabel("Ось X")
        ax.set_ylabel("Ось Y")
        ax.set_title("Распределение значений (сплайн / поле)")
        ax.grid(True, alpha=0.3)
        plt.show()


    with open("field_parametres.json", "r") as par_file:
        parameters = json.load(par_file)
    draw_everything(parameters)
except Exception as e:
    print(e)
    input("Press enter to exit...")