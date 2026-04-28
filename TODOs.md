# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Editor mode : remove winning tiles red ?
- Editor mode : starting a Game should accept currentPlayer...
- Editor mode : missing editor indicator in html (found in js)
- Find an evaluation function for a position -> core of the problem
- Add "real" (concrete games based on simple bots) Monte-Carlo for fast eval function
- Implement iterative α-β search
- Use board symmetries
- Opening tables
- Endgame tables: "kill" stones that can no longer contribute to an alignment
- Add draw and resign button
- Add SQLite to saves games (with moves) and players (with ELO)
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Prevent player from moving out-of-turn !
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
- Blue mode -> manage custom theme through color aliasesm
