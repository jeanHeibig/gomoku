from pathlib import Path

BOARD_SIZE = 8
ALIGN = 5


def idx(i: int, j: int) -> int:
    return i * 8 + j


def bit(i: int, j: int) -> int:
    return 1 << idx(i, j)


def segment_mask(cells: list[tuple[int, int]]) -> int:
    m = 0
    for i, j in cells:
        m |= bit(i, j)
    return m


def all_winning_segments() -> list[list[tuple[int, int]]]:
    segments: list[list[tuple[int, int]]] = []

    # Horizontaux
    for i in range(BOARD_SIZE):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            cells = [(i, j0 + t) for t in range(ALIGN)]
            segments.append(cells)

    # Verticaux
    for j in range(BOARD_SIZE):
        for i0 in range(BOARD_SIZE - ALIGN + 1):
            cells = [(i0 + t, j) for t in range(ALIGN)]
            segments.append(cells)

    # Diagonales NO-SE
    for i0 in range(BOARD_SIZE - ALIGN + 1):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            cells = [(i0 + t, j0 + t) for t in range(ALIGN)]
            segments.append(cells)

    # Diagonales SO-NE
    for i0 in range(ALIGN - 1, BOARD_SIZE):
        for j0 in range(BOARD_SIZE - ALIGN + 1):
            cells = [(i0 - t, j0 + t) for t in range(ALIGN)]
            segments.append(cells)

    return segments


def build_masks_by_cell() -> dict[int, list[int]]:
    masks_by_cell: dict[int, list[int]] = {k: [] for k in range(64)}

    for cells in all_winning_segments():
        mask = segment_mask(cells)
        for i, j in cells:
            masks_by_cell[idx(i, j)].append(mask)

    return masks_by_cell


def python_literal_for_dict(d: dict[int, list[int]]) -> str:
    lines: list[str] = []
    lines.append("# Auto-generated file. Do not edit by hand.")
    lines.append("")
    lines.append("WIN_MASKS_BY_CELL = {")

    for k in range(64):
        masks = d[k]
        lines.append(f"    {k}: [")
        for m in masks:
            lines.append(f"        {m},")
        lines.append("    ],")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    d = build_masks_by_cell()
    content = python_literal_for_dict(d)

    out = Path("precomputed_masks.py")
    out.write_text(content, encoding="utf-8")

    print(f"Fichier écrit : {out.resolve()}")
    print("Nombre total de masques gagnants :", len(all_winning_segments()))
    print("Exemple pour la case  0 :", d[0])
    print("Exemple pour la case 27 :", d[27])


if __name__ == "__main__":
    main()
