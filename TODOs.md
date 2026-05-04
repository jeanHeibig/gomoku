# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- watch bot vs bot on gui
- bot needs to do a faster search
- sort with best move (iterative deepening) at given ply number
- current bot is dumb at tactics -> implement TSS (threat-space search)
- current eval function is biased towards X (O missing one move during the eval)
- Use PV-search
- Use Transposition tables
- Use board symmetries
- add an opening book
- Use History Killer Moves
- improve bot time management
- Add SQLite to saves games (with moves) and players (with ELO)
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Prevent player from moving out-of-turn -> login system...
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
- Editor mode : at the end, only accept valid board configurations
- split css into base.css board.css ui.css modes.css
- JS -> only toggle classes / CSS -> everything visual
- Use CSS variables for THEMES (--bg, etc.)
- Stabilize Editor Board
- Make render fully authoritative
- Is it faster to do MOVES[k] or 1 << k ?
- Improve search engine
- Backend is too python heavy, not C, should rewrite it with only np numbers...
- improve bot speed/performance
- solve the 8x8x5 and then go for 16x16x5 with 4 bitboards, then go for oo-te structure
