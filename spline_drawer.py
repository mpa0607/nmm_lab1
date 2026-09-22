import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import bisplrep, BSpline, CubicSpline

# Пример данных: координаты вершин треугольников и значения в узлах
triangle_vertices = np.array([
    [0, 0],
    [1, 0],
    [0, 1]
])
triangle_triangles = np.array([
    [0, 0, 1],
    [1, 0, 1],
    [0, 1, 1]
])
values = np.array([1, 2, 3])

# Построение сглаживающего сплайна
bspline = BSpline(triangle_vertices, triangle_triangles, values)  # n — количество узлов
cs = CubicSpline(triangle_vertices[:, 0], triangle_vertices[:, 1], values, bc_type='natural')

# Генерация точек для изолиний
xi = np.linspace(triangle_vertices[:, 0].min(), triangle_vertices[:, 0].max(), 100)
yi = np.linspace(triangle_vertices[:, 1].min(), triangle_vertices[:, 1].max(), 100)
X, Y = np.meshgrid(xi, yi)
Z = cs(X, Y)

# Построение графика
fig, ax = plt.subplots()
ax.triplot(triangle_vertices[:, 0], triangle_vertices[:, 1], triangle_triangles,
          linewidth=2, outline=True, label='Треугольники')
ax.contour(X, Y, Z, levels=[1, 2, 3], colors='red', linestyles='dashed', alpha=0.7, label='Изолинии сплайна')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.legend()
plt.title('Изолинии кубического сглаживающего сплайна на треугольниках')
plt.show()