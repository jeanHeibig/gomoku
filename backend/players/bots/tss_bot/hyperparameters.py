import numpy as np


U64 = np.uint64


# --- HYPERPARAMETERS ---
CACHE = False
# K = 64  # Auto-prune after K moves
TT_BITS = 24  # >= 24


# --- HYPERVARIABLES --- (do not edit)
TT_SIZE = U64(1) << U64(TT_BITS)
TT_MASK = TT_SIZE - U64(1)
