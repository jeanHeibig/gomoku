# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Remove unnecessary bitboard recomputation inside negamax
- Use Transposition tables (with board symmetries and? ply number -of search- as depth?) and add PV-search (sort with best move -iterative deepening- at given ply number)
- Use History Killer Moves
- add an opening book
- bot needs to do a faster search
- improve bot speed/performance
- Improve search engine
- current bot is dumb at tactics -> implement TSS (threat-space search)
- current eval function is biased towards X (O missing one move during the eval)
- improve bot time management
- Add SQLite to saves games (with moves) and players (with ELO)
- Editor mode : at the end, only accept valid board configurations
- JS -> only toggle classes / CSS -> everything visual
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- watch bot vs bot on gui
- Prevent player from moving out-of-turn -> login system...
- Handle timeouts by the server
- Login page
- Manage matchmaking
- Deploy server online so players can connect via link to play against the bot
- solve the 8x8x5 and then go for 16x16x5 with 4 bitboards, then go for oo-te structure
