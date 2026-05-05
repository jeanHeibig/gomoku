import time

from numba import njit, objmode


@njit
def ctime():
    with objmode(t="float64"):
        t = time.time()
    return t
