export const state = {
    gameId: null,
    players: null,

    board: null,
    lastMove: null,
    hoveredCell: null,
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

    replayMode: false,
    replayPly: null,
    replayBoard: null,
    initialBoard: null,
    initialPlayer: 0,
    tacticalData: null,

    markers: {},
    transformIndex: 0,

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
    if (state.editorMode) {
        return state.editorBoard;
    }

    if (state.replayMode) {
        return state.replayBoard;
    }

    return state.board;
}

export function currentActivePlayer() {
    if (state.editorMode) {
        return state.editorPlayer;
    }

    if (state.replayMode && state.finished) {
        return replayCurrentPlayer();
    }

    return state.currentPlayer;
}

export function replayMoveList() {
    if (!state.replayMode) {
        return state.moveList;
    }

    return state.moveList.slice(0, state.replayPly);
}

export function replayCurrentPlayer() {
    if (state.finished && state.replayPly === state.moveList.length) {
        return state.currentPlayer;
    }

    return (state.initialPlayer + state.replayPly) % 2;
}
