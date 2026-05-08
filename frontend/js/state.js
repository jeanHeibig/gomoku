export const state = {
    gameId: null,
    players: null,

    board: null,
    lastMove: null,
    moveList: [],
    winningTiles: [],

    currentPlayer: 0,
    winner: null,
    finished: false,
    localPlayerIndex: 0,

    remainingTimes: [0, 0],
    increments: [0, 0],
    clockPly: 0,
    lastUpdate: Date.now(),
    clockInterval: null,

    editorMode: false,
    editorBoard: null,
    editorPlayer: null,

    botMoveInProgress: false,
};

export function applyServerState(data) {
    state.board = data.board;
    state.lastMove = data.lastMove;
    state.moveList = data.moveList;
    state.winningTiles = data.winningTiles;

    state.remainingTimes = [...data.times.times];
    state.increments = [...data.times.increments];
    state.clockPly = data.clockPly;

    state.currentPlayer = data.currentPlayer;
    state.finished = data.finished;
    state.winner = data.winner;

    state.lastUpdate = Date.now();
}

export function currentBoard() {
    return state.editorMode ? state.editorBoard : state.board;
}
