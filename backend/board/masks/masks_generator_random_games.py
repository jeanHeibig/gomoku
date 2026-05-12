import numpy as np


N = 128

def make_random_u64(n, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    low = rng.integers(2**32, size=n, dtype=np.uint64)
    high = rng.integers(2**32, size=n, dtype=np.uint64)

    return (high << np.uint64(32)) | low


def count_bits(r):
    s = r & 1
    for _ in range(64):
        r >>= 1
        s += r & 1
    return s


if __name__ == "__main__":

    r = make_random_u64(N)
    c = count_bits(r.copy())
    m = c.mean()
    while not m == 32:
        r = make_random_u64(N)
        c = count_bits(r.copy())
        m = c.mean()


    s = "RANDOM_GAMES = [\n"
    for x in r:
        s += f"    {x},\n"
    s += "]\n"


    with open("long_stuff.py", "w") as f:
        f.write(s)
