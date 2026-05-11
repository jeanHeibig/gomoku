import { BOARD_SIZE, BOARD_TRANSFORMS } from "./constants.js";
import { dom } from "./dom.js";
import { state, applyServerState, replayCurrentPlayer, replayMoveList, currentBoard } from "./state.js";
import { api } from "./api.js";
import { selectedSliders } from "./preferences.js";
import { render, renderBoard, renderOrientation, renderCell, renderCursor, renderMoveNumbers, renderPlayers, renderClocks } from "./render.js";
import { startClock, stopClock, syncClockState } from "./clock.js";
import { handleGameEnd } from "./effects.js";

export async function newGame() {
    if (state.editorMode) {
        await submitEditorBoard();
        return;
    }

    exitReplayMode();
    stopClock();

    const { time, increment, level } = selectedSliders();

    const data = await api(`/new_game?level=${level}&time=${time}&increment=${increment}`, {
        method: 'POST',
    });

    await launchNewGame(data);
}

async function launchNewGame(data) {
    state.gameId = data.gid;
    state.initialBoard = JSON.stringify(data.board);
    state.initialPlayer = data.currentPlayer;
    state.players = data.players;
    state.localPlayerIndex = state.players[0].isBot ? 1 : 0;

    await updateFromServer();
    await maybeTriggerBotMove();
}

export async function updateFromServer() {
    const wasFinished = state.finished;

    const data = await api(`/state?gid=${state.gameId}`);

    applyServerState(data);
    resetTacticalData();
    syncClockState();
    render();
    refreshHoverPreview();

    if (!wasFinished && state.finished) {
        handleGameEnd();
    }
}

export async function maybeTriggerBotMove() {
    if (
        state.botMoveInProgress ||
        state.finished ||
        !state.players ||
        !state.players[state.currentPlayer].isBot
    ) {
        return;
    }

    state.botMoveInProgress = true;

    await api(`/botMove?gid=${state.gameId}`, {
        method: "POST"
    });

    await updateFromServer();

    state.botMoveInProgress = false;
}

export async function playCell(cell) {
    const i = Number(cell.dataset.row);
    const j = Number(cell.dataset.col);

    resetTacticalData();

    if (state.editorMode) {
        playEditorCell(i, j);
        return;
    }

    if (!canPlayCell(i, j)) {
        return;
    }

    if (state.replayMode) {
        exitReplayMode();
        render();
    }

    const previousLastMove = state.lastMove ? [...state.lastMove] : null;
    applyOptimisticMove(i, j);

    startClock();

    if (previousLastMove) {
        renderCell(previousLastMove[0], previousLastMove[1]);
    }
    renderCell(i, j);
    renderCursor();
    renderPlayers();
    renderClocks();

    await api(`/move?gid=${state.gameId}&i=${i}&j=${j}`, {
        method: 'POST',
    });

    if (state.replayMode) {
        exitReplayMode();
        render();
    }

    await updateFromServer();
    await maybeTriggerBotMove();
}

function resetTacticalData() {
    if (state.tacticalData) {
        state.tacticalData = null;
        renderBoard();
    }
}

function applyOptimisticMove(i, j) {
    state.board[i][j] = state.currentPlayer + 1;
    state.lastMove = [i, j];
    state.moveList.push([i, j]);

    state.remainingTimes[state.currentPlayer] += state.increments[state.currentPlayer];

    state.currentPlayer = 1 - state.currentPlayer;
    state.clockPly += 1;
    state.lastUpdate = Date.now();

    clearAllPreviews();
}

export function canPlayCell(i, j) {
    return (
        state.board &&
        state.localPlayerIndex === state.currentPlayer &&
        state.board[i][j] === 0 &&
        !state.finished &&
        !state.editorMode
    );
}

export function showPreview(cell) {
    const i = Number(cell.dataset.row);
    const j = Number(cell.dataset.col);

    if (!canPlayCell(i, j)) {
        return;
    }

    cell.dataset.preview = state.currentPlayer === 0 ? "black" : "white";
}

export function hidePreview(cell) {
    delete cell.dataset.preview;
}

export function clearAllPreviews() {
    const cells = document.getElementsByClassName('cell');

    for (const cell of cells) {
        if (!cell.dataset.preview) {
            continue;
        }

        delete cell.dataset.preview;
    }
}

export function refreshHoverPreview() {
    if (!state.hoveredCell) {
        return;
    }

    hidePreview(state.hoveredCell);
    showPreview(state.hoveredCell);
}

export function toggleMarker(cell, color) {
    const i = Number(cell.dataset.row);
    const j = Number(cell.dataset.col);

    const key = `${i},${j}`;

    if (state.markers[key] === color) {
        delete state.markers[key];
    } else {
        state.markers[key] = color;
    }

    renderCell(i, j);
}

export function clearAllMarkers() {
    state.markers = {};

    renderBoard();
}

export function toggleMirrorHorizontal(vertical) {
    if (vertical) {
        if (state.transformIndex < 4) {
            state.transformIndex = (state.transformIndex + 2) % 4;
        } else {
            state.transformIndex = 4 + (state.transformIndex - 2) % 4;
        }
    }
    state.transformIndex = (state.transformIndex + 4) % 8;

    renderOrientation();
}

export function cycleRotation(backwards) {
    if (state.transformIndex < 4) {
        state.transformIndex = (state.transformIndex + (backwards ? 3 : 1)) % 4;
    } else {
        state.transformIndex = 4 + (state.transformIndex - (backwards ? 3 : 1)) % 4;
    }

    renderOrientation();
}

export function enterReplayMode() {
    // if (!state.finished) {
    //     return;
    // }

    state.replayMode = true;
    state.replayPly = state.moveList.length;

    state.replayBoard = buildReplayBoard(state.replayPly);

    render();
}

export function exitReplayMode() {
    state.replayMode = false;
    state.replayPly = null;
    state.replayBoard = null;
}

function buildReplayBoard(ply) {
    const board = JSON.parse(state.initialBoard);

    let player = state.initialPlayer;

    for (let k = 0; k < ply; k++) {
        const [i, j] = state.moveList[k];

        board[i][j] = player + 1;

        player = 1 - player;
    }

    return board;
}

export function replayPrevious() {
    // if (!state.finished) {
    //     return;
    // }

    if (!state.replayMode) {
        enterReplayMode();
    }

    if (state.replayPly <= 0) {
        return;
    }

    state.replayPly--;

    state.replayBoard = buildReplayBoard(state.replayPly);

    resetTacticalData();
    renderBoard();
    renderMoveNumbers();
}

export function replayNext() {
    // if (!state.finished) {
    //     return;
    // }

    if (!state.replayMode) {
        enterReplayMode();
    }

    if (state.replayPly >= state.moveList.length) {
        return;
    }

    state.replayPly++;

    state.replayBoard = buildReplayBoard(state.replayPly);

    resetTacticalData();
    renderBoard();
    renderMoveNumbers();
}

export function replayStart() {
    // if (!state.finished) {
    //     return;
    // }

    state.replayMode = true;
    state.replayPly = 0;
    state.replayBoard = buildReplayBoard(0);

    resetTacticalData();
    renderBoard();
    renderMoveNumbers();
}

export function replayEnd() {
    // if (!state.finished) {
    //     return;
    // }

    state.replayMode = true;
    state.replayPly = state.moveList.length;
    state.replayBoard = buildReplayBoard(state.replayPly);

    resetTacticalData();
    renderBoard();
    renderMoveNumbers();
}

export async function restartFromReplay() {
    if (!state.replayMode) {
        return;
    }

    stopClock();

    const { time, increment, level } = selectedSliders();

    const data = await api(`/submit_board`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            board: state.replayBoard,
            editorPlayer: replayCurrentPlayer(),
            moveList: replayMoveList(),
            localPlayer: state.localPlayerIndex,
            time: time,
            increment: increment,
            level: level,
        })
    });

    exitReplayMode();
    await launchNewGame(data);
}

export async function analyzeTactics() {

    if (state.tacticalData) {
        resetTacticalData();
        return
    }

    const data = await api(`/tactics`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            board: currentBoard(),
            currentPlayer: state.currentPlayer,
        })
    })

    state.tacticalData = data;
    renderBoard();
}

export function toggleEditorMode() {
    state.editorMode = !state.editorMode;

    resetTacticalData();
    clearAllPreviews();

    if (state.editorMode) {
        state.editorBoard = state.replayMode ? structuredClone(state.replayBoard) : structuredClone(state.board);
        state.editorPlayer = state.currentPlayer;
    } else {
        state.editorBoard = null;
        state.editorPlayer = null;
    }

    render();
}

export function toggleEditorPlayer() {
    if (!state.editorMode) {
        return;
    }

    state.editorPlayer = 1 - state.editorPlayer;
    renderPlayers();
}

export function clearEditorBoard() {
    if (!state.editorMode) {
        return;
    }

    state.editorBoard = emptyBoard();
    renderBoard();
}

export function swapEditorColors() {
    if (!state.editorMode) {
        return;
    }

    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            if (state.editorBoard[i][j] === 1) {
                state.editorBoard[i][j] = 2;
            } else if (state.editorBoard[i][j] === 2) {
                state.editorBoard[i][j] = 1;
            }
        }
    }

    // toggleEditorPlayer();
    renderBoard();
}

function playEditorCell(i, j) {
    const current = state.editorBoard[i][j];
    const next = state.editorPlayer + 1;

    state.editorBoard[i][j] = current === next ? 0 : next;

    renderBoard();
}

export async function submitEditorBoard() {
    if (!state.editorMode) {
        return;
    }

    exitReplayMode();
    stopClock();

    const { time, increment, level } = selectedSliders();

    const data = await api(`/submit_board`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            board: state.editorBoard,
            editorPlayer: state.editorPlayer,
            moveList: null,
            localPlayer: state.localPlayerIndex,
            time: time,
            increment: increment,
            level: level,
        }),
    });

    state.editorMode = false;
    state.editorBoard = null;
    state.editorPlayer = null;

    await launchNewGame(data);
}

function emptyBoard() {
    return Array.from({ length: BOARD_SIZE }, () =>
        Array.from({ length: BOARD_SIZE }, () => 0)
    );
}
