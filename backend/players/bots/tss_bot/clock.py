from time import time

import numba as nb


@nb.njit("f8()")
def ctime():

    with nb.objmode(t="f8"):
        t = time()

    return t
