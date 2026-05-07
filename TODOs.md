# gomoku
Gomoku Server and AI training

# TODO

-D5E4E5D4C5+move 12 -> X cant win anymore, can they ? If X can't win anymore, then the strat is a win for O (draw counted as a win here !)

- Review code and inline TODOs, add docstrings and type annotations
- isolate bot code, so that it is inside a single file (mandatory for students), manage extensions
- create a Memory class for our bot
- Make K ply dependent
- could improve a lot the double threat search with LUT. THe number of threat/double threat cases is actually quite limited
- just realized some cells are not dead as it would be possible to win there, however they are "effectively dead", as it would be impossible to force a winning threat there !! example game to be found... :
..o..x..
..x.o...
..oox...
.xoooox.
..oxxxoo
xoxxxox.
...ox...
...ox...
-> o could potentially win bottom right, however, due to dead adjacent cells, it is actually impossible for o to have a double threat there !
-> a line is depth-0-alive if geometrically possible; depth-(k+1) alive if there exists a move creating a depth-k unavoidable threat. -> many heuristic evaluators fail because they count shapes, but ignore whetherr the shapes can interact  -> you can solve independently disconnected regions !
- the pvs search could be done the following way: when you "check" (direct threat), the depth is not decremented, idem when you defend the threat -> forced moves shoud be treated in this kind of way. You could also decrement depth by the log of number of legal moves as stated (not the number of "LEGAL" Moves, but weigth the number of moves according to their "seriousness" -> entropy)
- improve score management (score should be nonnegative and fit in uint8)
- improve fast_eval management (mc eval ? eval should fit in int8?16?) -> maybe we could use this fast eval for positions at the beginning (seems good enough) but then at deeper depths, when the game has, say>16 or whatsoever stones played, then use a +1/0/-1 eval from mc_bot ?
- find a way to table base draws (position with lots of dead cells...)
- Improve board symmetries (eg, only look for center pieces first, add dead cells -> we already compute them actually) add LUT rather than loops. Still not convinced by symmetries during search... For opening, symmetries are great, but maybe we should keep them only at root. Symetries lost at root could be propagated so that there is no check for positions without available symmetries for their children
- Use History Killer Moves
- improve bot time management
- improve bot speed/performance
- current bot is dumb at tactics -> implement TSS (threat-space search)
- Add elo system based on tournament with imposed onenings (with or without handicap)
- Add SQLite to saves games (with moves) and players (with ELO)
- Editor mode : at the end, only accept valid board configurations
- JS -> only toggle classes / CSS -> everything visual
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- watch bot vs bot on gui
- add (keyboard) arrows that allow to move back and forth at the end
- add an eval bar
- Prevent player from moving out-of-turn -> login system...
- Handle timeouts by the server
- Login page
- Manage matchmaking
- Deploy server online so players can connect via link to play against the bot
- solve the 8x8x5 and then go for 16x16x5 with 4 bitboards, then go for oo-te structure
