try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import copy
    from tkinter.scrolledtext import ScrolledText
    from matplotlib import pyplot as plt
    import math
    import gmsh
    import sys
    import json
    from tkinter import *
    from tkinter import filedialog
    from tkinter.ttk import Combobox
    from tkinter import ttk
    from tkinter import messagebox

    class ToolTip(object):
        def __init__(self, widget, x_off, y_off, text, font, relief, background):
            self.widget = widget
            self.tipwindow = None
            self.id = None
            self.x = self.y = 0
            self.x_offset = x_off
            self.y_offset = y_off
            self.text = text
            self.font = font
            self.relief = relief
            self.background = background

        def showtip(self):
            if self.tipwindow or not self.text:
                return
            x, y, cx, cy = self.widget.bbox("insert")
            x = x + self.widget.winfo_rootx() + self.x_offset
            y = y + cy + self.widget.winfo_rooty() + self.y_offset
            self.tipwindow = tw = Toplevel(self.widget)
            tw.wm_overrideredirect(1)
            tw.wm_geometry("+%d+%d" % (x, y))
            label = Label(tw, text=self.text, justify=LEFT,
                          background=self.background, relief=self.relief, borderwidth=1,
                          font=self.font)
            label.pack(ipadx=1)

        def hidetip(self):
            tw = self.tipwindow
            self.tipwindow = None
            if tw:
                tw.destroy()

    def BindToolTip(widget, text, x_off, y_off, font, relief, background):
        toolTip = ToolTip(widget, x_off, y_off, text, font, relief, background)

        def enter(event):
            toolTip.showtip()

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    algos = ["MeshAdapt", "Delaunay", "Frontal-Delaunay", "BAMG", "Frontal-Delaunay-for-Quads",
             "Packing-of-parallelograms",
             "Initial-mesh-only"]
    algo_numbers = {"MeshAdapt": 1, "Delaunay": 5, "Frontal-Delaunay": 6, "BAMG": 7, "Frontal-Delaunay-for-Quads": 8,
                    "Packing-of-parallelograms": 9, "Initial-mesh-only": 3}
    main_font = "Consolas Bold"

    def choose_file():
        name = filedialog.askopenfilename(filetypes= \
                                              (("Файлы сеток", "*.msh"), ("Все файлы", "*.*")))
        filename.delete(0, END)
        filename.insert(0, name)
        update_short_info(name)

    def choose_file2():
        name = filedialog.askopenfilename(filetypes= \
                                              (("Файлы данных", "*.json"), ("Все файлы", "*.*")))
        filename2.delete(0, END)
        filename2.insert(0, name)

    def save_data():
        data = get_data()
        if data:
            name = filename2.get()
            if not name:
                messagebox.showwarning("Предупреждение", "Пустое имя файла")
                return 1
            if name[-5:] != ".json":
                name += ".json"
            with open(name, 'w') as out_file:
                json.dump(data, out_file)

            messagebox.showinfo("Итог", f"Данные успешно сохранены в файл:\n{name}")

    def write_data(data):

        ent1.delete(1.0, END)
        index = 1.0
        for i in data["nodes"]:
            ent1.insert(index, i)
            index += len(i)

        entlc.delete(1.0, END)
        entlc.insert(1.0, data["lcs"])

        ent2.delete(1.0, END)
        index = 1.0
        for i in data["lines"]:
            ent2.insert(index, i)
            index += len(i)

        ent3.delete(1.0, END)
        ent3.insert(1.0, data["border"])

        ent4.delete(1.0, END)
        index = 1.0
        for i in data["contoures"]:
            ent4.insert(index, i)
            index += len(i)

        ent5.delete(1.0, END)
        index = 1.0
        for i in data["areas"]:
            ent5.insert(index, i)
            index += len(i)

        entmat.delete(1.0, END)
        entmat.insert(1.0, data["materials"])

        ent6.delete(1.0, END)
        index = 1.0

        for i in data["embed_nodes"].keys():
            nodes = data["embed_nodes"][i]
            ent6.insert(index, nodes)
            index += len(nodes)

        return 0

    def load_data():
        name = filedialog.askopenfilename(filetypes=(("Файлы данных", "*.json"), ("Все файлы", "*.*")))
        data = {}
        if name:
            try:
                with open(name, 'r') as in_file:
                    got_data = json.load(in_file)
                data["nodes"] = got_data["nodes"]
                data["lines"] = got_data["lines"]
                data["border"] = got_data["border"]
                data["contoures"] = got_data["contoures"]
                data["areas"] = got_data["areas"]
                data["embed_nodes"] = got_data["embed_nodes"]
                data["lcs"] = got_data["lcs"]
                data["materials"] = got_data["materials"]
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при чтении файла:\n{name}")
                return 1
            try:
                for i in range(len(data["nodes"])):
                    data["nodes"][i] = str(data["nodes"][i][0]) + " " + str(data["nodes"][i][1]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании узлов из файла:\n{name}")
                return 1

            try:
                for j in range(len(data["lcs"])):
                    data["lcs"][j] = str(data["lcs"][j])
                data["lcs"] = '\n'.join(data["lcs"]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании значений Lc из файла:\n{name}")
                return 1

            try:
                for i in range(len(data["lines"])):
                    data["lines"][i] = str(data["lines"][i][0]) + " " + str(data["lines"][i][1]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании рёбер из файла:\n{name}")
                return 1

            try:
                for j in range(len(data["border"])):
                    data["border"][j] = str(data["border"][j])
                data["border"] = ' '.join(data["border"]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании внешних границ из файла:\n{name}")
                return 1

            try:
                for i in range(len(data["contoures"])):
                    for j in range(len(data["contoures"][i])):
                        data["contoures"][i][j] = str(data["contoures"][i][j])
                    data["contoures"][i] = ' '.join(data["contoures"][i]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании контуров из файла:\n{name}")
                return 1

            try:
                for i in range(len(data["areas"])):
                    for j in range(len(data["areas"][i])):
                        data["areas"][i][j] = str(data["areas"][i][j])
                    data["areas"][i] = ' '.join(data["areas"][i]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании областей из файла:\n{name}")
                return 1

            try:
                for j in range(len(data["materials"])):
                    data["materials"][j] = str(data["materials"][j])
                data["materials"] = '\n'.join(data["materials"]) + "\n"
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании номеров материалов из файла:\n{name}")
                return 1

            try:
                embeding = {}
                ind = 1
                for i in data["embed_nodes"]:
                    if len(i):
                        for j in range(len(i)):
                            i[j] = str(i[j])
                        embeding[str(ind)] = str(ind) + "\n" + ' '.join(i) + "\n"
                    ind += 1
                data["embed_nodes"] = embeding
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Ошибка при считывании включаемых узлов из файла:\n{name}")
                return 1

            return write_data(data)

    def get_data():
        data = {}

        coords = ent1.get(1.0, END).replace("\n", " ").split(" ")
        while '' in coords:
            coords.remove('')

        nodes = []

        if len(coords) % 2:
            messagebox.showerror("Ошибка", "Некорректное число значений координат узлов")
            return 0
        if len(coords) < 6:
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум три узла")
            return 0
        for i in range(0, len(coords) - 1, 2):
            try:
                nodes.append([float(coords[i]), float(coords[i + 1])])
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат координат узлов")
                return 0
        data["nodes"] = nodes



        lcs = entlc.get(1.0, END).replace("\n", " ").split(" ")
        while '' in lcs:
            lcs.remove('')

        if len(lcs) != len(nodes):
            messagebox.showerror("Предупреждение", "Необходимо задать значение Lc для каждого узла")
            return 0

        lcs_nums = []
        for i in range(len(lcs)):
            try:
                lcs_nums.append(float(lcs[i]))
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат значений параметров Lc")
                return 0
        data["lcs"] = lcs_nums

        lns = ent2.get(1.0, END).replace("\n", " ").split(" ")
        while '' in lns:
            lns.remove('')

        lines = []
        if len(lns) % 2:
            messagebox.showerror("Ошибка", "Некорректное число индексов точек в рёбрах")
            return 0
        if len(coords) < 6:
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум три ребра")
            return 0
        for i in range(0, len(lns) - 1, 2):
            try:
                lines.append([int(lns[i]), int(lns[i + 1])])
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат индексов точек в рёбрах")
                return 0
        data["lines"] = lines

        brdr = ent3.get(1.0, END).replace("\n", " ").split(" ")
        while '' in brdr:
            brdr.remove('')

        border = []
        for i in range(len(brdr)):
            try:
                border.append(int(brdr[i]))
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат индексов линий внешней границы")
                return 0
        data["border"] = border

        cntrs = ent4.get(1.0, END).split("\n")[:-1]
        while '' in cntrs:
            cntrs.remove('')
        if not len(cntrs):
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум один контур")
            return 0
        contoures = []
        for i in range(len(cntrs)):
            try:
                cntrs[i] = cntrs[i].split(' ')
                while '' in cntrs[i]:
                    cntrs.remove('')
                cntr = []
                for j in cntrs[i]:
                    cntr.append(int(j))
                contoures.append(cntr)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректное указание границ областей")
                return 0
        data["contoures"] = contoures

        ars = ent5.get(1.0, END).split("\n")[:-1]
        while '' in ars:
            ars.remove('')
        if not len(ars):
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум одну область")
            return 0
        areas = []
        for i in range(len(ars)):
            try:
                ars[i] = ars[i].split(' ')
                while '' in ars[i]:
                    ars.remove('')
                area = []
                for j in ars[i]:
                    area.append(int(j))
                areas.append(area)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректное указание областей")
                return 0
        data["areas"] = areas

        mats = entmat.get(1.0, END).replace("\n", " ").split(" ")
        while '' in mats:
            mats.remove('')

        if len(mats) != len(areas):
            messagebox.showerror("Предупреждение", "Необходимо задать номер материала для каждой области")
            return 0

        mat_nums = []
        for i in range(len(mats)):
            try:
                mat_nums.append(int(mats[i]))
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат номеров области")
                return 0
        data["materials"] = mat_nums

        emb = ent6.get(1.0, END).split("\n")
        while '' in emb:
            emb.remove('')
        if len(emb) % 2 and len(emb) > 0:
            messagebox.showerror("Ошибка", "Некорректное задание включений узлов")
            return 0

        embed = []
        for i in range(len(areas)):
            embed.append([])
        for i in range(len(emb)):
            if i % 2:
                emb[i] = emb[i].split(' ')
                while '' in emb[i]:
                    emb[i].remove('')
            else:
                try:
                    emb[i] = int(emb[i])
                except Exception as e:
                    print(e)
                    messagebox.showerror("Ошибка", "Некорректное указание индекса включения")
                    return 0

        for i in range(0, len(emb) - 1, 2):
            try:
                for j in range(len(emb[i + 1])):
                    insrt = int(emb[i + 1][j])
                    embed[emb[i] - 1].append(insrt)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", "Некорректный формат индексов велючаемых узлов")
                return 0
        data["embed_nodes"] = embed

        return data

    def generate_mesh():
        global accepted_materials
        gmsh.initialize()
        gmsh.option.setNumber("Mesh.Algorithm", algo_numbers[drp.get()])
        data = get_data()
        if data:
            name = filename.get()
            if not name:
                messagebox.showwarning("Предупреждение", "Пустое имя файла")
                gmsh.finalize()
                return 1
            if name[-4:] != ".msh":
                name += ".msh"

            gmsh.model.add("mesh")

            try:
                for i in range(len(data["nodes"])):
                    lc = data["lcs"][i]
                    node = data["nodes"][i]
                    gmsh.model.geo.addPoint(node[0], node[1], 0, lc, i + 1)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при задании точек")
                gmsh.finalize()
                return 1

            try:
                for i in range(len(data["lines"])):
                    line = data["lines"][i]
                    gmsh.model.geo.addLine(line[0], line[1], i + 1)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при задании линий")
                gmsh.finalize()
                return 1

            try:
                for i in range(len(data["contoures"])):
                    contour = data["contoures"][i]
                    gmsh.model.geo.addCurveLoop(contour, i + 1)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при задании границ областей")
                gmsh.finalize()
                return 1

            try:
                for i in range(len(data["areas"])):
                    area = data["areas"][i]
                    gmsh.model.geo.addPlaneSurface(area, i + 1)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при формировании областей")
                gmsh.finalize()
                return 1

            gmsh.model.geo.synchronize()
            try:
                for i in range(len(data["embed_nodes"])):
                    embed = data["embed_nodes"][i]
                    gmsh.model.mesh.embed(0, embed, 2, i + 1)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при включении дополнительных узлов")
                gmsh.finalize()
                return 1

            try:
                gmsh.model.addPhysicalGroup(0, [i + 1 for i in range(len(data["nodes"]))], name="Initial nodes", tag=1)
                gmsh.model.addPhysicalGroup(1, data["border"], name="Outer border", tag=1)
                mat_groups = {}
                if not accepted_materials:
                    nm = 1
                    while nm in data["materials"]:
                        nm += 1
                    if nm < max(data["materials"]):
                        text = f"Материал №{nm} не используется при построении сетки, хотя материалы с большими"
                        if nm > 1:
                            text += " и меньшими "
                        text += "номерами используются.\nЭто может привести к путанице при определении параметров материалов областей.\nВсё равно сохранить данные в файл?"
                        result = messagebox.askyesno("Предупреждение", text)
                        if not result:
                            gmsh.finalize()
                            return 1
                else:
                    accepted_materials = False
                for i in range(len(data["materials"])):
                    if data["materials"][i] in mat_groups.keys():
                        mat_groups[data["materials"][i]].append(i + 1)
                    else:
                        mat_groups[data["materials"][i]] = [i + 1]
                for ky in mat_groups.keys():
                    gmsh.model.addPhysicalGroup(2, mat_groups[ky], name=f"Material {ky}", tag=ky)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при создании физических групп")
                gmsh.finalize()
                return 1

            try:
                gmsh.model.mesh.generate(2)
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при генерации двумерной сетки")
                gmsh.finalize()
                return 1

            try:
                stp = getint(spin0.get())
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Неверный формат степени сгущения сетки")
                gmsh.finalize()
                return 1
            try:
                for i in range(stp):
                    gmsh.model.mesh.refine()
            except Exception as e:
                print(e)
                messagebox.showwarning("Предупреждение", "Произошла ошибка при сгущении сетки")
                gmsh.finalize()
                return 1

            if do_check.get():
                nodes = gmsh.model.mesh.getNodes(-1, -1)
                new_nodes = []
                for i in range(len(nodes[0])):
                    new_nodes.append([nodes[1][i * 3], nodes[1][i * 3 + 1]])

                elements = gmsh.model.mesh.getElements(2, -1)
                new_elements = []
                if 2 in elements[0]:
                    triangles = elements[1][0]
                    for i in triangles:
                        elem = gmsh.model.mesh.getElement(i)
                        new_elem = [int(elem[1][0]), int(elem[1][1]), int(elem[1][2])]
                        new_elements.append(new_elem)
                ask_about_uncons = False
                print("Starting inconsistency check")
                for el1 in new_elements:
                    sides = [[el1[0], el1[1]], [el1[1], el1[2]], [el1[2], el1[0]]]
                    counters = [0, 0, 0]
                    for el2 in new_elements:
                        if el2 != el1:
                            inters = get_loops_intersections(new_nodes, el1, el2, 1)
                            try:
                                loop_points_in_loop(new_nodes, el2, el1, 1)
                            except:
                                print(el2, el1)
                                gmsh.finalize()
                                return 1
                            loop_ins = loop_points_in_loop(new_nodes, el1, el2, 1) or loop_points_in_loop(new_nodes,
                                                                                                          el2,
                                                                                                          el1, 1)
                            if inters[0] or len(inters[1]) > 1 or loop_ins or (
                                    len(inters[1]) == 0 and len(inters[2]) > 1):

                                ask_about_uncons = True
                                break
                            else:
                                if len(inters[1]):
                                    sd = inters[1][0][:2]
                                    sdr = inters[1][0][2:]
                                    ind = -1
                                    if sd in sides:
                                        ind = sides.index(sd)
                                    elif sdr in sides:
                                        ind = sides.index(sdr)
                                    if ind >= 0:
                                        counters[ind] += 1
                    for cnt in counters:
                        if cnt > 1:
                            ask_about_uncons = True
                            break
                    if ask_about_uncons:
                        break
                print("Finished inconsistency check")
                if ask_about_uncons:
                    result = messagebox.askyesno("Предупреждение",
                                                 f"Построенная сетка не является согласованной\nВсё равно сохранить её в файл?")
                    if not result:
                        gmsh.finalize()
                        return 1
            gmsh.write(name)
            messagebox.showinfo("Итог", f"Сетка была успешно построена и сохранена в файл:\n{name}")
            gmsh.finalize()
            update_short_info(name)
            return 0
        else:
            gmsh.finalize()
            return 1

    def rewrite_width_1(width):
        global points
        lbl_n1.configure(width=width)
        for pt in points:
            chld = pt.winfo_children()
            chld[0].configure(width=width)
        table1.update_idletasks()

    def fast_add_point(x="", y="", lc="0.1"):
        global points
        point = Frame(table1, padx=2)
        lbl = Label(point, text=str(len(points) + 1), font=(main_font, 10), relief='solid', borderwidth=3)
        lbl.pack(side='left')
        spin1 = Entry(point)
        spin1.pack(side='left', expand=1, fill='x')
        spin1.insert(0, x)
        spin2 = Entry(point)
        spin2.pack(side='left', expand=1, fill='x')
        spin2.insert(0, y)
        spin3 = Spinbox(point, from_=1e-3, to=1e3, width=10, increment=0.001, format="%.3f")
        spin3.delete(0, END)
        spin3.insert(0, lc)
        spin3.pack(side="left")
        constant = len(points)
        btn = Button(point, text="-", command=lambda: remove_point(point=constant))
        btn.pack(side='left')
        BindToolTip(btn, f"Удалить точку №{len(points) + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        point.pack(expand=1, fill='x')
        table1.update_idletasks()
        rewrite_width_1(len(str(len(points) + 1)))
        points.append(point)
        canvas1.configure(scrollregion=canvas1.bbox("all"))

    def reconfigure_point(point):
        global points
        pt = points[point]
        childs = pt.winfo_children()
        childs[0].configure(text=str(point))
        constant2 = point - 1
        childs[-1].configure(command=lambda: remove_point(point=constant2))
        BindToolTip(childs[-1], f"Удалить точку №{constant2 + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")

    def remove_point(point):
        global points
        for i in range(point + 1, len(points)):
            reconfigure_point(i)
        points[point].destroy()
        points.remove(points[point])
        table1.update_idletasks()
        rewrite_width_1(len(str(len(points))))
        canvas1.configure(scrollregion=canvas1.bbox("all"))

    def rewrite_width_2(width):
        global lps
        lbl_n2.configure(width=width)
        lbl_t_4.configure(width=width)
        for lpn in lps:
            chld = lpn.winfo_children()
            chld[0].configure(width=width)
            chld[-3].configure(width=width)
        table2.update_idletasks()

    def isar_changed(lp):
        global lps
        child = lps[lp].winfo_children()
        if ars[lp].get():
            child[3].configure(state="normal")
            child[3].delete(0, END)
            child[3].insert(0, "1")
            child[3].configure(state="readonly")
        else:
            child[3].configure(state="normal")
            child[3].delete(0, END)
            child[3].insert(0, "0")
            child[3].configure(state="disabled")

    def fast_add_loop(pnts="", isar=True, mat="1"):
        global lps
        global ars
        lp = Frame(table2, padx=2)
        lbl_p = Label(lp, text=str(len(lps) + 1), font=(main_font, 10), relief='solid', borderwidth=3)
        lbl_p.pack(side='left')
        text = Entry(lp)
        text.pack(side='left', expand=1, fill='x')
        text.insert(0, pnts)
        var = BooleanVar(value=isar)
        ars.append(var)
        constant3 = len(lps)
        chk = Checkbutton(lp, variable=var, command= lambda: isar_changed(constant3))
        chk.pack(side='left')
        spin = Spinbox(lp, from_=1, to=len(lps)+1, width=len(str(len(lps) + 1)), increment=1, state='normal')
        spin.pack(side="left")
        spin.delete(0, END)
        spin.insert(0, mat)
        if not isar:
            spin.delete(0, END)
            spin.insert(0, "0")
            spin.configure(state="disabled")
        else:
            spin.configure(state="readonly")
        cnt = 0
        for thlp in lps:
            value = thlp.winfo_children()[-3].get()
            thlp.winfo_children()[-3].configure(to=len(lps)+1, state="normal")
            thlp.winfo_children()[-3].delete(0, END)
            thlp.winfo_children()[-3].insert(0, value)
            if ars[cnt].get():
                thlp.winfo_children()[-3].configure(state="readonly")
            else:
                thlp.winfo_children()[-3].configure(state="disabled")
            cnt += 1

        btnlp = Button(lp, text="Собрать", command=lambda: quick_build(cur_loop=constant3))
        btnlp.pack(side='left')
        BindToolTip(btnlp, f"Конфигурировать контур №{len(lps) + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        btn = Button(lp, text="-", command=lambda: remove_loop(loop=constant3))
        btn.pack(side='left')
        BindToolTip(btn, f"Удалить контур №{len(lps) + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        lp.pack(expand=1, fill='x')
        table2.update_idletasks()
        rewrite_width_2(len(str(len(lps) + 1)))
        lps.append(lp)
        canvas2.configure(scrollregion=canvas2.bbox("all"))

    def reconfigure_loop_material(loop, delmat):
        global lps
        pt = lps[loop]
        childs = pt.winfo_children()[-3]
        value = int(childs.get())
        if value > delmat and delmat:
            value -= 1
        value = str(value)
        childs.configure(to=len(lps) - 1, state="normal")
        childs.delete(0, END)
        childs.insert(0, value)
        if ars[loop].get():
            childs.configure(state="readonly")
        else:
            childs.configure(state="disabed")

    def reconfigure_loop_other(loop):
        global lps
        pt = lps[loop]
        childs = pt.winfo_children()
        childs[0].configure(text=str(loop))
        constant4 = loop - 1
        childs[2].configure(command=lambda: isar_changed(constant4))
        childs[-2].configure(command=lambda: quick_build(cur_loop=constant4))
        childs[-1].configure(command=lambda: remove_loop(loop=constant4))
        BindToolTip(childs[-2], f"Конфигурировать контур №{constant4 + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        BindToolTip(childs[-1], f"Удалить контур №{constant4 + 1}.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")

    def find_greatest_free_material():
        mat_nums = []
        for lp in lps:
            value = int(lp.winfo_children()[-3].get())
            if value not in mat_nums and value:
                mat_nums.append(value)
        num = len(lps)
        while num in mat_nums:
            num -= 1
        return num

    def remove_loop(loop):
        global lps
        num = find_greatest_free_material()
        for i in range(0, loop):
            reconfigure_loop_material(i, num)
        for i in range(loop + 1, len(lps)):
            reconfigure_loop_material(i, num)
            reconfigure_loop_other(i)
        lps[loop].destroy()
        lps.remove(lps[loop])
        ars.remove(ars[loop])
        table2.update_idletasks()
        rewrite_width_2(len(str(len(lps))))
        canvas2.configure(scrollregion=canvas2.bbox("all"))

    def resize_frame_1(event):
        # Растягиваем frame на всю площадь canvas
        global points
        canvas1.itemconfig(frame_id_1, width=event.width)
        for p in points:
            p.pack(expand=1, fill='x')
        table1.update_idletasks()
        canvas1.configure(scrollregion=canvas1.bbox("all"))

    def resize_frame_2(event):
        # Растягиваем frame на всю площадь canvas
        global lps
        canvas2.itemconfig(frame_id_2, width=event.width)
        for lp in lps:
            lp.pack(expand=1, fill='x')
        table2.update_idletasks()
        canvas2.configure(scrollregion=canvas2.bbox("all"))

    def is_in_loop(points, point, loop, loop_num_start):
        angles = []
        if len(loop) < 3:
            return False
        x1 = points[loop[0] - loop_num_start][0] - points[point][0]
        y1 = points[loop[0] - loop_num_start][1] - points[point][1]
        x2 = points[loop[-1 + loop_num_start - 1] - loop_num_start][0] - points[point][0]
        y2 = points[loop[-1 + loop_num_start - 1] - loop_num_start][1] - points[point][1]
        if not x1 and not y1 or not x2 and not y2:
            return True
        angle = math.acos(round((x1 * x2 + y1 * y2) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x2 ** 2 + y2 ** 2) ** 0.5), 14))
        angles.append(angle)
        if x1 * y2 - x2 * y1:
            sgn = (x1 * y2 - x2 * y1) / abs(x1 * y2 - x2 * y1)
        else:
            sgn = 0
        for i in range(1, len(loop) - 1 + loop_num_start):
            x1 = points[loop[i] - loop_num_start][0] - points[point][0]
            y1 = points[loop[i] - loop_num_start][1] - points[point][1]
            x2 = points[loop[i - 1] - loop_num_start][0] - points[point][0]
            y2 = points[loop[i - 1] - loop_num_start][1] - points[point][1]
            if not x1 and not y1 or not x2 and not y2:
                return True
            angle = math.acos(round((x1 * x2 + y1 * y2) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x2 ** 2 + y2 ** 2) ** 0.5), 14))
            if x1 * y2 - x2 * y1:
                sgn2 = (x1 * y2 - x2 * y1) / abs(x1 * y2 - x2 * y1)
                if not sgn:
                    sgn = sgn2
                else:
                    angle *= sgn * sgn2

            angles.append(angle)

        sm = abs(round(sum(angles), 10))
        return sm == round(2 * math.pi, 10)

    def is_in_side(points, point, pointa, pointb, eps=0):
        pt = points[point]
        pta = points[pointa]
        ptb = points[pointb]
        if pta[0] == ptb[0]:
            ln = abs(pta[1] - ptb[1])
            return 2 * abs(pt[0] - pta[0]) <= eps * ln and min(pta[1], ptb[1]) - eps * (ln) / 2 <= pt[1] <= max(pta[1], ptb[1]) + eps * (ln) / 2
        elif pta[1] == ptb[1]:
            ln = abs(pta[0] - ptb[0])
            return 2 * abs(pt[1] - pta[1]) / ln <= eps * ln and min(pta[0], ptb[0]) - eps * (ln) / 2 <= pt[0] <= max(pta[0], ptb[0]) + eps * (ln) / 2
        else:
            t1 = (pt[0] - pta[0]) / (ptb[0] - pta[0])
            t2 = (pt[1] - pta[1]) / (ptb[1] - pta[1])
            return abs(t1 - t2) <= eps and -eps / 2 <= t1 <= 1 + eps / 2

    def return_state(x1, y1, x2, y2):
        if x1 == x2:
            if y1 == y2:
                return 'point'
            else:
                return 'vertical'
        else:
            if y1 == y2:
                return 'horizontal'
            else:
                return 'usual'

    def check_line_intersections(x11, y11, x12, y12, x21, y21, x22, y22):
        state_1 = return_state(x11, y11, x12, y12)
        state_2 = return_state(x21, y21, x22, y22)
        if state_1 == state_2 == 'point':
            if x11 == x21 and y11 == y21:
                return True
            else:
                return False
        elif state_1 == state_2 == 'vertical':
            if x11 == x21 and (min(y11, y12) <= y21 <= max(y11, y12) or min(y11, y12) <= y22 <= max(y11, y12)):
                return True
            else:
                return False
        elif state_1 == state_2 == 'horizontal':
            if y11 == y21 and (min(x11, x12) <= x21 <= max(x11, x12) or min(x11, x12) <= x22 <= max(x11, x12)):
                return True
            else:
                return False
        elif state_1 == state_2 == 'usual':
            if (y12 - y11) * (x22 - x21) - (x12 - x11) * (y22 - y21):
                t1 = ((y21 - y11) * (x22 - x21) + (y22 - y21) * (x11 - x21)) / (
                        (y12 - y11) * (x22 - x21) - (x12 - x11) * (y22 - y21))
                t2 = (x11 - x21 + t1 * (x12 - x11)) / (x22 - x21)
                if 0 <= t1 <= 1 and 0 <= t2 <= 1:
                    return True
            else:
                t1 = (x11 - x21) / (x22 - x21)
                t2 = (x12 - x21) / (x22 - x21)
                if (y21 + t1 * (y22 - y21) == y11 and 0 <= t1 <= 1) or (y21 + t2 * (y22 - y21) == y12 and 0 <= t2 <= 1):
                    return True
            return False
        else:
            if state_1 == 'point' or state_2 == 'point':
                if state_1 == 'point':
                    xp = x11
                    yp = y11
                    xo1 = x21
                    xo2 = x22
                    yo1 = y21
                    yo2 = y22
                else:
                    xp = x21
                    yp = y21
                    xo1 = x11
                    xo2 = x12
                    yo1 = y11
                    yo2 = y12
                state = return_state(xo1, yo1, xo2, yo2)
                if state == 'vertical':
                    if xp == xo1 and min(yo1, yo2) <= yp <= max(yo1, yo2):
                        return True
                    else:
                        return False
                elif state == 'horizontal':
                    if yp == yo1 and min(xo1, xo2) <= xp <= max(xo1, xo2):
                        return True
                    else:
                        return False
                else:
                    t = (xp - xo1) / (xo2 - xo1)
                    if yo1 + t * (yo2 - yo1) == yp:
                        return True
                    else:
                        return False
            elif state_1 == 'vertical' or state_2 == 'vertical':
                if state_1 == 'vertical':
                    xv = x11
                    yv1 = y11
                    yv2 = y12
                    xo1 = x21
                    xo2 = x22
                    yo1 = y21
                    yo2 = y22
                else:
                    xv = x21
                    yv1 = y21
                    yv2 = y22
                    xo1 = x11
                    xo2 = x12
                    yo1 = y11
                    yo2 = y12
                state = return_state(xo1, yo1, xo2, yo2)
                if state == 'horizontal':
                    if min(xo1, xo2) <= xv <= max(xo1, xo2) and min(yv1, yv2) <= yo1 <= max(yv1, yv2):
                        return True
                    else:
                        return False
                else:
                    t = (xv - xo1) / (xo2 - xo1)
                    if min(yv1, yv2) <= yo1 + t * (yo2 - yo1) <= max(yv1, yv2) and 0 <= t <= 1:
                        return True
                    else:
                        return False
            elif state_1 == 'horizontal' or state_2 == 'horizontal':
                if state_1 == 'horizontal':
                    xh1 = x11
                    xh2 = x12
                    yh = y11
                    xo1 = x21
                    xo2 = x22
                    yo1 = y21
                    yo2 = y22
                else:
                    xh1 = x21
                    xh2 = x22
                    yh = y22
                    xo1 = x11
                    xo2 = x12
                    yo1 = y11
                    yo2 = y12
                t = (yh - yo1) / (yo2 - yo1)
                if min(xh1, xh2) <= xo1 + t * (xo2 - xo1) <= max(xh1, xh2) and 0 <= t <= 1:
                    return True
                else:
                    return False

    def get_loops_intersections(pts, loopa, loopb, loop_num_start):
        intersections = []
        for i in range(len(loopa) - 1):
            for j in range(len(loopb) - 1):
                p11 = pts[loopa[i] - loop_num_start]
                p12 = pts[loopa[i + 1] - loop_num_start]
                p21 = pts[loopb[j] - loop_num_start]
                p22 = pts[loopb[j + 1] - loop_num_start]
                if check_line_intersections(p11[0], p11[1], p12[0], p12[1], p21[0], p21[1], p22[0], p22[1]):
                    intersections.append([loopa[i] + 1 - loop_num_start, loopa[i + 1] + 1 - loop_num_start, loopb[j] + 1 - loop_num_start, loopb[j + 1] + 1 - loop_num_start])
            if loop_num_start:
                p11 = pts[loopa[i] - 1]
                p12 = pts[loopa[i + 1] - 1]
                p21 = pts[loopb[len(loopb) - 1] - 1]
                p22 = pts[loopb[0] - 1]
                if check_line_intersections(p11[0], p11[1], p12[0], p12[1], p21[0], p21[1], p22[0], p22[1]):
                    intersections.append([loopa[i], loopa[i + 1],
                            loopb[len(loopb) - 1], loopb[0]])
        if loop_num_start:
            for j in range(len(loopb) - 1):
                p11 = pts[loopa[len(loopa) - 1] - 1]
                p12 = pts[loopa[0] - 1]
                p21 = pts[loopb[j] - 1]
                p22 = pts[loopb[j + 1] - 1]
                if check_line_intersections(p11[0], p11[1], p12[0], p12[1], p21[0], p21[1], p22[0], p22[1]):
                    intersections.append([loopa[len(loopa) - 1], loopa[0], loopb[j], loopb[j + 1]])
            if loop_num_start:
                p11 = pts[loopa[len(loopa) - 1] - loop_num_start]
                p12 = pts[loopa[0] - loop_num_start]
                p21 = pts[loopb[len(loopb) - 1] - loop_num_start]
                p22 = pts[loopb[0] - loop_num_start]
                if check_line_intersections(p11[0], p11[1], p12[0], p12[1], p21[0], p21[1], p22[0], p22[1]):
                    intersections.append([loopa[len(loopa) - 1], loopa[0],
                            loopb[len(loopb) - 1], loopb[0]])

        share_sides = []
        share_points = []
        intersect_sides = []
        for it in intersections:
            if it[0] == it[2] and it[1] == it[3] or it[0] == it[3] and it[1] == it[2]:
                share_sides.append(it)
            elif it[0] == it[2] and it[1] != it[3] or it[0] == it[3] and it[1] != it[2]:
                if it[0] not in share_points:
                    share_points.append(it[0])
            elif it[1] == it[3] and it[0] != it[2] or it[1] == it[2] and it[0] != it[3]:
                if it[1] not in share_points:
                    share_points.append(it[1])
            else:
                intersect_sides.append(it)
        return [intersect_sides, share_sides, share_points]

    def loop_points_in_loop(pts, loop_in, loop_out, loop_num_start):
        in_pts = []
        if len(loop_in) and len(loop_out):
            if loop_num_start:
                the_lp = loop_in
            else:
                the_lp = loop_in[:-1]
            for pp in the_lp:
                isinlp = is_in_loop(pts, pp - loop_num_start, loop_out, loop_num_start)
                if isinlp and pp not in loop_out:
                    in_pts.append(pp)
        return in_pts

    def is_in_loop_coords(points, point, loop, loop_num_start):
        angles = []
        if len(loop) < 3:
            return False
        x1 = points[loop[0] - loop_num_start][0] - point[0]
        y1 = points[loop[0] - loop_num_start][1] - point[1]
        x2 = points[loop[-1 + loop_num_start - 1] - loop_num_start][0] - point[0]
        y2 = points[loop[-1 + loop_num_start - 1] - loop_num_start][1] - point[1]
        if not x1 and not y1 or not x2 and not y2:
            return True
        angle = math.acos(round((x1 * x2 + y1 * y2) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x2 ** 2 + y2 ** 2) ** 0.5), 14))
        angles.append(angle)
        if x1 * y2 - x2 * y1:
            sgn = (x1 * y2 - x2 * y1) / abs(x1 * y2 - x2 * y1)
        else:
            sgn = 0
        for i in range(1, len(loop) - 1 + loop_num_start):
            x1 = points[loop[i] - loop_num_start][0] - point[0]
            y1 = points[loop[i] - loop_num_start][1] - point[1]
            x2 = points[loop[i - 1] - loop_num_start][0] - point[0]
            y2 = points[loop[i - 1] - loop_num_start][1] - point[1]
            if not x1 and not y1 or not x2 and not y2:
                return True
            angle = math.acos(round((x1 * x2 + y1 * y2) / ((x1 ** 2 + y1 ** 2) ** 0.5 * (x2 ** 2 + y2 ** 2) ** 0.5), 14))
            if x1 * y2 - x2 * y1:
                sgn2 = (x1 * y2 - x2 * y1) / abs(x1 * y2 - x2 * y1)
                if not sgn:
                    sgn = sgn2
                else:
                    angle *= sgn * sgn2

            angles.append(angle)

        sm = abs(round(sum(angles), 10))
        return sm == round(2 * math.pi, 10)

    def loop_middle_points_in_loop(pts, loop_in, loop_out, loop_num_start):
        if len(loop_in) and len(loop_out):
            if loop_num_start:
                the_lp = loop_in
            else:
                the_lp = loop_in[:-1]
            for pp in range(len(the_lp) - 1):
                middle = [max(pts[the_lp[pp] - loop_num_start][0], pts[the_lp[pp + 1] - loop_num_start][0]) - min(pts[the_lp[pp] - loop_num_start][0], pts[the_lp[pp + 1] - loop_num_start][0]),
                          max(pts[the_lp[pp] - loop_num_start][1], pts[the_lp[pp + 1] - loop_num_start][1]) - min(pts[the_lp[pp] - loop_num_start][0], pts[the_lp[pp + 1] - loop_num_start][1])]
                isinlp = is_in_loop_coords(pts, middle, loop_out, loop_num_start)
                if not isinlp:
                    return False
            middle = [max(pts[the_lp[0] - loop_num_start][0], pts[the_lp[-1] - loop_num_start][0]) - min(pts[the_lp[0] - loop_num_start][0],
                                                                                  pts[the_lp[-1] - loop_num_start][0]),
                      max(pts[the_lp[0] - loop_num_start][1], pts[the_lp[-1] - loop_num_start][1]) - min(pts[the_lp[0] - loop_num_start][0],
                                                                                  pts[the_lp[-1] - loop_num_start][1])]
            isinlp = is_in_loop_coords(pts, middle, loop_out, loop_num_start)
            if not isinlp:
                return False
        return True

    def get_view_data():
        preview_data = []
        pts = []
        ls = []
        extra_pts = [[], []]
        extrn = []
        intrn = []
        inclusions = []
        are_areas = []
        embedings = []

        if not len(points):
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум одну точку")
            return []
        for i in range(len(points)):
            children = points[i].winfo_children()
            try:
                x = float(children[1].get())
                y = float(children[2].get())
                if [x, y, 0] in pts:
                    messagebox.showwarning("Предупреждение", f"Точка N {i + 1} совпадает с точкой N {pts.index([x, y, 0 ]) + 1}")
                    return []
                pts.append([x, y, 0])
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Координаты точки N {i + 1} заданы некорректно")
                return []
        contour_usage = [False for ctr in range(len(lps))]
        intercrosses = [False for fl in range(len(lps))]
        for i in range(len(lps)):
            children = lps[i].winfo_children()
            new_loop = []
            inclusion = []
            ar = ars[i].get()
            if ar:
                contour_usage[i] = True
            try:
                lp = children[1].get().split(' ')
                while '' in lp:
                    lp.remove('')
                if not len(lp):
                    messagebox.showwarning("Предупреждение", f"Контур N {i + 1} не содержит вершин")
                    return []
                lp[0] = int(lp[0]) - 1
                new_loop.append(lp[0])

                for j in range(1, len(lp)):
                    lp[j] = int(lp[j]) - 1
                    if j != lp.index(lp[j]):
                        messagebox.showwarning("Предупреждение",
                                               f"Точка N {lp[j] + 1} встручается в контуре N {i + 1} более одного раза")
                        return []
                    if lp[j] < 0 or lp[j] > len(pts) - 1:
                        messagebox.showerror("Ошибка",
                                             f" В контур N {i + 1} включается несуществующая точка N {lp[j] + 1}")
                        return []
                    new_loop.append(lp[j])

                new_loop.append(lp[0])
                try:
                    stp = getdouble(spin2.get())
                except Exception as e:
                    print(e)
                    messagebox.showwarning("Предупреждение", "Неверный формат погрешности попадания точки в отрезок")
                    gmsh.finalize()
                    return []
                for pnt in range(len(pts)):
                    for pl in range(1, len(new_loop)):
                        if  pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                            if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                if pnt in new_loop[:-1]:
                                    result = messagebox.askyesno("Предупреждение",
                                                                 f"Точка N {pnt + 1} повторно включается в контур N {i + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                                new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                intercrosses[i] = True
                                break
                ls.append(new_loop)

                are_areas.append(ar)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Индексы вершин внешнего контура области N {i + 1} заданы некорректно")
                return []


            inclusions.append([])
            embedings.append([[], []])

        for cntr1 in range(len(ls)):
            for cntr2 in range(cntr1, len(ls)):
                if cntr1 == cntr2:
                    cntr = ls[cntr1]
                    if len(get_loops_intersections(pts, cntr, cntr, 0)[0]):
                        result = messagebox.askyesno("Предупреждение", f"Контур N {cntr1 + 1} имеет пересекающиеся отрезки \n Хотите продолжить?")
                        intercrosses[cntr1] = True
                        if not result:
                            return []
                else:
                    inter_data = get_loops_intersections(pts, ls[cntr1], ls[cntr2], 0)
                    if len(inter_data[0]):
                        result = messagebox.askyesno("Предупреждение", f"Контур N {cntr1 + 1} и контур N {cntr2 + 1} имеют \n пересекающиеся отрезки\n Хотите продолжить?")
                        if not result:
                            return []
                    else:
                        isar1 = ars[cntr1].get()
                        isar2 = ars[cntr2].get()
                        in_pts_12 = loop_points_in_loop(pts, ls[cntr1], ls[cntr2], 0)
                        in_12_fact = len(in_pts_12) + len(inter_data[2]) == len(ls[cntr1]) - 1
                        in_pts_21 = loop_points_in_loop(pts, ls[cntr2], ls[cntr1], 0)
                        in_21_fact = len(in_pts_21) + len(inter_data[2]) == len(ls[cntr2]) - 1
                        in_12_incl = False
                        in_21_incl = False
                        for incl in inclusions[cntr2]:
                            inter_perm = get_loops_intersections(pts, ls[cntr1], ls[incl], 0)
                            in_pts_i_12 = loop_points_in_loop(pts, ls[cntr1], ls[incl], 0)
                            in_12_i_fact = len(in_pts_i_12) + len(inter_perm[2]) == len(ls[cntr1]) - 1
                            if in_12_i_fact:
                                in_12_incl = True
                                break
                        for incl in inclusions[cntr1]:
                            inter_perm = get_loops_intersections(pts, ls[cntr2], ls[incl], 0)
                            in_pts_i_21 = loop_points_in_loop(pts, ls[cntr2], ls[incl], 0)
                            in_21_i_fact = len(in_pts_i_21) + len(inter_perm[2]) == len(ls[cntr2]) - 1
                            if in_21_i_fact:
                                in_21_incl = True
                                break
                        in_12_mid = loop_middle_points_in_loop(pts, ls[cntr1], ls[cntr2], 0)
                        in_21_mid = loop_middle_points_in_loop(pts, ls[cntr2], ls[cntr1], 0)
                        if isar1 and isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and cntr1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1)
                            elif in_21_fact and not in_21_incl and not in_21_mid and cntr2 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2)
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    result = messagebox.askyesno("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    result = messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                        elif isar1 or isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and isar2 and cntr1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1)
                                contour_usage[cntr1] = True
                            elif in_21_fact and not in_21_incl and not in_21_mid and isar1 and cntr2 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2)
                                contour_usage[cntr2] = True
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    result = messagebox.askyesno("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    result = messagebox.askyesno("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                            if isar2 and in_12_fact and len(demi_barrier_points):
                                result = messagebox.askyesno("Предупреждение",
                                                       f"Контур N {cntr1 + 1} имеет общие стороны с контуром N {cntr2 + 1},\n будучи пустым и включённым в него\n Хотите продолжить?")
                                if not result:
                                    return []
                            elif isar1 and in_21_fact and len(demi_barrier_points):
                                result = messagebox.askyesno("Предупреждение",
                                                       f"Контур N {cntr2 + 1} имеет общие стороны с контуром N {cntr1 + 1},\n будучи пустым и включённым в него\n Хотите продолжить?")
                                if not result:
                                    return []
                        else:
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    result = messagebox.askyesno("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    result = messagebox.askyesno("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n Хотите продолжить?")
                                    if not result:
                                        return []
            theincls = inclusions[cntr1]
            for cntr2 in range(cntr1):
                sideincl = inclusions[cntr2]
                for inc in theincls:
                    if cntr1 in sideincl and inc in sideincl:
                        sideincl.remove(inc)

        try:
            eps2 = getdouble(spin3.get())
        except Exception as e:
            print(e)
            messagebox.showwarning("Предупреждение", "Неверный формат порога площади контуров")
            gmsh.finalize()
            return []
        for lp in range(len(ls)):
            new_loop = [[], []]

            if not check_area(pts, ls[lp], 0, eps2) and not intercrosses[lp]:
                result = messagebox.askyesno("Предупреждение",
                                             f"Площадь контура N {lp + 1} меньше допустимого значения\n Хотите продолжить?")
                if not result:
                    return []
            for j in range(len(ls[lp])):
                new_loop[0].append(pts[ls[lp][j]][0])
                new_loop[1].append(pts[ls[lp][j]][1])
                pts[ls[lp][j]][2] = 1
            preview_data.append(new_loop)

        for chk in range(len(ls)):
            if not contour_usage[chk]:
                result = messagebox.askyesno("Предупреждение",
                                             f"Контур N {chk + 1} не используется при построении\n Хотите продолжить?")
                if not result:
                    return []

        for i in range(len(lps)):
            children = lps[i].winfo_children()
            new_loop = []
            isar = ars[i].get()
            is_included = False
            for inc in inclusions:
                if i in inc:
                    is_included = True
            if not is_included and isar or is_included and not isar:
                lp = children[1].get().split(' ')
                while '' in lp:
                    lp.remove('')
                for plp in range(len(lp)):
                    lp[plp] = int(lp[plp]) - 1
                    new_loop.append(lp[plp])
                new_loop.append(lp[0])
                try:
                    stp = getdouble(spin2.get())
                except Exception as e:
                    print(e)
                    messagebox.showwarning("Предупреждение", "Неверный формат погрешности попадания точки в отрезок")
                    gmsh.finalize()
                    return []
                for pnt in range(len(pts)):
                    for pl in range(1, len(new_loop)):
                        if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                            if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                break
                for j in range(1, len(new_loop)):
                    new_line = [new_loop[j - 1], new_loop[j]]
                    if new_line in extrn:
                        extrn.remove(new_line)
                        intrn.append(new_line)
                    elif [new_line[1], new_line[0]] in extrn:
                        extrn.remove([new_line[1], new_line[0]])
                        intrn.append(new_line)
                    elif new_line not in intrn and [new_line[1], new_line[0]] not in intrn:
                        extrn.append(new_line)

        external_lines = []
        for ex in extrn:
            external_lines.append([[pts[ex[0]][0], pts[ex[1]][0]], [pts[ex[0]][1], pts[ex[1]][1]]])

        for p in range(len(pts)):
            if not pts[p][2]:
                for lpp in range(len(ls)):
                    a = ars[lpp].get()
                    if is_in_loop(pts, p, ls[lpp], 0) and a:
                        is_internal = True
                        for lppp in inclusions[lpp]:
                            if is_in_loop(pts, p, ls[lppp], 0):
                                is_internal = False
                        if is_internal:
                            embedings[lpp][0].append(pts[p][0])
                            embedings[lpp][1].append(pts[p][1])
                            pts[p][2] = 1
                            break
        for p in range(len(pts)):
            if not pts[p][2]:
                extra_pts[0].append(pts[p][0])
                extra_pts[1].append(pts[p][1])
        return [preview_data, extra_pts, external_lines, inclusions, are_areas, embedings]

    def loops_preview():

        check = get_view_data()
        if len(check):
            labels = []
            colors = []
            area_list = []
            plt.clf()
            n = 1
            for pr in range(len(check[0])):
                if check[4][pr]:
                    pl = plt.plot(check[0][pr][0], check[0][pr][1], marker='o')
                    colors.append(pl[0].get_color())
                    labels.append(f"Область N {n}, Контур N {pr + 1}")
                    area_list.append(n - 1)
                    n += 1
                    if show_coords.get():
                        for i in range(len(check[0][pr][0])):
                            plt.annotate(f'({check[0][pr][0][i]}; {check[0][pr][1][i]})',
                                     (check[0][pr][0][i], check[0][pr][1][i]),
                                     textcoords="offset points", xytext=(0, 1), ha='center')
            if len(check[1][0]):
                labels.append("Невошедшие точки")
                plt.scatter(check[1][0], check[1][1], color="k")
                if show_coords.get():
                    for i in range(len(check[1][0])):
                        plt.annotate(f'({check[1][0][i]}; {check[1][1][i]})', (check[1][0][i], check[1][1][i]), textcoords="offset points", xytext=(0, 1), ha='center')
            m = 0
            for pr in range(len(check[0])):
                if not check[4][pr]:
                    add_unused = True
                    for pr2 in check[3]:
                        if pr in pr2:
                            add_unused = False
                            break
                    if add_unused:
                        m += 1
                        labels.append(F"Неиспользуемый контур N {m}({pr + 1})")
                        plt.plot(check[0][pr][0], check[0][pr][1], marker='*', linestyle=":")
                        if show_coords.get():
                            for i in range(len(check[0][pr][0])):
                                plt.annotate(f'({check[0][pr][0][i]}; {check[0][pr][1][i]})', (check[0][pr][0][i], check[0][pr][1][i]),
                                         textcoords="offset points", xytext=(0, 1), ha='center')

            if len(check[2]):
                labels.append("Внешний контур")
                for ln in check[2]:
                    plt.plot(ln[0], ln[1], marker='x', linestyle="-.", color="k")

            n = 0
            clrs = []
            for prp in range(len(check[0])):
                if check[4][prp]:
                    clrs.append(colors[n])
                    n += 1
                else:
                    clrs.append("w")
            for pr in range(len(check[0])):
                if check[4][pr]:
                    plt.fill(check[0][pr][0], check[0][pr][1], alpha=0.2, color=clrs[pr])
                    for loop_ind in check[3][pr]:
                        plt.fill(check[0][loop_ind][0], check[0][loop_ind][1], color="w")
                        plt.fill(check[0][loop_ind][0], check[0][loop_ind][1], alpha=0.2, color=clrs[loop_ind])
                        if not check[4][loop_ind]:
                            plt.plot(check[0][loop_ind][0], check[0][loop_ind][1], marker='o', color=clrs[loop_ind])
                    plt.scatter(check[5][pr][0], check[5][pr][1], marker='o', color=clrs[pr])
                    if show_coords.get():
                        for i in range(len(check[5][pr][0])):
                            plt.annotate(f'({check[5][pr][0][i]}; {check[5][pr][1][i]})', (check[5][pr][0][i], check[5][pr][1][i]), textcoords="offset points", xytext=(0, 1), ha='center')
            if len(check[1][0]):
                plt.scatter(check[1][0], check[1][1], color="k")
            if len(check[2]):
                for ln in check[2]:
                    plt.plot(ln[0], ln[1], marker='x', linestyle="-.", color="k")
            plt.legend(labels, loc="upper right")
            plt.grid()
            plt.title("График контуров и областей")
            plt.show()

    def get_fast_data():
        global accepted_materials
        pts = []
        lcs_nums = []
        mat_nums = []
        pts_use = []
        closed_loops = []
        inclusions = []

        if not len(points):
            messagebox.showwarning("Предупреждение", "Необходимо задать как минимум одну точку")
            return []
        for i in range(len(points)):
            children = points[i].winfo_children()
            try:
                x = float(children[1].get())
                y = float(children[2].get())
                if [x, y] in pts:
                    messagebox.showwarning("Предупреждение", f"Точка N {i + 1} совпадает с точкой N {pts.index([x, y]) + 1}")
                    return []
                pts.append([x, y])
                pts_use.append(0)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Координаты точки N {i + 1} заданы некорректно")
                return []
            try:
                lc_num = float(children[3].get())
                lcs_nums.append(lc_num)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Параметр Lc точки N {i + 1} задан некорректно")
                return []

        for i in range(len(lps)):
            children = lps[i].winfo_children()
            try:
                lp = children[1].get().split(' ')
                while '' in lp:
                    lp.remove('')
                if not len(lp):
                    messagebox.showwarning("Предупреждение", f"Контур N {i + 1} не содержит вершин")
                    return []
                for j in range(len(lp)):
                    lp[j] = int(lp[j])
                    if j != lp.index(lp[j]):
                        messagebox.showwarning("Предупреждение",
                                               f"Точка N {lp[j]} встречается в контуре N {i + 1} более одного раза")
                        return []
                    if lp[j] - 1 < 0 or lp[j] - 1 > len(pts) - 1:
                        messagebox.showerror("Ошибка",
                                             f" В контур N {i + 1} включается несуществующая точка N {lp[j]}")
                        return []
                    pts_use[lp[j] - 1] = 1
                try:
                    stp = getdouble(spin2.get())
                except Exception as e:
                    print(e)
                    messagebox.showwarning("Предупреждение", "Неверный формат погрешности попадания точки в отрезок")
                    gmsh.finalize()
                    return []
                for pnt in range(len(pts)):
                    need_check_last = True
                    for pl in range(1, len(lp)):
                        if  pnt != lp[pl] - 1 and pnt != lp[pl - 1] - 1:
                            if is_in_side(pts, pnt, lp[pl - 1] - 1, lp[pl] - 1, stp):
                                if pnt + 1 not in lp:
                                    lp = lp[:pl] + [pnt + 1] + lp[pl:]
                                    need_check_last = False
                                    pts_use[pnt] = 1
                                    break
                                else:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Точка N {pnt + 1} повторно включается в контур N {i + 1}")
                                    return []
                    if need_check_last and pnt != lp[len(lp) - 1] - 1 and pnt != lp[0] - 1:
                        if is_in_side(pts, pnt, lp[len(lp) - 1] - 1, lp[0] - 1, stp):
                            if pnt + 1 not in lp:
                                lp.append(pnt + 1)
                                pts_use[pnt] = 1
                            else:
                                messagebox.showwarning("Предупреждение",
                                                       f"Точка N {pnt + 1} повторно включается в контур N {i + 1}")
                                return []

                closed_loops.append(lp)
                inclusions.append([])
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Индексы внешних вершин контура N {i + 1} заданы некорректно")
                return []


            try:
                mt = int(children[3].get())
                mat_nums.append(mt)
            except Exception as e:
                print(e)
                messagebox.showerror("Ошибка", f"Номер материала области с внешним контуром N {i + 1} задан некорректно")
                return []

        for cntr1 in range(len(closed_loops)):
            for cntr2 in range(cntr1, len(closed_loops)):
                if cntr1 == cntr2:
                    cntr = closed_loops[cntr1]
                    if len(get_loops_intersections(pts, cntr, cntr, 1)[0]):
                        messagebox.showwarning("Предупреждение", f"Контур N {cntr1 + 1} имеет пересекающиеся отрезки")
                        return []
                else:
                    inter_data = get_loops_intersections(pts, closed_loops[cntr1], closed_loops[cntr2], 1)
                    if len(inter_data[0]):
                        messagebox.showwarning("Предупреждение", f"Контур N {cntr1 + 1} и контур N {cntr2 + 1} имеют \n пересекающиеся отрезки")
                        return []
                    else:
                        isar1 = ars[cntr1].get()
                        isar2 = ars[cntr2].get()
                        in_pts_12 = loop_points_in_loop(pts, closed_loops[cntr1], closed_loops[cntr2], 1)
                        in_12_fact = len(in_pts_12) + len(inter_data[2]) == len(closed_loops[cntr1])
                        in_pts_21 = loop_points_in_loop(pts, closed_loops[cntr2], closed_loops[cntr1], 1)
                        in_21_fact = len(in_pts_21) + len(inter_data[2]) == len(closed_loops[cntr2])
                        in_12_incl = False
                        in_21_incl = False
                        for incl in inclusions[cntr2]:
                            inter_perm = get_loops_intersections(pts, closed_loops[cntr1], closed_loops[incl - 1], 1)
                            in_pts_i_12 = loop_points_in_loop(pts, closed_loops[cntr1], closed_loops[incl - 1], 1)
                            in_12_i_fact = len(in_pts_i_12) + len(inter_perm[2]) == len(closed_loops[cntr1])
                            if in_12_i_fact:
                                in_12_incl = True
                                break
                        for incl in inclusions[cntr1]:
                            inter_perm = get_loops_intersections(pts, closed_loops[cntr2], closed_loops[incl - 1], 1)
                            in_pts_i_21 = loop_points_in_loop(pts, closed_loops[cntr2], closed_loops[incl - 1], 1)
                            in_21_i_fact = len(in_pts_i_21) + len(inter_perm[2]) == len(closed_loops[cntr2])
                            if in_21_i_fact:
                                in_21_incl = True
                                break
                        in_12_mid = loop_middle_points_in_loop(pts, closed_loops[cntr1], closed_loops[cntr2], 1)
                        in_21_mid = loop_middle_points_in_loop(pts, closed_loops[cntr2], closed_loops[cntr1], 1)
                        if isar1 and isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and cntr1 + 1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1+1)
                            elif in_21_fact and not in_21_incl and not in_21_mid and cntr2 + 1 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2+1)
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}")
                                    return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}")
                                    return []
                        elif isar1 or isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and isar2 and cntr1 + 1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1+1)
                            elif in_21_fact and not in_21_incl and not in_21_mid and isar1 and cntr2 + 1 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2+1)
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}")
                                    return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}")
                                    return []
                            if isar2 and in_12_fact and len(demi_barrier_points):
                                messagebox.showwarning("Предупреждение",
                                                       f"Контур N {cntr1 + 1} имеет общие стороны с контуром N {cntr2 + 1},\n будучи пустым и включённым в него")
                                return []
                            elif isar1 and in_21_fact and len(demi_barrier_points):
                                messagebox.showwarning("Предупреждение",
                                                       f"Контур N {cntr2 + 1} имеет общие стороны с контуром N {cntr1 + 1},\n будучи пустым и включённым в него")
                                return []
                        else:
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}")
                                    return []
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    messagebox.showwarning("Предупреждение",
                                                           f"Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}")
            theincls = inclusions[cntr1]
            for cntr2 in range(cntr1):
                sideincl = inclusions[cntr2]
                for inc in theincls:
                    if cntr1 + 1 in sideincl and inc in sideincl:
                        sideincl.remove(inc)

        try:
            eps2 = getdouble(spin3.get())
        except Exception as e:
            print(e)
            messagebox.showwarning("Предупреждение", "Неверный формат порога площади контуров")
            gmsh.finalize()
            return []
        for lp in range(len(closed_loops)):
            if not check_area(pts, closed_loops[lp], 1, eps2):
                messagebox.showwarning("Предупреждение",
                                       f"Площадь контура N {lp + 1} меньше допустимого значения")
                return []
        lns = []
        brd = []
        cnts = []
        ares = []
        mats = []
        emb = []
        intrn = []
        contour_usage = [False for flp in range(len(lps))]
        for nlp in range(len(closed_loops)):
            isar = ars[nlp].get()

            if isar:
                contour_usage[nlp] = True
                addition = []
                for pt in range(len(pts)):
                    if not pts_use[pt] and is_in_loop(pts, pt, closed_loops[nlp], 1):
                        is_included = True
                        for nlpp in inclusions[nlp]:
                            if is_in_loop(pts, pt, closed_loops[nlpp - 1], 1):
                                is_included = False
                        if is_included:
                            pts_use[pt] = 1
                            addition.append(pt + 1)
                emb.append(addition)
                ares.append([nlp + 1])
                for incl in inclusions[nlp]:
                    contour_usage[incl - 1] = True
                ares[-1].extend(inclusions[nlp])
                mats.append(mat_nums[nlp])

            cnt = []
            curr_loop = closed_loops[nlp]
            for np in range(len(curr_loop) - 1):
                new_line = [curr_loop[np], curr_loop[np + 1]]
                minus_new_line = [curr_loop[np + 1], curr_loop[np]]
                if new_line in lns:
                    ind = lns.index(new_line) + 1
                    cnt.append(ind)
                elif minus_new_line in lns:
                    ind = lns.index(minus_new_line) + 1
                    cnt.append(-ind)
                else:
                    lns.append(new_line)
                    cnt.append(len(lns))
            new_line = [curr_loop[len(curr_loop) - 1], curr_loop[0]]
            minus_new_line = [curr_loop[0], curr_loop[len(curr_loop) - 1]]
            if new_line in lns:
                ind = lns.index(new_line) + 1
                cnt.append(ind)
            elif minus_new_line in lns:
                ind = lns.index(minus_new_line) + 1
                cnt.append(-ind)
            else:
                lns.append(new_line)
                cnt.append(len(lns))
            cnts.append(cnt)
        for nlp in range(len(closed_loops)):
            isar = ars[nlp].get()
            curr_loop = closed_loops[nlp]
            not_included = True
            for incl in inclusions:
                if nlp + 1 in incl:
                    not_included = False
                    break
            if not_included == isar:
                for np in range(len(curr_loop) - 1):
                    new_line = [curr_loop[np], curr_loop[np + 1]]
                    minus_new_line = [curr_loop[np + 1], curr_loop[np]]
                    if new_line in lns:
                        ind = lns.index(new_line) + 1
                    else:
                        ind = lns.index(minus_new_line) + 1
                    if ind in brd:
                        brd.remove(ind)
                        intrn.append(ind)
                    elif ind not in intrn:
                        brd.append(ind)
                new_line = [curr_loop[len(curr_loop) - 1], curr_loop[0]]
                minus_new_line = [curr_loop[0], curr_loop[len(curr_loop) - 1]]
                if new_line in lns:
                    ind = lns.index(new_line) + 1
                else:
                    ind = lns.index(minus_new_line) + 1
                if ind in brd:
                    brd.remove(ind)
                    intrn.append(ind)
                elif ind not in intrn:
                    brd.append(ind)

        for chk in range(len(closed_loops)):
            if not contour_usage[chk]:
                result = messagebox.askyesno("Предупреждение",
                                             f"Контур N {chk + 1} не используется при построении\n Хотите продолжить?")
                if not result:
                    return []

        for cnt in range(len(cnts)):
            cnts[cnt] = reconfigure_contour(pts, lns, cnts[cnt])

        for i in range(len(pts)):
            pts[i] = str(pts[i][0]) + " " + str(pts[i][1]) + "\n"

        for i in range(len(lcs_nums)):
            lcs_nums[i] = str(lcs_nums[i])
        lcs_nums = '\n'.join(lcs_nums) + "\n"

        for i in range(len(lns)):
            lns[i] = str(lns[i][0]) + " " + str(lns[i][1]) + "\n"

        for j in range(len(brd)):
            brd[j] = str(brd[j])
        brd = ' '.join(brd) + "\n"

        for i in range(len(cnts)):
            for j in range(len(cnts[i])):
                cnts[i][j] = str(cnts[i][j])
            cnts[i] = ' '.join(cnts[i]) + "\n"

        for i in range(len(ares)):
            for j in range(len(ares[i])):
                ares[i][j] = str(ares[i][j])
            ares[i] = ' '.join(ares[i]) + "\n"

        nm = 1
        while nm in mats:
            nm += 1
        if nm < max(mats):
            text = f"Материал №{nm} не используется при построении сетки, хотя материалы с большими"
            if nm > 1:
                text += " и меньшими "
            text += "номерами используются.\nЭто может привести к путанице при определении параметров материалов областей.\nВсё равно перенести данные во вкладку 'Входные данные'?"
            accepted_materials = messagebox.askyesno("Предупреждение", text)
            if not accepted_materials:
                return []

        for i in range(len(mats)):
            mats[i] = str(mats[i])
        mats = '\n'.join(mats) + "\n"

        embeding = {}
        ind = 1
        for i in emb:
            if len(i):
                for j in range(len(i)):
                    i[j] = str(i[j])
                embeding[str(ind)] = str(ind) + "\n" + ' '.join(i) + "\n"
            ind += 1
        emb = embeding

        messagebox.showinfo("Итог", "Данные успешно перенесены во вкладку 'Входные данные'")
        return {"nodes": pts, "lcs": lcs_nums, "lines": lns, "border": brd, "contoures": cnts, "areas": ares, "materials": mats, "embed_nodes": emb}

    def reconfigure_contour(pts, lns, cnt):
        line_data = []
        for ln in lns:
            line = [pts[ln[0] - 1], pts[ln[1] - 1]]
            line_data.append(line)

        if not is_cw(line_data, cnt) < 0:
            new_contour = inverse_contour(cnt)
        else:
            new_contour = cnt

        return new_contour

    def is_cw(line_data, cnt_data):
        sm = 0
        for pt in range(len(cnt_data) - 1):
            cur_side = cnt_data[pt]
            next_side = cnt_data[pt + 1]
            if cur_side > 0:
                cur_side = line_data[cur_side - 1]
            else:
                cur_side = [line_data[-cur_side - 1][1], line_data[-cur_side - 1][0]]
            if next_side > 0:
                next_side = line_data[next_side - 1]
            else:
                next_side = [line_data[-next_side - 1][1], line_data[-next_side - 1][0]]
            xa = cur_side[1][0] - cur_side[0][0]
            ya = cur_side[1][1] - cur_side[0][1]
            xb = next_side[1][0] - next_side[0][0]
            yb = next_side[1][1] - next_side[0][1]
            sm -= xa * yb - xb * ya

        cur_side = cnt_data[-1]
        next_side = cnt_data[0]
        if cur_side > 0:
            cur_side = line_data[cur_side - 1]
        else:
            cur_side = [line_data[-cur_side - 1][1], line_data[-cur_side - 1][0]]
        if next_side > 0:
            next_side = line_data[next_side - 1]
        else:
            next_side = [line_data[-next_side - 1][1], line_data[-next_side - 1][0]]
        xa = cur_side[1][0] - cur_side[0][0]
        ya = cur_side[1][1] - cur_side[0][1]
        xb = next_side[1][0] - next_side[0][0]
        yb = next_side[1][1] - next_side[0][1]
        sm -= xa * yb - xb * ya

        return sm

    def inverse_contour(cnt):
        new_cnt = []
        for cn in range(len(cnt) - 1, -1, -1):
            new_cnt.append(-cnt[cn])
        return new_cnt

    def check_area(pts, loop, loop_num_start, eps=0):
        sm = 0
        for i in range(len(loop) - 1):
            pti = pts[loop[i] - loop_num_start]
            pti_1 = pts[loop[i + 1] - loop_num_start]
            sm += pti[0] * pti_1[1] - pti[1] * pti_1[0]
        if loop_num_start:
            pti = pts[loop[-1] - loop_num_start]
            pti_1 = pts[loop[0] - loop_num_start]
            sm += pti[0] * pti_1[1] - pti[1] * pti_1[0]
        return abs(sm) / 2 >= eps

    def transfer_data():
        data = get_fast_data()
        if len(data):
            return write_data(data)
        return 1

    def transfer_and_generate():
        if not transfer_data():
            generate_mesh()

    def open_gmsh():
        gmsh.initialize()
        name = filename.get()
        if not name:
            gmsh.finalize()
            messagebox.showwarning("Предупреждение", "Пустое имя файла")
            return 1
        if name[-4:] != ".msh":
            name += ".msh"
        try:
            gmsh.open(name)
            if '-nopopup' not in sys.argv:
                gmsh.fltk.run()
            gmsh.finalize()
        except Exception as e:
            print(e)
            gmsh.finalize()
            messagebox.showerror("Ошибка", "Не удалось открыть указанный файл")
            return 1
        return 0

    def quick_build(cur_loop):
        global points
        global lps
        global ars

        def write_loop_info(index):
            compilation_info.configure(state="normal")
            compilation_info.insert(index, f"Информация о собираемом контуре:\nТочки контура: {loop_conf}")
            compilation_info.configure(state="disabled")

        def check_warnings(warn_count):
            if warn_count:
                finish_btn.configure(state="disabled")
            else:
                finish_btn.configure(state="normal")

        def point_up(pnt):
            global loop_conf
            if pnt == 0:
                loop_conf = loop_conf[1:] + [loop_conf[0]]
            else:
                cnst = loop_conf[pnt - 1]
                loop_conf[pnt - 1] = loop_conf[pnt]
                loop_conf[pnt] = cnst
            loops_preview_2()

        def point_down(pnt):
            global loop_conf
            if pnt == len(loop_conf) - 1:
                loop_conf =  [loop_conf[-1]] + loop_conf[:-1]
            else:
                cnst = loop_conf[pnt + 1]
                loop_conf[pnt + 1] = loop_conf[pnt]
                loop_conf[pnt] = cnst
            loops_preview_2()

        def reconfigure_point_2(pnt, ind):
            pt = table3.winfo_children()[ind]
            constant_pt = loop_conf.index(pnt)
            pt.winfo_children()[-3].configure(state="normal",
                                                  command=lambda: point_up(pnt=constant_pt))
            pt.winfo_children()[-1].configure(state="normal",
                                                  command=lambda: point_down(pnt=constant_pt))

        def get_view_data_2():
            preview_data = []
            pts = []
            ls = []
            extra_pts = [[], []]
            extrn = []
            intrn = []
            inclusions = []
            are_areas = []
            embedings = []
            compilation_info.configure(state="normal")
            compilation_info.delete(1.0, END)
            index = 1.0
            warning_count = 0
            check_warnings(warning_count)
            new_points = table3.winfo_children()
            for pnt in range(len(new_points)):
                thepnt = new_points[pnt]
                num = int(thepnt.winfo_children()[0].cget("text"))
                if num in loop_conf:
                    thepnt.winfo_children()[-2].configure(text=str(loop_conf.index(num) + 1))
                    reconfigure_point_2(num, pnt)
                else:
                    thepnt.winfo_children()[-2].configure(text="-")
                    thepnt.winfo_children()[-3].configure(state="disabled")
                    thepnt.winfo_children()[-1].configure(state="disabled")

            if not len(points):
                warning = "Предупреждение: Необходимо задать как минимум одну точку\n"
                compilation_info.insert(index, warning)
                warning_count += 1
                index += len(warning)
                write_loop_info(index)
                check_warnings(warning_count)
                return []
            for i in range(len(points)):
                children = points[i].winfo_children()
                try:
                    x = float(children[1].get())
                    y = float(children[2].get())
                    pts.append([x, y, 0])
                except Exception as e:
                    print(e)
                    warning = f"Ошибка: Координаты точки N {i + 1} заданы некорректно\n"
                    compilation_info.insert(index, warning)
                    warning_count += 1
                    index += len(warning)
                    compilation_info.configure(state="disabled")
                    write_loop_info(index)
                    check_warnings(warning_count)
                    return []
            contour_usage = [False for ctr in range(len(lps))]
            intercrosses = [False for fl in range(len(lps))]
            for i in range(cur_loop):
                children = lps[i].winfo_children()
                new_loop = []
                ar = ars[i].get()
                if ar:
                    contour_usage[i] = True
                try:
                    lp = children[1].get().split(' ')
                    while '' in lp:
                        lp.remove('')
                    if len(lp):
                        lp[0] = int(lp[0]) - 1
                        new_loop.append(lp[0])

                    for j in range(1, len(lp)):
                        lp[j] = int(lp[j]) - 1
                        new_loop.append(lp[j])
                    if len(lp):
                        new_loop.append(lp[0])
                    try:
                        stp = getdouble(spin22.get())
                    except Exception as e:
                        print(e)
                        warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                        compilation_info.insert(index, warning)
                        warning_count += 1
                        index += len(warning)
                        compilation_info.configure(state="disabled")
                        write_loop_info(index)
                        check_warnings(warning_count)
                        return []
                    for pnt in range(len(pts)):
                        for pl in range(1, len(new_loop)):
                            if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                                if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                    new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                    intercrosses[i] = True
                                    break
                    ls.append(new_loop)

                    are_areas.append(ar)
                except Exception as e:
                    print(e)
                    warning = f"Ошибка: Индексы вершин внешнего контура области N {i + 1} заданы некорректно\n"
                    compilation_info.insert(index, warning)
                    warning_count += 1
                    index += len(warning)
                    compilation_info.configure(state="disabled")
                    write_loop_info(index)
                    check_warnings(warning_count)
                    return []
                inclusions.append([])
                embedings.append([[], []])

            new_loop = []
            inclusion = []
            ar = loop_is_ar.get()
            if ar:
                contour_usage[cur_loop] = True
            try:
                lp = copy.copy(loop_conf)
                if len(lp):
                    lp[0] = int(lp[0]) - 1
                    new_loop.append(lp[0])

                for j in range(1, len(lp)):
                    lp[j] = int(lp[j]) - 1
                    new_loop.append(lp[j])

                if len(lp):
                    new_loop.append(lp[0])
                try:
                    stp = getdouble(spin22.get())
                except Exception as e:
                    print(e)
                    warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                    compilation_info.insert(index, warning)
                    warning_count += 1
                    index += len(warning)
                    compilation_info.configure(state="disabled")
                    write_loop_info(index)
                    check_warnings(warning_count)
                    return []
                for pnt in range(len(pts)):
                    for pl in range(1, len(new_loop)):
                        if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                            if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                if pnt in new_loop[:-1]:
                                    warning = f"Предупреждение: Точка N {pnt + 1} повторно включается в контур N {cur_loop + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                                new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                intercrosses[cur_loop] = True
                                break
                ls.append(new_loop)

                are_areas.append(ar)
            except Exception as e:
                print(e)
                warning = f"Ошибка: Индексы вершин внешнего контура области N {cur_loop + 1} заданы некорректно\n"
                compilation_info.insert(index, warning)
                warning_count += 1
                index += len(warning)
                compilation_info.configure(state="disabled")
                write_loop_info(index)
                check_warnings(warning_count)
                return []
            inclusions.append([])
            embedings.append([[], []])

            for i in range(cur_loop + 1, len(lps)):
                children = lps[i].winfo_children()
                new_loop = []
                inclusion = []
                ar = ars[i].get()
                if ar:
                    contour_usage[i] = True
                try:
                    lp = children[1].get().split(' ')
                    while '' in lp:
                        lp.remove('')
                    if len(lp):
                        lp[0] = int(lp[0]) - 1
                        new_loop.append(lp[0])

                    for j in range(1, len(lp)):
                        lp[j] = int(lp[j]) - 1
                        new_loop.append(lp[j])
                    if len(lp):
                        new_loop.append(lp[0])
                    try:
                        stp = getdouble(spin22.get())
                    except Exception as e:
                        print(e)
                        warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                        compilation_info.insert(index, warning)
                        warning_count += 1
                        index += len(warning)
                        compilation_info.configure(state="disabled")
                        write_loop_info(index)
                        check_warnings(warning_count)
                        return []
                    for pnt in range(len(pts)):
                        for pl in range(1, len(new_loop)):
                            if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                                if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                    new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                    intercrosses[i] = True
                                    break
                    ls.append(new_loop)

                    are_areas.append(ar)
                except Exception as e:
                    print(e)
                    warning = f"Ошибка: Индексы вершин внешнего контура области N {i + 1} заданы некорректно\n"
                    compilation_info.insert(index, warning)
                    index += len(warning)
                    compilation_info.configure(state="disabled")
                    write_loop_info(index)
                    check_warnings(warning_count)
                    return []
                inclusions.append([])
                embedings.append([[], []])


            cntr1 = cur_loop
            for cntr2 in range(len(ls)):
                if cntr1 == cntr2:
                    cntr = ls[cntr1]
                    if len(get_loops_intersections(pts, cntr, cntr, 0)[0]):
                        warning = f"Предупреждение: Контур N {cntr1 + 1} имеет пересекающиеся отрезки\n"
                        compilation_info.insert(index,
                                                warning)
                        index += len(warning)
                        warning_count += 1
                        intercrosses[cntr1] = True
                else:
                    inter_data = get_loops_intersections(pts, ls[cntr1], ls[cntr2], 0)
                    if len(inter_data[0]):
                        warning = f"Предупреждение: Контур N {cntr1 + 1} и контур N {cntr2 + 1} имеют пересекающиеся отрезки\n"
                        compilation_info.insert(index,
                                                warning)
                        index += len(warning)
                        warning_count += 1
                    else:
                        isar1 = ars[cntr1].get()
                        isar2 = ars[cntr2].get()
                        in_pts_12 = loop_points_in_loop(pts, ls[cntr1], ls[cntr2], 0)
                        in_12_fact = len(in_pts_12) + len(inter_data[2]) == len(ls[cntr1]) - 1
                        in_pts_21 = loop_points_in_loop(pts, ls[cntr2], ls[cntr1], 0)
                        in_21_fact = len(in_pts_21) + len(inter_data[2]) == len(ls[cntr2]) - 1
                        in_12_incl = False
                        in_21_incl = False
                        for incl in inclusions[cntr2]:
                            inter_perm = get_loops_intersections(pts, ls[cntr1], ls[incl], 0)
                            in_pts_i_12 = loop_points_in_loop(pts, ls[cntr1], ls[incl], 0)
                            in_12_i_fact = len(in_pts_i_12) + len(inter_perm[2]) == len(ls[cntr1]) - 1
                            if in_12_i_fact:
                                in_12_incl = True
                                break
                        for incl in inclusions[cntr1]:
                            inter_perm = get_loops_intersections(pts, ls[cntr2], ls[incl], 0)
                            in_pts_i_21 = loop_points_in_loop(pts, ls[cntr2], ls[incl], 0)
                            in_21_i_fact = len(in_pts_i_21) + len(inter_perm[2]) == len(ls[cntr2]) - 1
                            if in_21_i_fact:
                                in_21_incl = True
                                break
                        in_12_mid = loop_middle_points_in_loop(pts, ls[cntr1], ls[cntr2], 0)
                        in_21_mid = loop_middle_points_in_loop(pts, ls[cntr2], ls[cntr1], 0)
                        if isar1 and isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and cntr1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1)
                                contour_usage[cntr1] = True
                            elif in_21_fact and not in_21_incl and not in_21_mid and cntr2 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2)
                                contour_usage[cntr2] = True
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    warning = f"Предупреждение: Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    warning = f"Предупреждение: Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                        elif isar1 or isar2:
                            if in_12_fact and not in_12_incl and not in_12_mid and isar2 and cntr1 not in inclusions[cntr2]:
                                inclusions[cntr2].append(cntr1)
                                contour_usage[cntr1] = True
                            elif in_21_fact and not in_21_incl and not in_21_mid and isar1 and cntr2 not in inclusions[cntr1]:
                                inclusions[cntr1].append(cntr2)
                                contour_usage[cntr2] = True
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    warning = f"Предупреждение: Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    warning = f"Предупреждение: Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                            if isar2 and in_12_fact and len(demi_barrier_points):
                                warning = f"Предупреждение: Контур N {cntr1 + 1} имеет общие стороны с контуром N {cntr2 + 1}, будучи пустым и включённым в него\n"
                                compilation_info.insert(index,
                                                        warning)
                                index += len(warning)
                                warning_count += 1
                            elif isar1 and in_21_fact and len(demi_barrier_points):
                                warning = f"Предупреждение: Контур N {cntr2 + 1} имеет общие стороны с контуром N {cntr1 + 1}, будучи пустым и включённым в него\n"
                                compilation_info.insert(index,
                                                        warning)
                                index += len(warning)
                                warning_count += 1
                        else:
                            demi_barrier_points = []
                            for dbs in inter_data[1]:
                                for dbp in dbs:
                                    if dbp not in demi_barrier_points:
                                        demi_barrier_points.append(dbp)
                            for in_pt1 in in_pts_12:
                                if in_pt1 not in demi_barrier_points and not in_12_fact:
                                    warning = f"Предупреждение: Контур N {cntr1 + 1} пересекает контур N {cntr2 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
                            for in_pt2 in in_pts_21:
                                if in_pt2 not in demi_barrier_points and not in_21_fact:
                                    warning = f"Предупреждение: Контур N {cntr2 + 1} пересекает контур N {cntr1 + 1}\n"
                                    compilation_info.insert(index,
                                                            warning)
                                    index += len(warning)
                                    warning_count += 1
            theincls = inclusions[cntr1]
            for cntr2 in range(cntr1):
                sideincl = inclusions[cntr2]
                for inc in theincls:
                    if cntr1 + 1 in sideincl and inc in sideincl:
                        sideincl.remove(inc)
            try:
                eps2 = getdouble(spin32.get())
            except Exception as e:
                print(e)
                warning = f"Ошибка: Неверно задан формат минимального порога площади контура\n"
                compilation_info.insert(index, warning)
                warning_count += 1
                index += len(warning)
                compilation_info.configure(state="disabled")
                write_loop_info(index)
                check_warnings(warning_count)
                return []
            if not check_area(pts, ls[cur_loop], 0, eps2) and not intercrosses[cur_loop]:
                warning = f"Предупреждение: Площадь контура N {cur_loop + 1} меньше допустимого значения\n"
                compilation_info.insert(index,
                                        warning)
                index += len(warning)
                warning_count += 1
            for lp in range(len(ls)):
                new_loop = [[], []]


                for j in range(len(ls[lp])):
                    new_loop[0].append(pts[ls[lp][j]][0])
                    new_loop[1].append(pts[ls[lp][j]][1])
                    pts[ls[lp][j]][2] = 1
                preview_data.append(new_loop)

            for chk in range(len(ls)):
                if not contour_usage[chk]:
                    warning = f"Лёгкое предупреждение: Контур N {chk + 1} не используется при построении\n"
                    compilation_info.insert(index,
                                            warning)
                    index += len(warning)

            for i in range(cur_loop):
                children = lps[i].winfo_children()
                new_loop = []
                isar = ars[i].get()
                is_included = False
                for inc in inclusions:
                    if i in inc:
                        is_included = True
                if not is_included and isar:
                    lp = children[1].get().split(' ')
                    while '' in lp:
                        lp.remove('')
                    for plp in range(len(lp)):
                        lp[plp] = int(lp[plp]) - 1
                        new_loop.append(lp[plp])
                    if len(lp):
                        new_loop.append(lp[0])
                    try:
                        stp = getdouble(spin22.get())
                    except Exception as e:
                        print(e)
                        warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                        compilation_info.insert(index, warning)
                        warning_count += 1
                        index += len(warning)
                        compilation_info.configure(state="disabled")
                        write_loop_info(index)
                        check_warnings(warning_count)
                        return []
                    for pnt in range(len(pts)):
                        for pl in range(1, len(new_loop)):
                            if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                                if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                    new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                    break
                    for j in range(1, len(new_loop)):
                        new_line = [new_loop[j - 1], new_loop[j]]
                        if new_line in extrn:
                            extrn.remove(new_line)
                            intrn.append(new_line)
                        elif [new_line[1], new_line[0]] in extrn:
                            extrn.remove([new_line[1], new_line[0]])
                            intrn.append(new_line)
                        elif new_line not in intrn and [new_line[1], new_line[0]] not in intrn:
                            extrn.append(new_line)

            new_loop = []
            isar = loop_is_ar.get()
            is_included = False
            for inc in inclusions:
                if cur_loop in inc:
                    is_included = True
            if not is_included and isar or is_included and not isar:
                lp = copy.copy(loop_conf)
                for plp in range(len(lp)):
                    lp[plp] = int(lp[plp]) - 1
                    new_loop.append(lp[plp])
                if len(lp):
                    new_loop.append(lp[0])
                try:
                    stp = getdouble(spin22.get())
                except Exception as e:
                    print(e)
                    warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                    compilation_info.insert(index, warning)
                    warning_count += 1
                    index += len(warning)
                    compilation_info.configure(state="disabled")
                    write_loop_info(index)
                    check_warnings(warning_count)
                    return []
                for pnt in range(len(pts)):
                    for pl in range(1, len(new_loop)):
                        if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                            if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                break
                for j in range(1, len(new_loop)):
                    new_line = [new_loop[j - 1], new_loop[j]]
                    if new_line in extrn:
                        extrn.remove(new_line)
                        intrn.append(new_line)
                    elif [new_line[1], new_line[0]] in extrn:
                        extrn.remove([new_line[1], new_line[0]])
                        intrn.append(new_line)
                    elif new_line not in intrn and [new_line[1], new_line[0]] not in intrn:
                        extrn.append(new_line)

            for i in range(cur_loop + 1, len(lps)):
                children = lps[i].winfo_children()
                new_loop = []
                isar = ars[i].get()
                is_included = False
                for inc in inclusions:
                    if i in inc:
                        is_included = True
                if not is_included and isar:
                    lp = children[1].get().split(' ')
                    while '' in lp:
                        lp.remove('')
                    for plp in range(len(lp)):
                        lp[plp] = int(lp[plp]) - 1
                        new_loop.append(lp[plp])
                    if len(lp):
                        new_loop.append(lp[0])
                    try:
                        stp = getdouble(spin22.get())
                    except Exception as e:
                        print(e)
                        warning = f"Ошибка: Неверно задан формат погрешности попадания точки в отрезок\n"
                        compilation_info.insert(index, warning)
                        warning_count += 1
                        index += len(warning)
                        compilation_info.configure(state="disabled")
                        write_loop_info(index)
                        check_warnings(warning_count)
                        return []
                    for pnt in range(len(pts)):
                        for pl in range(1, len(new_loop)):
                            if pnt != new_loop[pl] and pnt != new_loop[pl - 1]:
                                if is_in_side(pts, pnt, new_loop[pl - 1], new_loop[pl], stp):
                                    new_loop = new_loop[:pl] + [pnt] + new_loop[pl:]
                                    break
                    for j in range(1, len(new_loop)):
                        new_line = [new_loop[j - 1], new_loop[j]]
                        if new_line in extrn:
                            extrn.remove(new_line)
                            intrn.append(new_line)
                        elif [new_line[1], new_line[0]] in extrn:
                            extrn.remove([new_line[1], new_line[0]])
                            intrn.append(new_line)
                        elif new_line not in intrn and [new_line[1], new_line[0]] not in intrn:
                            extrn.append(new_line)

            external_lines = []
            for ex in extrn:
                external_lines.append([[pts[ex[0]][0], pts[ex[1]][0]], [pts[ex[0]][1], pts[ex[1]][1]]])

            for p in range(len(pts)):
                if not pts[p][2]:
                    for lpp in range(len(ls)):
                        a = ars[lpp].get()
                        if is_in_loop(pts, p, ls[lpp], 0) and a:
                            is_internal = True
                            for lppp in inclusions[lpp]:
                                if is_in_loop(pts, p, ls[lppp], 0):
                                    is_internal = False
                            if is_internal:
                                embedings[lpp][0].append(pts[p][0])
                                embedings[lpp][1].append(pts[p][1])
                                pts[p][2] = 1
                                break
            for p in range(len(pts)):
                if not pts[p][2]:
                    extra_pts[0].append(pts[p][0])
                    extra_pts[1].append(pts[p][1])
            compilation_info.configure(state="disabled")
            write_loop_info(index)
            check_warnings(warning_count)
            return [preview_data, extra_pts, external_lines, inclusions, are_areas, embedings]

        def loops_preview_2():
            check = get_view_data_2()
            if len(check):
                labels = []
                colors = []
                area_list = []
                ax.clear()
                n = 1
                for pr in range(len(check[0])):
                    if check[4][pr]:
                        pl = ax.plot(check[0][pr][0], check[0][pr][1], marker='o')
                        colors.append(pl[0].get_color())
                        labels.append(f"Область N {n}, Контур N {pr + 1}")
                        area_list.append(n - 1)
                        n += 1
                        if show_coords_2.get():
                            for i in range(len(check[0][pr][0])):
                                ax.annotate(f'({check[0][pr][0][i]}; {check[0][pr][1][i]})',
                                            (check[0][pr][0][i], check[0][pr][1][i]),
                                            textcoords="offset points", xytext=(0, 1), ha='center')
                if len(check[1][0]):
                    labels.append("Невошедшие точки")
                    ax.scatter(check[1][0], check[1][1], color="k")
                    if show_coords_2.get():
                        for i in range(len(check[1][0])):
                            ax.annotate(f'({check[1][0][i]}; {check[1][1][i]})', (check[1][0][i], check[1][1][i]),
                                        textcoords="offset points", xytext=(0, 1), ha='center')
                m = 0
                for pr in range(len(check[0])):
                    if not check[4][pr]:
                        add_unused = True
                        for pr2 in check[3]:
                            if pr in pr2:
                                add_unused = False
                                break
                        if add_unused:
                            m += 1
                            labels.append(F"Неиспользуемый контур N {m}({pr + 1})")
                            ax.plot(check[0][pr][0], check[0][pr][1], marker='*', linestyle=":")
                            if show_coords_2.get():
                                for i in range(len(check[0][pr][0])):
                                    ax.annotate(f'({check[0][pr][0][i]}; {check[0][pr][1][i]})',
                                                (check[0][pr][0][i], check[0][pr][1][i]),
                                                textcoords="offset points", xytext=(0, 1), ha='center')

                if len(check[2]):
                    labels.append("Внешний контур")
                    for ln in check[2]:
                        ax.plot(ln[0], ln[1], marker='x', linestyle="-.", color="k")
                n = 0
                clrs = []
                for prp in range(len(check[0])):
                    if check[4][prp]:
                        clrs.append(colors[n])
                        n += 1
                    else:
                        clrs.append("w")
                for pr in range(len(check[0])):
                    if check[4][pr]:
                        plt.fill(check[0][pr][0], check[0][pr][1], alpha=0.2, color=clrs[pr])
                        for loop_ind in check[3][pr]:
                            plt.fill(check[0][loop_ind][0], check[0][loop_ind][1], color="w")
                            plt.fill(check[0][loop_ind][0], check[0][loop_ind][1], alpha=0.2, color=clrs[loop_ind])
                            if not check[4][loop_ind]:
                                plt.plot(check[0][loop_ind][0], check[0][loop_ind][1], marker='o', color=clrs[loop_ind])
                        plt.scatter(check[5][pr][0], check[5][pr][1], marker='o', color=clrs[pr])
                        if show_coords.get():
                            for i in range(len(check[5][pr][0])):
                                plt.annotate(f'({check[5][pr][0][i]}; {check[5][pr][1][i]})',
                                             (check[5][pr][0][i], check[5][pr][1][i]), textcoords="offset points",
                                             xytext=(0, 1), ha='center')
                if len(check[1][0]):
                    ax.scatter(check[1][0], check[1][1], color="k")
                if len(check[2]):
                    for ln in check[2]:
                        ax.plot(ln[0], ln[1], marker='x', linestyle="-.", color="k")
                ax.legend(labels, loc="upper right")
                ax.grid()
                cnvs.draw()

        def resize_frame_3(event):
            # Растягиваем frame на всю площадь canvas
            canvas3.itemconfig(frame_id_3, width=event.width)
            table3.update_idletasks()
            canvas3.configure(scrollregion=canvas3.bbox("all"))

        def sort_points_by_i():
            point_set.sort(key= lambda x: x.winfo_children()[0].cget("text"))
            reconfigure_table3()

        def sort_points_by_x():
            point_set.sort(key= lambda x: float(x.winfo_children()[1].get()))
            reconfigure_table3()

        def sort_points_by_y():
            point_set.sort(key= lambda x: float(x.winfo_children()[2].get()))
            reconfigure_table3()

        def get_order(point):
            cnst = point.winfo_children()[-2].cget("text")
            if cnst.isdigit():
                return int(cnst)
            else:
                return float("inf")

        def sort_points_by_order():
            point_set.sort(key= lambda x: get_order(x))
            reconfigure_table3()

        def close_edit():
            print("Closing edit window")
            window2.destroy()

        def finish_edit():
            global lps
            global ars
            new_data = [[], []]
            for pt in loop_conf:
                new_data[0].append(str(pt))
            the_loop = lps[cur_loop].winfo_children()
            the_loop[1].delete(0, END)
            the_loop[1].insert(0, ' '.join(new_data[0]))
            if ars[cur_loop].get() != loop_is_ar.get():
                ars[cur_loop].set(loop_is_ar.get())
                isar_changed(cur_loop)
            close_edit()

        def rewrite_width_3(width):
            sort_by_n.configure(width=width)
            for pt in point_set:
                chld = pt.winfo_children()
                chld[0].configure(width=width)
            table3.update_idletasks()

        def point_changed(pt):
            if point_inclusion[pt].get():
                loop_conf.append(pt + 1)
            else:
                loop_conf.remove(pt + 1)
            loops_preview_2()

        def reconfigure_table3():
            for p in point_set:
                p.pack_forget()
                p.pack(expand=1, fill='x')
            table3.update_idletasks()
            canvas3.configure(scrollregion=canvas3.bbox("all"))

        def fast_add_point_2():
            point = Frame(table3, padx=2)
            chld = points[len(point_set)].winfo_children()
            chld2 = lps[cur_loop].winfo_children()
            lbl = Label(point, text=str(len(point_set) + 1), font=(main_font, 10), relief='solid', borderwidth=3)
            lbl.pack(side='left')
            spin1 = Entry(point)
            spin1.pack(side='left', expand=1, fill='x')
            spin1.insert(1, chld[1].get())
            spin1.configure(state="disabled")
            spin2 = Entry(point)
            spin2.pack(side='left', expand=1, fill='x')
            spin2.insert(1, chld[2].get())
            spin2.configure(state="disabled")
            check_incl = BooleanVar(value=(str(len(point_set) + 1) in chld2[1].get()))
            point_inclusion.append(check_incl)
            constant_chk_1 = len(point_set)
            pt_incl_chk = Checkbutton(point, variable=check_incl, command= lambda : point_changed(constant_chk_1), width=2)
            pt_incl_chk.pack(side="left")
            point_forward = Button(point, text="\u2190")
            point_forward.pack(side="left")
            lbl = Label(point, text="-", font=(main_font, 10), relief="sunken")
            lbl.pack(side="left")
            point_backward = Button(point, text="\u2192")
            point_backward.pack(side="left")
            point.pack(expand=1, fill='x')
            table3.update_idletasks()
            point_set.append(point)
            canvas3.configure(scrollregion=canvas3.bbox("all"))

        def rewrite_width_31(width):
            sort_by_order.configure(width=(width + 5))
            for pt in point_set:
                chld = pt.winfo_children()
                chld[-2].configure(width=width)
            table3.update_idletasks()

        def include_all():
            for i in range(len(point_inclusion)):
                if not point_inclusion[i].get():
                    point_inclusion[i].set(True)
                    loop_conf.append(i + 1)
            loops_preview_2()

        def remove_all():
            for i in range(len(point_inclusion)):
                if point_inclusion[i].get():
                    point_inclusion[i].set(False)
                    loop_conf.remove(i + 1)
            loops_preview_2()

        print("Start forming edit window")
        window2 = Toplevel(window)
        window2.title(f"Сборка контура N {cur_loop + 1}")
        window2.geometry('1350x840')

        lp_info = lps[cur_loop].winfo_children()
        point_set = []
        point_inclusion = []
        loop_is_ar = BooleanVar(value=ars[cur_loop].get())
        loop_conf = lp_info[1].get().split(' ')
        while '' in loop_conf:
            loop_conf.remove('')
        for lpi in range(len(loop_conf)):
            loop_conf[lpi] = int(loop_conf[lpi])

        outfrm21 = Frame(window2, background='darkgrey', relief="sunken", padx=5, border=3)
        outfrm21.pack(expand=1, fill='both', side='left')
        dtfrm21 = Frame(outfrm21, background='darkgrey', padx=5, border=3)
        dtfrm21.pack(fill='x')
        lbl = Label(dtfrm21, text="Имеющиеся точки", font=(main_font, 10), relief='solid', borderwidth=3)
        lbl.pack(fill='x')
        BindToolTip(lbl, "Набор точек, формирующих контуры.", 180, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        dtfrm22 = Frame(outfrm21, background='darkgrey', padx=5, border=3)
        dtfrm22.pack(fill='x')
        sort_by_n = Button(dtfrm22, text="N", font=(main_font, 10), relief='solid', borderwidth=3, command=sort_points_by_i)
        sort_by_n.pack(side="left")
        BindToolTip(sort_by_n, "Глобальный номер точки.\n(Нажмите для сортировки по нему)", 0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        sort_by_x = Button(dtfrm22, text="X", font=(main_font, 10), relief='solid', borderwidth=3, command=sort_points_by_x)
        sort_by_x.pack(side="left", fill='x', expand=1)
        BindToolTip(sort_by_x, "Координата точки по оси X.\n(Нажмите для сортировки по ней)", 0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        sort_by_y = Button(dtfrm22, text="Y", font=(main_font, 10), relief='solid', borderwidth=3, command=sort_points_by_y)
        sort_by_y.pack(side="left", fill='x', expand=1)
        BindToolTip(sort_by_y, "Координата точки по оси Y.\n(Нажмите для сортировки по ней)", 0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        filler = Frame(dtfrm22)
        filler.pack(side="left", fill='x')
        BindToolTip(filler, "Нажмите на чекбокс рядом с точкой,\nчтобы включить её в контур.\n(Точка добавляется в конец набора)\nДля добавления всех точек в текущий контур нажмите на галочку,\nа для удаления всех точек из него - на крестик.", 0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        fill_all = Button(filler, text="✓", font=(main_font, 10), relief='solid', borderwidth=3, command=include_all, width=1)
        fill_all.pack(side="left")
        rem_all = Button(filler, text="✗", font=(main_font, 10), relief='solid', borderwidth=3, command=remove_all, width=1)
        rem_all.pack(side="left")
        sort_by_order = Button(dtfrm22, text="Индекс", font=(main_font, 10), relief='solid', borderwidth=3,
                               command=sort_points_by_order)
        sort_by_order.pack(side="left", fill='x')
        BindToolTip(sort_by_order,
                    "Положение точки в текущем контуре.\n(Нажмите на эту надпись для сортировки по нему)\nДля перемещения точки 'назад' или 'вперёд'\nпо контуру нажмите на кнопку со стрелкой\nслева или справа от индекса соответственно.",
                    0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        dtfrm31 = Frame(outfrm21, background='darkgrey', padx=5, border=3)
        dtfrm31.pack(expand=1, fill='both')
        canvas3 = Canvas(dtfrm31)

        table3 = Frame(canvas3)
        scrollbar3 = Scrollbar(window2, orient="vertical", command=canvas3.yview)
        canvas3.configure(yscrollcommand=scrollbar3.set)

        canvas3.pack(fill="both", expand=1, side="left")
        scrollbar3.pack(side="left", fill="y")
        canvas3.bind('<Configure>', resize_frame_3)
        frame_id_3 = canvas3.create_window((0, 0), window=table3, anchor="n")
        table3.update_idletasks()
        canvas3.configure(scrollregion=canvas3.bbox("all"))
        table3.columnconfigure(1, weight=1, minsize=75)
        table3.columnconfigure(2, weight=1, minsize=75)

        extrafrm14 = Frame(window2, background='darkgrey', relief="sunken", padx=5, border=3)
        extrafrm14.pack(expand=1, fill='both')
        lbl = Label(extrafrm14, text="График контуров и областей", font=(main_font, 10), relief='solid',
                    borderwidth=3)
        lbl.pack(fill='x')
        BindToolTip(lbl,
                    "Схематический график сформированных областей.\n(Обновляется при каждом действии)",
                    205, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        figure = plt.Figure(figsize=(5, 5))
        ax = figure.add_subplot(111)
        cnvs = FigureCanvasTkAgg(figure, extrafrm14)
        cnvs.get_tk_widget().pack(fill="both", expand=1)

        outfrm32 = Frame(window2)
        outfrm32.pack(expand=1, fill='both', side='left')
        extrafrm02 = Frame(outfrm32, background='darkgrey', relief="sunken", padx=5, border=3)
        extrafrm02.pack(expand=1, fill='both')
        compilation_info = ScrolledText(extrafrm02, height=8, state='disabled')
        compilation_info.pack(fill=BOTH, expand=1)
        BindToolTip(extrafrm02,
                    "Информация о состоянии контура.\n(Обновляется при каждом действии)",
                    0, -29,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        extrafrm12 = Frame(outfrm32, background='darkgrey', relief="sunken", padx=5, border=3)
        extrafrm12.pack(expand=1, fill='both')
        is_ar = Frame(extrafrm12, background="darkgrey")
        is_ar.pack(fill='x')
        lbl = Label(is_ar, text=f"Контур N {cur_loop + 1} задаёт область", font=(main_font, 10), relief='solid', borderwidth=3)
        lbl.pack(side="left")
        BindToolTip(lbl,
                    "При включённой галочке в данном контуре будет\nпроходить построение сетки.",
                    0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        is_area = Checkbutton(is_ar, relief="sunken", borderwidth=3, variable=loop_is_ar, command=loops_preview_2)
        is_area.pack(side="right")
        eps_set2 = Frame(extrafrm12, background="darkgrey")
        eps_set2.pack(fill='x')
        lbl = Label(eps_set2, text="Погрешность попадания точки на отрезок:", font=(main_font, 10), relief='solid',
                    borderwidth=3)
        lbl.pack(side="left")
        BindToolTip(lbl, "Погрешность, с которой будет определяться, попадает ли точка на отрезки.\n(Принимаются числа в целочисленном формате,\nчисла с плавающей точкой и\nв экспоненциальном формате)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        spin22 = StringVar(value="1e-15")
        spin22w = Entry(eps_set2, width=23, textvariable=spin22)
        spin22w.pack(pady=5, side=RIGHT)
        eps2_set2 = Frame(extrafrm12, background="darkgrey")
        eps2_set2.pack(fill='x')

        lbl = Label(eps2_set2, text="Нижний порог площади контура:", font=(main_font, 10), relief='solid',
                    borderwidth=3)
        lbl.pack(side="left")
        BindToolTip(lbl, "Минимальное значение, которое может принять площадь контура.\n(Принимаются числа в целочисленном формате,\nчисла с плавающей точкой и\nв экспоненциальном формате)", 0, 23,
                    ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        spin32 = StringVar(value="1e-15")
        spin32w = Entry(eps2_set2, width=23, textvariable=spin32)
        spin32w.pack(pady=5, side=RIGHT)
        shw_crds_2 = Frame(extrafrm12, background="darkgrey")
        shw_crds_2.pack(fill='x')
        lbl = Label(shw_crds_2, text="Отображать координаты точек", font=(main_font, 10), relief='solid', borderwidth=3)
        lbl.pack(side="left")
        BindToolTip(lbl, "При включённой галочке при построении графика областей будут отображаться координаты точек.",
                    0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
        show_coords_2 = BooleanVar(value=True)
        sh_crd_chk_2 = Checkbutton(shw_crds_2, variable=show_coords_2, relief="sunken", borderwidth=3, command=loops_preview_2)
        sh_crd_chk_2.pack(side="right")
        dopfrm = Frame(extrafrm12, background='darkgrey', pady=3)
        dopfrm.pack(fill='x', side="bottom")
        exit_btn = Button(dopfrm, text="Отмена", command=close_edit)
        exit_btn.pack(pady=3, padx=3, side=RIGHT)
        finish_btn = Button(dopfrm, text="Сохранить", command=finish_edit)
        finish_btn.pack(pady=3, padx=3, side=RIGHT)


        for pnt in range(len(points)):
            fast_add_point_2()
        rewrite_width_3(len(str(len(point_set) + 1)))
        rewrite_width_31(len(str(len(point_set) + 1)))
        loops_preview_2()
        print("Edit window formed succsessfully")
        window2.grab_set()

    def on_closing():
        print("Saving tables' data")
        fast_save()
        print("Closing main window")
        plt.close("all")
        window.destroy()

    def preload():
        try:
            with open("last_save.json", "r") as svfl:
                sav_dat = json.load(svfl)
            for pt in sav_dat["points"]:
                fast_add_point(pt[0], pt[1], pt[2])
            for lp in sav_dat["loops"]:
                fast_add_loop(lp[0], lp[1], lp[2])
            msh_gen = sav_dat["mesh_generation"]
            filename.delete(0, END)
            filename.insert(0, msh_gen["file_name"])
            drp.set(msh_gen["algo"])
            spin0.delete(0, END)
            spin0.insert(0, msh_gen["density"])
            spin2w.delete(0, END)
            spin2w.insert(0, msh_gen["eps_cont"])
            spin3w.delete(0, END)
            spin3w.insert(0, msh_gen["eps_area"])
            show_coords.set(msh_gen["show_coords"])
            do_check.set(msh_gen["do_check"])
            inp_dat = sav_dat["input_data"]
            filename2.delete(0, END)
            filename2.insert(0, inp_dat["file_name"])
            ent1.delete(1.0, END)
            ent1.insert(1.0, inp_dat["nodes"])
            entlc.delete(1.0, END)
            entlc.insert(1.0, inp_dat["lcs"])
            ent2.delete(1.0, END)
            ent2.insert(1.0, inp_dat["lines"])
            ent3.delete(1.0, END)
            ent3.insert(1.0, inp_dat["border"])
            ent4.delete(1.0, END)
            ent4.insert(1.0, inp_dat["contoures"])
            ent5.delete(1.0, END)
            ent5.insert(1.0, inp_dat["areas"])
            entmat.delete(1.0, END)
            entmat.insert(1.0, inp_dat["materials"])
            ent6.delete(1.0, END)
            ent6.insert(1.0, inp_dat["embed_nodes"])
        except Exception as e:
            print(e)
            with open("last_save.json", "w") as jsfile:
                data = {"points": [], "loops":[],
                        "mesh_generation": {
                            "file_name": "test.msh",
                            "algo": "Frontal-Delaunay",
                            "density": "0",
                            "eps_cont": "1e-15",
                            "eps_area": "1e-15",
                            "show_coords": True,
                            "do_check": False
                        },
                        "input_data": {
                            "file_name": "",
                            "nodes": "",
                            "lcs": "",
                            "lines": "",
                            "border": "",
                            "contoures": "",
                            "areas": "",
                            "materials": "",
                            "embed_nodes": ""
                        }
                        }
                json.dump(data, jsfile)
            messagebox.showerror("Ошибка", "Не удалось восстановить таблицы из файла last_save.json")
            return 1

    def fast_save():
        data = {"points": [], "loops": [],
                        "mesh_generation": {
                            "file_name": filename.get(),
                            "algo": drp.get(),
                            "density": spin0.get(),
                            "eps_cont": spin2w.get(),
                            "eps_area": spin3w.get(),
                            "show_coords": show_coords.get(),
                            "do_check": do_check.get()
                        },
                        "input_data": {
                            "file_name": filename2.get(),
                            "nodes": ent1.get(1.0, END),
                            "lcs": entlc.get(1.0, END),
                            "lines": ent2.get(1.0, END),
                            "border": ent3.get(1.0, END),
                            "contoures": ent4.get(1.0, END),
                            "areas": ent5.get(1.0, END),
                            "materials": entmat.get(1.0, END),
                            "embed_nodes": ent6.get(1.0, END)
                        }}
        for pt in points:
            pt_info = pt.winfo_children()
            point_data = [pt_info[1].get(), pt_info[2].get(), pt_info[3].get()]
            data["points"].append(point_data)
        for lp in range(len(lps)):
            lp_info = lps[lp].winfo_children()
            loop_data = [lp_info[1].get(), ars[lp].get(), lp_info[3].get()]
            data["loops"].append(loop_data)
        with open("last_save.json", "w") as wrfl:
            json.dump(data, wrfl)

    def backward_loading():
        global lps
        data = get_data()
        if data:
            while len(points):
                remove_point(0)
            for pt in range(len(data["nodes"])):
                fast_add_point(str(data["nodes"][pt][0]), str(data["nodes"][pt][1]), str(data["lcs"][pt]))
            while len(lps):
                remove_loop(0)
            for lp in data["contoures"]:
                loop_points = []
                for lpt in lp:
                    if lpt > 0:
                        side = data["lines"][lpt - 1]
                        if side[0] not in loop_points:
                            loop_points.append(side[0])
                        if side[1] not in loop_points:
                            loop_points.append(side[1])
                    else:
                        side = data["lines"][-lpt - 1]
                        if side[1] not in loop_points:
                            loop_points.append(side[1])
                        if side[0] not in loop_points:
                            loop_points.append(side[0])
                for i in range(len(loop_points)):
                    loop_points[i] = str(loop_points[i])
                new_lp = ' '.join(loop_points)
                fast_add_loop(new_lp, False)
            for ar in range(len(data["areas"])):
                are = data["areas"][ar]
                ars[are[0] - 1].set(True)
                for a in range(1, len(are)):
                    are[a] = str(are[a])
                table2.winfo_children()[are[0] - 1].winfo_children()[3].configure(state="normal")
                table2.winfo_children()[are[0] - 1].winfo_children()[3].delete(0, END)
                table2.winfo_children()[are[0] - 1].winfo_children()[3].insert(0, str(data["materials"][ar]))
                table2.winfo_children()[are[0] - 1].winfo_children()[3].configure(state="readonly")

    def get_msh_data(msh):
        gmsh.initialize()

        gmsh.open(msh)

        nodes = gmsh.model.mesh.getNodes(-1, -1)
        new_nodes = []
        for i in range(len(nodes[0])):
            new_nodes.append(' '.join([str(i + 1) + ":", str(nodes[1][i * 3]), str(nodes[1][i * 3 + 1])]))

        phys_groups = gmsh.model.getPhysicalGroups(2)
        new_elements = {}
        for group in phys_groups:
            name = gmsh.model.getPhysicalName(2, group[1])
            surfs = gmsh.model.getEntitiesForPhysicalGroup(2, group[1])
            for sf in surfs:
                new_elements[sf] = {"material": name, "elements": []}
                triangles = gmsh.model.mesh.getElements(2, sf)[1][0]
                for i in triangles:
                    elem = gmsh.model.mesh.getElement(i)
                    new_elem = ' '.join([str(i) + ":", str(elem[1][0]), str(elem[1][1]), str(elem[1][2])])
                    new_elements[sf]["elements"].append(new_elem)

        borders = gmsh.model.mesh.getElements(1, -1)
        new_borders = {}
        if 1 in borders[0]:
            lines = borders[1][0]
            for i in lines:
                line = gmsh.model.mesh.getElement(i)
                new_line = [str(line[1][0]), str(line[1][1])]
                if line[3] in new_borders.keys():
                    if new_line[0] not in new_borders[line[3]]:
                        new_borders[line[3]].append(new_line[0])
                    if new_line[1] not in new_borders[line[3]]:
                        new_borders[line[3]].append(new_line[1])
                else:
                    new_borders[line[3]] = new_line

            for ky in new_borders.keys():
                new_borders[ky] = ' '.join(new_borders[ky])

        gmsh.finalize()
        return {"nodes": new_nodes, "borders": new_borders, "surfaces": new_elements}

    def update_short_info(msh):
        if not len(msh):
            text_data = ""
        else:
            try:
                msh_data = get_msh_data(msh)
                elem_qunt = 0
                mat_list = []
                for surf in msh_data["surfaces"].keys():
                    elem_qunt += len(msh_data["surfaces"][surf]["elements"])
                    if msh_data["surfaces"][surf]["material"] not in mat_list:
                        mat_list.append(msh_data["surfaces"][surf]["material"])
                text_data = f"Число узлов: {len(msh_data["nodes"])}\nЧисло отрезков внешней границы: {len(msh_data["borders"])}\nЧисло элементов: {elem_qunt}\nЧисло областей: {len(msh_data["surfaces"])}\nЧисло материалов: {len(mat_list)}"
            except:
                text_data = f"Не удалось получить сводку файла {msh}"
        short_info.configure(state="normal")
        short_info.delete(1.0, END)
        short_info.insert(1.0, text_data)
        short_info.configure(state="disabled")

    def get_msh_info():
        name = filename.get()
        if not name:
            gmsh.finalize()
            messagebox.showwarning("Предупреждение", "Пустое имя файла")
            return 1
        if name[-4:] != ".msh":
            name += ".msh"
        try:
            data = get_msh_data(name)
            text = "Набор узлов:\n"
            for nd in data["nodes"]:
                text += nd + "\n"
            text += "Набор внешних границ:\n"
            for ky in data["borders"].keys():
                text += f"{str(ky)}: {data["borders"][ky]}\n"
            text += "Набор поверхностей:\n"
            for surf in data["surfaces"].keys():
                text += f"Область №{surf}\nМатериал: {data["surfaces"][surf]["material"]}\n"
                for elm in data["surfaces"][surf]["elements"]:
                    text += elm + "\n"
            print("Start forming info window")
            window3 = Toplevel(window)
            window3.title(f"Информация о файле {name}")
            window3.geometry('1350x840')
            info = ScrolledText(window3)
            info.pack(fill=BOTH, expand=True)
            info.insert(1.0, text)
            info.configure(state='disabled')
        except Exception as e:
            print(e)
            messagebox.showerror("Ошибка", "Не удалось открыть указанный файл")
            return 1
        return 0

    print("Start forming window")
    window = Tk()
    window.title("Программа генерации сеток для МКЭ")
    window.geometry('1620x700')

    tab_control = ttk.Notebook(window)
    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab4 = ttk.Frame(tab_control)
    tab_control.add(tab1, text='Построение сетки')
    tab_control.add(tab2, text='Входные данные')
    tab_control.add(tab4, text='Справка')
    tab_control.pack(expand=1, fill='both')

    print("Start forming tab1")
    prfrm = Frame(tab1)
    prfrm.pack(expand=1, fill='both')
    points = []
    lps = []
    ars = []
    outfrm1 = Frame(prfrm, background='darkgrey', relief="sunken", padx=5, border=3)
    outfrm1.pack(expand=1, fill='both', side='left')
    dtfrm = Frame(outfrm1, background='darkgrey', padx=5, border=3)
    dtfrm.pack(fill='x')
    lbl = Label(dtfrm, text="Стартовый набор точек", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(expand=1, fill='x')
    BindToolTip(lbl, "Набор точек, необходимых для построения сетки.", 160, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    dtfrm1 = Frame(outfrm1, background='darkgrey', padx=5, border=3)
    dtfrm1.pack(fill='x')
    lbl_n1 = Label(dtfrm1, text="N", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_n1.pack(side="left")
    BindToolTip(lbl_n1, "Глобальный номер точки.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl = Label(dtfrm1, text="X", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(side="left", fill='x', expand=1)
    BindToolTip(lbl, "Координаты точек по оси X.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl = Label(dtfrm1, text="Y", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(side="left", fill='x', expand=1)
    BindToolTip(lbl, "Координаты точек по оси Y.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl = Label(dtfrm1, text="Lc", font=(main_font, 10), relief='solid', width=10, borderwidth=3)
    lbl.pack(side="left")
    BindToolTip(lbl,
                "Шаг, с которым рёбра контуров будут разбиты на отрезки.\n(Например, при шаге 0.1 ребро длинной 1 будет разбито на 10 отрезков.\nПринимаются числа в целочисленном формате,\nчисла с плавающей точкой и в экспоненциальном формате)\nПри нажатии на стрелочку вверх/вниз\n соответствующее число увеличится/уменьшится на 0.001.",
                0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    add_btn = Button(dtfrm1, text="+", command=fast_add_point)
    add_btn.pack(side="left")
    BindToolTip(add_btn, "Добавить точку.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    dtfrm2 = Frame(outfrm1, background='darkgrey', padx=5, border=3)
    dtfrm2.pack(expand=1, fill='both')
    canvas1 = Canvas(dtfrm2)

    table1 = Frame(canvas1)
    scrollbar1 = Scrollbar(prfrm, orient="vertical", command=canvas1.yview)
    canvas1.configure(yscrollcommand=scrollbar1.set)

    canvas1.pack(fill="both", expand=1, side="left")
    scrollbar1.pack(side="left", fill="y")
    canvas1.bind('<Configure>', resize_frame_1)
    frame_id_1 = canvas1.create_window((0, 0), window=table1, anchor="n")
    table1.update_idletasks()
    canvas1.configure(scrollregion=canvas1.bbox("all"))
    table1.columnconfigure(1, weight=1, minsize=75)
    table1.columnconfigure(2, weight=1, minsize=75)

    outfrm2 = Frame(prfrm, background='darkgrey', relief="sunken", padx=5, border=3)
    outfrm2.pack(expand=1, fill='both', side='left')
    dtfrm = Frame(outfrm2, background='darkgrey', padx=5, border=3)
    dtfrm.pack(fill='x')
    lbl = Label(dtfrm, text="Набор замкнутых контуров", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(expand=1, fill='x')
    BindToolTip(lbl, "Набор геометрических контуров, формирующих области построения сетки.", 40, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    dtfrm3 = Frame(outfrm2, background='darkgrey', padx=5, border=3)
    dtfrm3.pack(fill='x')
    lbl_n2 = Label(dtfrm3, text="N", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_n2.pack(side="left")
    BindToolTip(lbl_n2, "Глобальный номер контура", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl_t_1 = Label(dtfrm3, text="  Точки контура   ", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_t_1.pack(side="left", fill='x', expand=1)
    BindToolTip(lbl_t_1, "Глобальные индексы точек, формирующих контур.\n(Порядок индексов влияет на форму контура)\nНабор задаётся последовательностью целых чисел,\nразделённых пробелом (Например, 1 2 3...)'", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl_t_2 = Label(dtfrm3, text=" * ", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_t_2.pack(side="left")
    BindToolTip(lbl_t_2, "Задание контуром области.\n(При включённой галочке в\nконтуре будет формироваться сетка)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl_t_3 = Label(dtfrm3, text="Включаемые контуры", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_t_3.pack(side="left", fill='x', expand=1)
    BindToolTip(lbl_t_3, "Глобальные индексы контуров, включаемых в текущий.\n(Сетка, которая будет построена в текущем\nконтуре, будет обтекать эти контуры)\nНабор задаётся последовательностью целых чисел,\nразделённых пробелом (Например, 1 2 3...)'", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    lbl_t_4 = Label(dtfrm3, text="M", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl_t_4.pack(side="left")
    BindToolTip(lbl_t_4, "Номер материала области.\n(Для изменения номера на +1/-1\nнажмите стрелочку вверх/вниз возле номера)", 0,
                23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    add_btn = Button(dtfrm3, text="+", command=fast_add_loop, width=10)
    add_btn.pack(side="left")
    BindToolTip(add_btn, "Добавить контур", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    dtfrm4 = Frame(outfrm2, background='darkgrey', padx=5, border=3)
    dtfrm4.pack(expand=1, fill='both')
    canvas2 = Canvas(dtfrm4)

    table2 = Frame(canvas2)
    scrollbar2 = Scrollbar(prfrm, orient="vertical", command=canvas2.yview)
    canvas2.configure(yscrollcommand=scrollbar2.set)
    canvas2.pack(fill="both", expand=1, side="left")
    scrollbar2.pack(side="left", fill="y")
    canvas2.bind('<Configure>', resize_frame_2)
    frame_id_2 = canvas2.create_window((0, 0), window=table2, anchor="n")
    table2.update_idletasks()
    canvas2.configure(scrollregion=canvas2.bbox("all"))
    table2.columnconfigure(1, weight=1, minsize=75)
    table2.columnconfigure(1, weight=1, minsize=75)
    table2.columnconfigure(3, weight=1, minsize=75)


    outfrm = Frame(prfrm)
    outfrm.pack(expand=1, fill='y')

    frm = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, pady=5, border=3)
    frm.pack(expand=1, fill='both')
    lbl = Label(frm, text="Файл сохранения сетки", font=(main_font, 13), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl, "Имя файла/путь к файлу, в который будет сохранена построенная сетка.\n(Принимаются файлы формата MSH.\nДля создания нового файла просто введите его имя.\nНовый файл появится в той же папке, что и программа)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    filename = Entry(frm, width=70)
    filename.pack(pady=3, padx=3, side=LEFT)
    filename.insert(0, "test.msh")
    btn = Button(frm, text="Обзор...", command=choose_file)
    btn.pack(pady=3, padx=3, side=RIGHT)
    BindToolTip(btn, "Выбрать файл среди существующих на компьютере.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    extrafrm00 = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, border=3)
    extrafrm00.pack(expand=1, fill='both')
    short_info = ScrolledText(extrafrm00, height=5, width=50, state='disabled')
    short_info.pack(fill="x")
    BindToolTip(extrafrm00,
                "Основная информация о сетке из файла.\n(Обновляется при изменении имени файла\nи после построения сетки)",
                0, -29,
                ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    prfrm = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, pady=5, border=3)
    prfrm.pack(expand=1, fill='both')
    lbl = Label(prfrm, text="Параметры построения сетки", font=(main_font, 13), relief='solid', borderwidth=3)
    lbl.pack(pady=4)
    frm = Frame(prfrm, background='darkgrey')
    frm.pack(expand=1, fill='x')
    lbl = Label(frm, text="Алгоритм построения сетки:", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "Алгоритм, который будет использоваться программой для построения сетки на основе входных данных.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    drp = Combobox(frm, values=algos, width=23, state='readonly')
    drp.set("Frontal-Delaunay")
    drp.pack(pady=5, side=RIGHT)
    frm = Frame(prfrm, background='darkgrey')
    frm.pack(expand=1, fill='x')
    lbl = Label(frm, text="Степень сгущения(вложенности) сетки:", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "Сколько раз полученная сетка будет подроблена.\n(Принимаются числа в целочисленном формате)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    spin0 = Spinbox(frm, from_=0, to=10, width=23, increment=1)
    spin0.pack(pady=5, side=RIGHT)
    eps_set = Frame(prfrm, background="darkgrey")
    eps_set.pack(expand=1, fill='x')
    lbl = Label(eps_set, text="Погрешность попадания точки на отрезок:", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "Погрешность, с которой будет определяться, попадает ли точка на отрезки.\n(Принимаются числа в целочисленном формате,\nчисла с плавающей точкой и\nв экспоненциальном формате)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    spin2 = StringVar(value="1e-15")
    spin2w = Entry(eps_set, width=23, textvariable=spin2)
    spin2w.pack(pady=5, side=RIGHT)
    eps2_set = Frame(prfrm, background="darkgrey")
    eps2_set.pack(expand=1, fill='x')
    lbl = Label(eps2_set, text="Нижний порог площади контура:", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "Минимальное значение, которое может принять площадь контура.\n(Принимаются числа в целочисленном формате,\nчисла с плавающей точкой и\nв экспоненциальном формате)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    spin3 = StringVar(value="1e-15")
    spin3w = Entry(eps2_set, width=23, textvariable=spin3)
    spin3w.pack(pady=5, side=RIGHT)
    shw_crds = Frame(prfrm, background="darkgrey")
    shw_crds.pack(expand=1,fill='x')
    lbl = Label(shw_crds, text="Отображать координаты точек", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "При включённой галочке при построении графика областей будут отображаться координаты точек.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    show_coords = BooleanVar(value=True)
    sh_crd_chk = Checkbutton(shw_crds, variable=show_coords, relief="sunken", borderwidth=3)
    sh_crd_chk.pack(pady=5, side=RIGHT)
    do_chk = Frame(prfrm, background="darkgrey")
    do_chk.pack(expand=1, fill='x')
    lbl = Label(do_chk, text="Проводить проверку согласованности", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3, side=LEFT)
    BindToolTip(lbl, "При включённой галочке после генерации сетки будет проведена проверка на согласованность.\n(Эта процедура может занять время на сетках с большим числом элементов)", 0,
                23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    do_check = BooleanVar(value=False)
    do_check_chk = Checkbutton(do_chk, variable=do_check, relief="sunken", borderwidth=3)
    do_check_chk.pack(pady=5, side=RIGHT)

    frm = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, pady=5, border=3)
    frm.pack(expand=1, fill='both')
    preview_btn = Button(frm, text="Построить график контуров", command=loops_preview)
    preview_btn.pack(pady=3)
    BindToolTip(preview_btn, "Вывести схематическое изображение областей.", 0,23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    insert_btn = Button(frm, text="Сформировать входные данные", command=transfer_data)
    insert_btn.pack(pady=3)
    BindToolTip(insert_btn, "Перенести данные из таблиц во вкладку 'Входные данные'.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    back_btn = Button(frm, text="Извлечь входные данные", command=backward_loading)
    back_btn.pack(pady=3)
    BindToolTip(back_btn, "Перенести данные из вкладки 'Входные данные' в таблицы.", 0, 23, ("tahoma", "8", "normal"),
                SOLID, "#e0e0e0")
    btn = Button(frm, text="Запустить построение сетки", command=generate_mesh)
    btn.pack(pady=3)
    BindToolTip(btn, "Построить сетку на основе данных во вкладке 'Входные данные'.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    inst_btn = Button(frm, text="Сформировать входные данные\nи построить сетку", command=transfer_and_generate)
    inst_btn.pack(pady=3)
    BindToolTip(inst_btn, "Перенести данные из таблиц во вкладку 'Входные данные'\nи построить на их основе сетку.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    mshbtn = Button(frm, text="Получить информацию о файле", command=get_msh_info)
    mshbtn.pack(pady=3)
    BindToolTip(mshbtn, "Получить расширенную информацию о файле, указанном в блоке 'Файл сохранения сетки'.", 0, 23,
                ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    gmshbtn = Button(frm, text="Открыть файл в Gmsh", command=open_gmsh)
    gmshbtn.pack(pady=3)
    BindToolTip(gmshbtn, "Открыть файл сетки, указанный в блоке 'Файл сохранения сетки'.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    accepted_materials = False
    print("Tab1 formed\nStart forming tab2")

    outfrm = Frame(tab2)
    outfrm.pack(expand=1, fill='both')

    dtfrm = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, pady=5, border=3)
    dtfrm.pack()
    lbl = Label(dtfrm, text="Сохранение и загрузка входных данных", font=(main_font, 13), relief='solid', borderwidth=3)
    lbl.pack(pady=5)
    lbl = Label(dtfrm, text="Файл сохранения данных", font=("Arial Bold", 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl, "Имя файла/путь к файлу, в который будет сохранены входные данные.\n(Принимаются файлы формата JSON.\nДля создания нового файла просто введите его имя.\nНовый файл появится в той же папке, что и программа)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    filename2 = Entry(dtfrm, width=50)
    filename2.pack(pady=3)
    btn = Button(dtfrm, text="Обзор...", command=choose_file2)
    btn.pack(pady=3)
    BindToolTip(btn, "Выбрать файл среди существующих на компьютере.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    btn = Button(dtfrm, text="Сохранить данные", command=save_data)
    btn.pack(pady=3)
    BindToolTip(btn, "Сохранить входные данные в файл, указанный в поле ввода.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    btn = Button(dtfrm, text="Загрузить данные", command=load_data)
    btn.pack(pady=3)
    BindToolTip(btn, "Выбрать файл среди существующих на компьютере и ввести его данные в поля.", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")

    dtfrm1 = Frame(outfrm, background='darkgrey', relief="sunken", padx=5, pady=5, border=3)
    dtfrm1.pack(expand=1, fill='both')
    lbl = Label(dtfrm1, text="Редактирование входных данных", font=(main_font, 13), relief='solid', borderwidth=3)
    lbl.pack(pady=5)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Координаты заданных узлов", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl, "Набор координат узлов, необходимых для построения сетки.\n(Точки задаются парами чисел с плавающей точкой, например:\n1.0 1.0 \n0.32 0.21\n...)", 0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent1 = ScrolledText(frm, width=10)
    ent1.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Значения Lc", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                "Значения параметра Lc для каждой точки.\n(Значения задаются набором чисел с плавающей точкой, например:\n0.1\n0.2\n...)\nПервое значение назначается первой точке, второе - второй и т.д.",
                0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    entlc = ScrolledText(frm, width=10)
    entlc.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Индексы концов заданных рёбер", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                  "Набор отрезков(рёбер), необходимых для построения сетки.\n(Рёбра задаются парами индексов точек (их порядковых номеров, начиная с 1), например:\n1 2 \n3 2\n...)",
                  0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent2 = ScrolledText(frm, width=10)
    ent2.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Индексы рёбер внешней границы", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                  "Набор рёбер, являющихся внешними границами областей.\n(Т.е. набор индексов соответствующих рёбер, например:\n1 2 3...)",
                  0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent3 = ScrolledText(frm, width=10)
    ent3.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Индексы рёбер заданных контуров", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                  "Наборы индексов рёбер, формирующих контуры.\n(Контуры задаются строчками с наборами целых чисел, например:\n1 2 3 \n3 4 5\n...)\nПри этом необходимо, чтобы вторая вершина каждого ребра соответствовала\nпервой вершине следующего.\nАналогично для последнего и первого рёбер.\nЕсли слева к индексу ребра приписать '-', то оно будет считаться 'повёрнутым'\n(То есть ребро 1 2 будет считаться как 2 1)",
                  0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent4 = ScrolledText(frm, width=10)
    ent4.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Индексы контуров заданных областей", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                  "Наборы индексов контуров, формирующих области.\n(Области задаются строчками с наборами индексов контуров, например:\n1 2 \n2\n...)\nПервый индекс обозначает контур, являющийся внешней границей области.\nОстальные включаются в эту область и считаются отверстиями в ней.",
                  0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent5 = ScrolledText(frm, width=10)
    ent5.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Номера материалов", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                "Значения номера материала каждой области.\n(Значения задаются набором целых чисел от 1 до n,\nгде n - число областей, например:\n1\n2\n...)\nПервое значение назначается первой области, второе - второй и т.д.",
                0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    entmat = ScrolledText(frm, width=14)
    entmat.pack(fill=BOTH, expand=True, padx=3)

    frm = Frame(dtfrm1, background='darkgrey')
    frm.pack(side=LEFT, expand=1, fill='both')
    lbl = Label(frm, text="Индексы дополнительных узлов областей", font=(main_font, 10), relief='solid', borderwidth=3)
    lbl.pack(pady=3)
    BindToolTip(lbl,
                  "Наборы индексов точек, включаемых в области и не используемых при задании их границ.\n(Каждый набор обозначается двумя строками.\nВ первой задаётся индекс области, а во второй - наобор индексов точек, например:\n1 \n2 3\n4\n6 7 8 9...\nЗадание подобного набора не является обязательным.)",
                  0, 23, ("tahoma", "8", "normal"), SOLID, "#e0e0e0")
    ent6 = ScrolledText(frm, width=10)
    ent6.pack(fill=BOTH, expand=True, padx=3)

    print("Tab2 formed\nStart forming tab3")

    info = ScrolledText(tab4)
    info.pack(fill=BOTH, expand=True)
    try:
        with open("readme.txt", 'r', encoding='utf-8') as rdmf:
            info.insert(1.0, rdmf.read())
    except Exception as e:
        print(e)
        info.insert(1.0, "Не удалось открыть файл readme.txt")
    info.configure(state='disabled')

    print("Tab3 formed\nWindow formed successfully")
    preload()
    window.protocol("WM_DELETE_WINDOW", on_closing)
    update_short_info(filename.get())
    window.mainloop()
except Exception as e:
    print(e)
    input("Press enter to exit...")
    try:
        fast_save()
    except:
        pass