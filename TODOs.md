# gomoku
Gomoku Server and AI training

# TODO

- bot needs to do a faster search
- Add draw and resign button (t, r)
- Add then add threats get_scores
- Introduce dead cells -> cells that a player can no longer have interest in, because they can't produce a win -> reduces attack search
- dead cell should also allow a player to know if both players play for a win or someone already plays for a draw
- Eval as a dead draw as soon as no alignment is possible anymore
- Implement iterative α-β search
- current bot is dumb at tactics
- Get scores (and Fast eval?) must look for tactics
- current eval function is biased towards X (O missing one move during the eval)
- Use PV-search
- Use Transposition tables
- add an opening book
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
- manage custom theme through color aliasesm
- TODO : merge new game and submit board
- Editor mode : at the end, only accept valid board configurations
- Review code and inline TODOs
- split css into base.css board.css ui.css modes.css
- JS -> only toggle classes / CSS -> everything visual
- Stabilize Editor Board
- Make render fully authoritative
- Is it faster to do MOVES[k] or 1 << k ?
- Improve search engine
- Backend is too python heavy, not C, should rewrite it with only np numbers...
