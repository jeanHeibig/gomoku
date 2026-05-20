import numba as nb
import numpy as np

from self_play.canonicalization import BB, RawPosition


WIN_MASKS = np.array(
    [
        31,
        62,
        124,
        248,
        7936,
        15872,
        31744,
        63488,
        2031616,
        4063232,
        8126464,
        16252928,
        520093696,
        1040187392,
        2080374784,
        4160749568,
        133143986176,
        266287972352,
        532575944704,
        1065151889408,
        34084860461056,
        68169720922112,
        136339441844224,
        272678883688448,
        8725724278030336,
        17451448556060672,
        34902897112121344,
        69805794224242688,
        2233785415175766016,
        4467570830351532032,
        8935141660703064064,
        17870283321406128128,
        4311810305,
        1103823438080,
        282578800148480,
        72340172838010880,
        8623620610,
        2207646876160,
        565157600296960,
        144680345676021760,
        17247241220,
        4415293752320,
        1130315200593920,
        289360691352043520,
        34494482440,
        8830587504640,
        2260630401187840,
        578721382704087040,
        68988964880,
        17661175009280,
        4521260802375680,
        1157442765408174080,
        137977929760,
        35322350018560,
        9042521604751360,
        2314885530816348160,
        275955859520,
        70644700037120,
        18085043209502720,
        4629771061632696320,
        551911719040,
        141289400074240,
        36170086419005440,
        9259542123265392640,
        68853957121,
        137707914242,
        275415828484,
        550831656968,
        17626613022976,
        35253226045952,
        70506452091904,
        141012904183808,
        4512412933881856,
        9024825867763712,
        18049651735527424,
        36099303471054848,
        1155177711073755136,
        2310355422147510272,
        4620710844295020544,
        9241421688590041088,
        4328785936,
        8657571872,
        17315143744,
        34630287488,
        1108169199616,
        2216338399232,
        4432676798464,
        8865353596928,
        283691315101696,
        567382630203392,
        1134765260406784,
        2269530520813568,
        72624976666034176,
        145249953332068352,
        290499906664136704,
        580999813328273408
    ],
    dtype=BB,
)


@nb.njit("boolean(uint64)", inline="always")
def is_winning(bb_current: BB) -> bool:
    """Return whether the bitboard contains a 5-alignment."""

    for k in range(96):

        mask = WIN_MASKS[k]

        if (bb_current & mask) == mask:
            return True

    return False


@nb.njit("boolean(uint64, uint64)", inline="always")
def is_dead_draw(bb_current: BB, bb_opponent: BB) -> bool:
    """Return whether no player can still form a 5-alignment."""

    return (
        not is_winning(~bb_opponent)
        and
        not is_winning(~bb_current)
    )


def move_names_to_raw_position(move_names: list[str]) -> RawPosition:
    bb_current = BB(0)
    bb_opponent = BB(0)

    current_player = len(move_names) % 2
    for move_name in move_names:
        i = 8 - int(move_name[1])
        j = ord(move_name[0].lower()) - 97
        cell = 8 * i + j
        move = BB(1) << cell

        if current_player:
            bb_opponent |= move
        else:
            bb_current |= move

        current_player = 1 - current_player

    raw_position = RawPosition(bb_current, bb_opponent)
    return raw_position
