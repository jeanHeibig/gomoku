"""
Module for generating precomputed winning masks for a Gomoku game.

This module provides functionality to generate bitmasks representing all possible
winning segments on an 8x8 game board where 5 pieces in a row constitute a win.
The masks are used for efficient bitboard-based game state evaluation.

Constants:
    BOARD_SIZE: The size of the square game board (8x8).
    ALIGN: The number of consecutive pieces required to win (5).

Functions:
    idx(i, j): Converts 2D coordinates to a 1D index.
    bit(i, j): Returns the bit mask for a specific cell.
    segment_mask(cells): Creates a bitmask from a list of cell coordinates.
    all_winning_segments(): Generates all possible winning line segments.
    build_masks_by_cell(): Maps each cell to its associated winning masks.
    python_literal_for_dict(d): Generates Python code for the masks dictionary.
    main(): Entry point to generate and save the precomputed masks.
"""

from pathlib import Path

BOARD_SIZE = 8
ALIGN = 5


def idx(i: int, j: int) -> int:
    """Convert 2D coordinates (i, j) to a 1D index."""
    return i * BOARD_SIZE + j


def bit(i: int, j: int) -> int:
    """Get the bit mask for the cell at position (i, j)."""
    return 1 << idx(i, j)


def segment_mask(cells: list[tuple[int, int]]) -> int:
    """Create a bitmask from a list of cell coordinates."""
    m = 0
    for i, j in cells:
        m |= bit(i, j)
    return m


def all_winning_segments() -> list[list[tuple[int, int]]]:
    """Generate all possible winning segments on the board."""
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
    """Build a dictionary mapping each cell index to its list of winning masks."""
    masks_by_cell: dict[int, list[int]] = {k: [] for k in range(BOARD_SIZE * BOARD_SIZE)}

    for cells in all_winning_segments():
        mask = segment_mask(cells)
        for i, j in cells:
            masks_by_cell[idx(i, j)].append(mask)

    return masks_by_cell


def python_literal_for_dict(d: dict[int, list[int]]) -> str:
    """Generate Python code representing the masks dictionary."""
    lines: list[str] = []
    lines.append("# Auto-generated file. Do not edit by hand.")
    lines.append("")
    lines.append("WIN_MASKS_BY_CELL = {")

    for k in range(BOARD_SIZE * BOARD_SIZE):
        masks = d[k]
        lines.append(f"    {k}: [")
        for m in masks:
            lines.append(f"        {m},")
        lines.append("    ],")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Generate and write the precomputed masks to a file."""
    d = build_masks_by_cell()
    content = python_literal_for_dict(d)

    out = Path("precomputed_masks_by_cell.py")
    out.write_text(content, encoding="utf-8")

    print(f"Fichier écrit : {out.resolve()}")
    print("Nombre total de masques gagnants :", len(all_winning_segments()))
    print("Exemple pour la case  0 :", d[0])
    print("Exemple pour la case 27 :", d[27])


if __name__ == "__main__":
    main()
