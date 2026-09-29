import math

_FUNCTIONS = {
    0: (lambda x, y: x + y, lambda x, y: 1.0, lambda x, y: 1.0),
    1: (lambda x, y: x ** 2 + y ** 2, lambda x, y: 2 * x, lambda x, y: 2 * y),
    2: (lambda x, y: x ** 3 + y ** 3, lambda x, y: 3 * x ** 2, lambda x, y: 3 * y ** 2),
    3: (lambda x, y: x ** 4 + y ** 4, lambda x, y: 4 * x ** 3, lambda x, y: 4 * y ** 3),
    4: (lambda x, y: math.sin(x) + math.sin(y), lambda x, y: math.cos(x), lambda x, y: math.cos(y)),
}
_ZERO = (lambda x, y: 0.0,) * 3


def u_func(f, x=0, y=0):
    return _FUNCTIONS.get(f, _ZERO)[0](x, y)


def du_dx_func(f, x=0, y=0):
    return _FUNCTIONS.get(f, _ZERO)[1](x, y)


def du_dy_func(f, x=0, y=0):
    return _FUNCTIONS.get(f, _ZERO)[2](x, y)
