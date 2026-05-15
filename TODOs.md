# TODO

## Bugs

## Frontend / GUI

--- HIGH PRIORITY ---

Replayer should toggle active player if game has ended
GUI book builder
Show all the moves from the PV

--- MEDIUM PRIORITY ---

's'? key switches side and continues a new game from current moveList (way to play bot vs bot)
Need to play bot vs bot and benchmark with elo
Find a way to stop the bot and have it play its current best move
Reject impossible positions from editor board
Logger

--- LOW PRIORITY ---

Eval bar
Escape key go back to default view
Watch bot vs bot games directly in GUI
Add preset boards in the GUI
Need more control for timer

## Backend / Bot Engine

### Architecture

--- HIGH PRIORITY ---

Review codebase: add docstrings, remove obsolete code, deal with inline TODOs
Put `bb_open` in sort moves via `tactics & bb_open`, rather than in the heuristics
Add quiescence / tactical extension

--- MEDIUM PRIORITY ---

Benchmark different Heuristic functions

--- LOW PRIORITY ---

Need to check alignment distribution in RG
When the position is drawn, find the "best" draw

### Search Improvements

--- HIGH PRIORITY ---

Mate solver
multi-PV support
Improve move ordering: add Killer Moves

--- MEDIUM PRIORITY ---

Improve time management
Fix tactical weaknesses: implement proper Threat-Space Search (TSS)

--- LOW PRIORITY ---

Create self-play opening book
Solve the handicap game

### Dynamic Depth / Entropy Search

--- HIGH PRIORITY ---

Move reduction with symmetry should be made once at root only for the current stage

--- MEDIUM PRIORITY ---

Root `find_best_move` should look for all moves in the opening book (for transpositions)
weight moves by seriousness instead of raw move count

--- LOW PRIORITY ---

...

### Evaluation Function

--- HIGH PRIORITY ---

TSS during quiescence
Detect draws with pairing moves to kill cells

--- MEDIUM PRIORITY ---

Alignment tablebase

--- LOW PRIORITY ---

Order MASKS_BY_CELL by hit probability (lazy evaluation)
Improve evaluation function

## Server / Online / Matchmaking

--- HIGH PRIORITY ---

Switch to websockets
Add SQLite: save games, players
Add authentication/login system
Add matchmaking
Prevent out-of-turn play

--- MEDIUM PRIORITY ---

Add ELO system: tournaments with imposed openings
Handle timeouts server-side
Deploy public server for online play against bots and humans

--- LOW PRIORITY ---

server-side verification

## Long-Term Goals

--- HIGH PRIORITY ---

Solve 8x8x5 Gomoku : use pairing moves.

--- MEDIUM PRIORITY ---

Explore larger variants: 16x16x5
multi-bitboard representations

--- LOW PRIORITY ---

infinite/abstract board structures
