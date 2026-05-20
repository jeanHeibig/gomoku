def remaining_lines_for_attacker(bb_attacker, bb_defender):
    # all WMA masks not touching defender
    ...


def cell_alignment_sets(lines):
    # A[cell] = bitset of remaining line indices containing cell
    ...


def maximal_cells(A, bb_open):
    # keep only cells whose A[cell] is not strictly contained in another A[d]
    ...


def greedy_pair_certificate(lines, bb_open):
    # try to find disjoint pairs whose common lines cover all lines
    ...
