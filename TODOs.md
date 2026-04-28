# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Add board.addEventListener click onstead of 64 cells.
- rewrite js with dom const
- optimize rendering by only updating changed cells, times, etc. instead of re-rendering everything
- add MC to all levels, otherwise, they are really bad
- bug UI : les cells occupées ont un mauvais curseur
- Fix Game UI editor
- Find an evaluation function for a position -> core of the problem
- Add "real" (concrete games based on simple bots) Monte-Carlo for fast eval function
- Implement iterative α-β search
- Use board symmetries
- Opening tables
- Endgame tables: "kill" stones that can no longer contribute to an alignment
- Add a board editor function
- Add draw and resign button
- Add SQLite to saves games (with moves) and players (with ELO)
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Prevent player from moving out-of-turn !
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
