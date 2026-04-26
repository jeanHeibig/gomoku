# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Refactor JS / HTML
- Allow a bot to retain memory from one turn to another via a memory parameter of any type
- Board and/or bitboard class
- Improve performance: port the latest bot to C, optimize the long blocking of double threats
- Add a logger that saves games
- Add a logger that saves everything possible for debugging (external logging library?)
- Implement a player database with Elo rankings
- Find an evaluation function for a position -> core of the problem
- Implement iterative α-β search
- Use board symmetries
- Opening tables
- Endgame tables: "kill" stones that can no longer contribute to an alignment
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Prevent player from moving out-of-turn !
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
