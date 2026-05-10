# gomoku

Gomoku server, GUI and AI engine

# TODO

## Frontend / GUI

Add:
Threat visuals (check / checkmate)
Eval bar
Favicon
Escape key go back to default view
Mouse scroll to go through preview
Build a complete logger of all the info possible during search and follow it "by hand" (with eventually fast forward button)
GUI book builder
Improve editor mode:
Validate final board legality before starting
Reject impossible positions
Watch bot vs bot games directly in GUI

## Backend / Bot Engine

### Architecture

Review codebase:
remove obsolete code/TODOs
add docstrings
add type annotations
add numba input/output types
Isolate bot logic into a single-file student-friendly version
keep optional extensions/modular advanced engine
Create a Memory / transposition helper class
Improve score representation:
nonnegative compact scores (uint8)
compact fast evals (int8 / int16)

### Search Improvements

Improve move ordering:
sort all moves, not only hash move
add History Heuristic / Killer Moves
Improve PVS:
multi-PV support
better principal variation propagation
Improve time management
Improve raw search speed/performance
Fix tactical weaknesses:
implement proper Threat-Space Search (TSS)
faster double-threat detection with LUTs
Mate faster:
prefer shortest winning lines

### Dynamic Depth / Entropy Search

Make search depth adaptive:
attacking side searches narrower
defending side searches wider
Explore entropy-based depth reduction:
forced moves do not decrease depth
depth reduction depends on effective branching factor
if move is forcing threat, reduce depth (not only child)
weight moves by seriousness instead of raw move count

### Evaluation Function

Improve evaluation quality
Investigate hybrid evaluation:
lightweight heuristic eval in opening
stronger tactical/Monte-Carlo eval in complex positions
Build the TSS tree during eval
x/o asymmetry -> always finish on o
Implement dead/effectively-dead cell analysis:
detect geometrically dead regions
detect strategically dead regions
identify disconnected independent regions
Detect drawish/tablebase-like positions with many dead cells

### Symmetry / Opening Work

Improve symmetry handling:
LUT-based transforms
dead symmetry propagation from root
Create self-play opening book

## Server / Online / Matchmaking

Add SQLite persistence:
saved games
move history
players
ELO ratings
Add ELO system:
tournaments
imposed openings
optional handicaps
Handle timeouts server-side
Prevent out-of-turn play
Add authentication/login system
Add matchmaking
Switch online play to websockets
Allow online bot tournaments:
secure bot submission
server-side verification/sandboxing
Deploy public server for online play against bots and humans

## Long-Term Goals

Solve 8x8x5 Gomoku
Explore larger variants:
16x16x5
multi-bitboard representations
infinite/abstract board structures
