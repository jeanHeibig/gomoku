# Gomoku Server and AI Training

A comprehensive Gomoku (8x8) game server implementation with AI bot training capabilities, built with FastAPI and featuring a web-based interface for human vs AI gameplay.

## Features

### Core Gameplay
- **8x8 Gomoku Board**: First to get 5 in a row wins
- **Time Controls**: 15 minutes + 1 second increment per move
- **Human vs AI**: Play against various AI bot implementations
- **Real-time Clock**: Visual timer display with automatic time management

### AI System
- **Multiple Bot Strategies**:
  - Random Bot: Makes random valid moves
  - Take Win in One Bot: Immediately takes winning moves
  - Block Opponent Bot: Blocks immediate threats
  - Double Threats Bot: Creates multiple winning threats
  - Prevent Double Threats Bot: Blocks opponent's double threats
  - Monte Carlo Score Bot: Uses Monte Carlo evaluation
- **Bot Tournament System**: Automated bot vs bot matches for training and evaluation
- **Elo Rating System**: Planned player ranking system

### Web Interface
- **Responsive Design**: Clean, modern web interface
- **Real-time Updates**: Live game state synchronization
- **Clock Visualization**: Visual timer display for both players
- **Move Highlighting**: Highlights last moves and winning alignments (planned)

### Server Architecture
- **FastAPI Backend**: High-performance async API server
- **RESTful API**: Well-documented endpoints for game management
- **WebSocket Support**: Planned for real-time multiplayer features
- **Bitboard Implementation**: Efficient board representation for AI calculations

## Project Structure

```
project/
├── api/                    # FastAPI server
│   ├── __init__.py
│   └── app.py             # Main API server with endpoints
├── backend/               # Game logic and AI
│   ├── __init__.py
│   ├── bitboard.py        # Bitboard implementation
│   ├── elo.py            # Elo rating system
│   ├── game.py           # Core game logic
│   ├── clock/            # Time management
│   │   ├── __init__.py
│   │   ├── test_timeout.py
│   │   ├── timeout.py
│   │   └── timer.py
│   ├── masks/            # Precomputed bitmasks
│   │   ├── board_tiles.py
│   │   ├── masks_generator_all_board.py
│   │   ├── masks_generator_by_cell.py
│   │   ├── precomputed_masks_all_board.py
│   │   └── precomputed_masks_by_cell.py
│   └── players/          # Player and bot implementations
│       ├── __init__.py
│       ├── human.py
│       ├── online_bot.py
│       ├── player.py
│       └── bots/
│           ├── __init__.py
│           ├── block_opponent_bot.py
│           ├── double_threats_bot.py
│           ├── mc_score_bot.py
│           ├── prevent_double_threats_bot.py
│           ├── random_bot.py
│           └── take_win_in_one_bot.py
├── frontend/              # Web interface
│   ├── app.js            # Frontend JavaScript
│   ├── game.html         # Main game page
│   ├── login.html        # Login page (planned)
│   └── style.css         # CSS styling
├── tournament.py         # Bot tournament system
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
├── README.md            # This file
└── TODOs.md             # Development roadmap
```

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/jeanHeibig/gomoku.git
   cd gomoku/8_8_5/project
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the server:
   ```bash
   uvicorn api.app:app --reload
   ```

4. Open your browser to `http://localhost:8000`

## Usage

### Playing the Game
1. Navigate to the game page
2. Click "NEW GAME" to start a new match
3. Click on the board to make your move
4. The AI will respond automatically
5. Game ends when a player gets 5 in a row or time runs out

### Running Tournaments
Execute bot tournaments for AI training:
```bash
python tournament.py
```

This will run automated matches between different bot implementations and output results.

## API Documentation

The server provides the following REST endpoints:

### GET /
Serves the main game HTML interface.

### POST /new_game
Creates a new game with random player order.
**Returns**: Game state object with board, players, timers, etc.

### POST /move
Makes a move in an existing game.
**Parameters**:
- `gid` (str): Game ID
- `i` (int): Row index (0-7)
- `j` (int): Column index (0-7)
**Returns**: Updated game state

### POST /flag
Checks for time violations in a game.
**Parameters**:
- `gid` (str): Game ID
**Returns**: Updated game state

### GET /state
Retrieves current game state without making changes.
**Parameters**:
- `gid` (str): Game ID
**Returns**: Current game state

## Development

### Current State
The project is in active development with the following implemented:
- ✅ Basic game logic and rules
- ✅ Multiple AI bot implementations
- ✅ Web interface with real-time gameplay
- ✅ Tournament system for bot evaluation
- ✅ Time controls and clock management
- ✅ Bitboard optimization for performance

### Planned Features
See [TODOs.md](TODOs.md) for the complete development roadmap, including:
- Advanced AI algorithms (α-β search, evaluation functions)
- Database integration for player rankings
- WebSocket support for real-time features
- Enhanced GUI features (move highlighting, animations)
- Online multiplayer capabilities
- Opening and endgame tablebases

### Running Tests
```bash
# Run tournament tests
python tournament.py

# Test specific bot implementations
python -m backend.players.bots.random_bot
```

### Code Quality
- Follow PEP 8 style guidelines
- Add docstrings to all public functions
- Include unit tests for new features
- Use type hints where possible

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run existing tests to ensure no regressions
5. Submit a pull request with a clear description

### Areas for Contribution
- AI algorithm improvements
- Frontend enhancements
- Performance optimizations
- Documentation improvements
- Bug fixes and testing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Uses [NumPy](https://numpy.org/) for efficient array operations
- Inspired by traditional Gomoku gameplay and AI research

---

For more details on current development status and planned features, see [TODOs.md](TODOs.md).
