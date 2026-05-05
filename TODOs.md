# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs, add docstrings and type annotations
- isolate bot code, so that it is inside a single file (mandatory for students), manage extensions
- improve score management (score should be nonnegative and fit in uint8)
- improve fast_eval management (mc eval ? eval should fit in int8?16?)
- Remove unnecessary bitboard recomputation inside negamax ?
- Improve board symmetries
- add an opening book (here symmetries are very important !)
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
