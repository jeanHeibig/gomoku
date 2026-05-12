import numpy as np


U64 = np.uint64


# --- HYPERPARAMETERS ---
TT_BITS = 20


# --- HYPERVARIABLES --- (do not edit)
TT_SIZE = U64(1) << U64(TT_BITS)
TT_MASK = TT_SIZE - U64(1)
