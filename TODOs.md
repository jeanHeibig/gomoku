# gomoku
Gomoku Server and AI training

# TODO

- Review code and inline TODOs
- Add a logger that saves games
- Add a logger that saves everything possible for debugging (external logging library?)
- Implement a player database with Elo rankings
- Find an evaluation function for a position -> core of the problem
- Add "real" (concrete games based on simple bots) Monte-Carlo for fast eval function
- Implement iterative α-β search
- Use board symmetries
- Opening tables
- Endgame tables: "kill" stones that can no longer contribute to an alignment
- Switch to websockets for GUI
- Switch to websockets for BOT tournaments and allow players to submit bots online after verification
- Add draw and resign button
- Add a board editor funciton
- Prevent player from moving out-of-turn !
- Handle timeouts by the server
- Deploy server online so players can connect via link to play against the bot
- Login page
- Manage matchmaking
- Add a GUI toggle with letter M : stones vs X/O
