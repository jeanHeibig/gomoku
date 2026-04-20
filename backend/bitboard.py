from precomputed_masks import WIN_MASKS_BY_CELL

def has_five(bb: int, last_i: int, last_j: int) -> bool:
    k = last_i * 8 + last_j
    for mask in WIN_MASKS_BY_CELL[k]:
        if (bb & mask) == mask:
            return True
    return False

def set_bit(bb, i, j):
    return bb | (1 << (8*i + j))
