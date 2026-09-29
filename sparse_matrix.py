import copy
import math


class Matrix:
    """Симметричный портрет: di — диагональ, ggl/ggu — нижний/верхний треугольник, ig/jg — строки/столбцы."""

    def __init__(self, ig, jg, ggl, ggu, di):
        self.ig = copy.copy(ig)
        self.jg = copy.copy(jg)
        self.ggl = copy.copy(ggl)
        self.ggu = copy.copy(ggu)
        self.di = copy.copy(di)

    def get_elem(self, i, j):
        if i == j:
            return self.di[i]
        if i > j:
            for e in range(self.ig[i], self.ig[i + 1]):
                if self.jg[e] == j:
                    return self.ggl[e]
        else:
            for e in range(self.ig[j], self.ig[j + 1]):
                if self.jg[e] == i:
                    return self.ggu[e]
        return 0.0

    def add_to_elem(self, i, j, n):
        if n == 0:
            return 0
        if i == j:
            self.di[i] += n
            return 0
        if i > j:
            for e in range(self.ig[i], self.ig[i + 1]):
                if self.jg[e] == j:
                    self.ggl[e] += n
                    return 0
        else:
            for e in range(self.ig[j], self.ig[j + 1]):
                if self.jg[e] == i:
                    self.ggu[e] += n
                    return 0
        return 1

    def matrix_mult_vector(self, x, y, n):
        for i in range(n):
            y[i] = x[i] * self.di[i]
        for i in range(n):
            for e in range(self.ig[i], self.ig[i + 1]):
                col = self.jg[e]
                y[i] += self.ggl[e] * x[col]
                y[col] += self.ggu[e] * x[i]
        return 0

    @staticmethod
    def scalar_multiply(x, y, n):
        return sum(x[i] * y[i] for i in range(n))

    def msg(self, pr, x, max_k, mismax, dmsrf):
        """Метод сопряжённых градиентов для Ax = pr; x — начальное приближение, решение пишется в него."""
        n = len(pr)
        r = [0.0] * n
        z = [0.0] * n
        az = [0.0] * n
        ar = [0.0] * n
        norm_pr = self.scalar_multiply(pr, pr, n)
        if norm_pr < 1e-30:
            norm_pr = 1.0
        self.matrix_mult_vector(x, ar, n)
        for i in range(n):
            r[i] = pr[i] - ar[i]
            z[i] = r[i]
        r_norm = self.scalar_multiply(r, r, n)
        mism = math.sqrt(r_norm / norm_pr)
        k1 = 0
        for k in range(1, max_k + 1):
            print(f"Начало итерации {k}...")
            self.matrix_mult_vector(z, az, n)
            azz = self.scalar_multiply(az, z, n)
            if abs(azz) < 1e-30:
                print("Остановка MSG: (Az,z) ≈ 0")
                break
            a = r_norm / azz
            for i in range(n):
                x[i] += a * z[i]
                r[i] -= a * az[i]
            r_norm_new = self.scalar_multiply(r, r, n)
            b = 0.0 if abs(r_norm) < 1e-30 else r_norm_new / r_norm
            r_norm = r_norm_new
            for i in range(n):
                z[i] = r[i] + b * z[i]
            mism = math.sqrt(r_norm / norm_pr)
            k1 += 1
            if k1 % 10 == 0 and dmsrf:
                vec = [0.0] * n
                self.matrix_mult_vector(x, vec, n)
                for vc in range(n):
                    vec[vc] = pr[vc] - vec[vc]
                mism = math.sqrt(self.scalar_multiply(vec, vec, n) / norm_pr)
            print(f"Итерация {k} завершена\nНевязка: {mism}")
            if mism <= mismax:
                break
        print(f"Число итераций: {k1}; Невязка: {mism}")
