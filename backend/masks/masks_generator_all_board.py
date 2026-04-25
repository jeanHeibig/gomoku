BOARD_SIZE = 8
ALIGN = 5


# TODO: merge those functions with those of masks_generator_by_cell
# TODO: And unify mask generation with other file
def idx(i: int, j: int) -> int:
    """Convert 2D coordinates (i, j) to a 1D index."""
    return i * BOARD_SIZE + j


def bit(i: int, j: int) -> int:
    """Get the bit mask for the cell at position (i, j)."""
    return 1 << idx(i, j)


def generate_masks():
    masks = []

    # horizontaux
    for i in range(BOARD_SIZE):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            m = 0
            for t in range(ALIGN):
                m |= bit(i, j0 + t)
            masks.append(m)

    # verticaux
    for j in range(BOARD_SIZE):
        for i0 in range(BOARD_SIZE - ALIGN + 1):
            m = 0
            for t in range(ALIGN):
                m |= bit(i0 + t, j)
            masks.append(m)

    # diagonales NO-SE
    for i0 in range(BOARD_SIZE - ALIGN + 1):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            m = 0
            for t in range(ALIGN):
                m |= bit(i0 + t, j0 + t)
            masks.append(m)

    # diagonales SO-NE
    for i0 in range(ALIGN - 1, BOARD_SIZE):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            m = 0
            for t in range(ALIGN):
                m |= bit(i0 - t, j0 + t)
            masks.append(m)

    return masks


def save_masks(masks):
    with open("precomputed_masks_all_board.py", "w", encoding="utf-8") as f:
        f.write("# Auto-generated file. Do not edit by hand.\n\n")
        f.write("WIN_MASKS_ALL_BOARD = [\n")
        for m in masks:
            f.write(f"    {m},\n")
        f.write("]\n")


if __name__ == "__main__":
    all_masks = generate_masks()
    print("Nombre de masques:", len(all_masks))  # must be 96
    save_masks(all_masks)
