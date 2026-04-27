# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Clean existing bots level 0 -> 5
- Improve Board and move structure so that it is numpy efficient
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
