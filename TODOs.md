# gomoku
Gomoku Server and AI training

# TODO

- Remove X to move indicator in board editor
- active player does not work when bot thinks
- Add draw and resign button (t, r)
- Declare draw as soon as no alignment is possible anymore
- Implement iterative α-β search
- current bot is dumb at tactics
- current eval function is biased towards X (O missing one move during the eval)
- Get scores (and Fast eval?) must look for tactics
- Use PV-search
- Use Transposition tables
- Use board symmetries
- Use History Killer Moves
- Opening tables
- Endgame tables: "kill" stones that can no longer contribute to an alignment
- Initialise board before recieving first bot move ?...
- Preview does not work after recieving a move
- Add SQLite to saves games (with moves) and players (with ELO)
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Prevent player from moving out-of-turn !
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
- Blue mode -> manage custom theme through color aliasesm
- TODO : merge new game and submit board
- Editor mode : at the end, only accept valid board configurations
- Review code and inline TODOs
- split css into base.css board.css ui.css modes.css
- JS -> only toggle classes / CSS -> everything visual
- Stabilize Editor Board
- Make render fully authoritative
- Is it faster to do MOVES[k] or 1 << k ?
- Improve search engine
