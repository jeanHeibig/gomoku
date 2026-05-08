import { BOARD_SIZE } from "./constants.js";
import { dom } from "./dom.js";
import { state, applyServerState } from "./state.js";
import { api } from "./api.js";
import { selectedSliders } from "./preferences.js";
import { render, renderBoard, renderCursor, renderMoveNumbers, renderPlayers, renderClocks } from "./render.js";
import { startClock, stopClock, syncClockState } from "./clock.js";
import { handleGameEnd } from "./effects.js";

export async function newGame() {
    if (state.editorMode) {
        await submitEditorBoard();
        return;
    }

    stopClock();

    const { time, increment, level } = selectedSliders();

    const data = await api(`/new_game?level=${level}&time=${time}&increment=${increment}`, {
        method: 'POST',
    });

    state.gameId = data.gid;
    state.players = data.players;
    state.localPlayerIndex = state.players[0].isBot ? 1 : 0;

    await updateFromServer();
    await maybeTriggerBotMove();
}

export async function updateFromServer() {
    const wasFinished = state.finished;

    const data = await api(`/state?gid=${state.gameId}`);

    applyServerState(data);
    syncClockState();
    render();

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

    if (state.editorMode) {
        playEditorCell(i, j);
        return;
    }

    if (!canPlayCell(i, j)) {
        return;
    }

    applyOptimisticMove(i, j);

    startClock();
    render();

    await api(`/move?gid=${state.gameId}&i=${i}&j=${j}`, {
        method: 'POST',
    });

    await updateFromServer();
    await maybeTriggerBotMove();
}

function applyOptimisticMove(i, j) {
    state.board[i][j] = state.currentPlayer + 1;
    state.lastMove = [i, j];

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

    const stone = cell.querySelector('.stone');
    stone.classList.add(state.currentPlayer === 0 ? "black" : "white", "preview");
}

export function hidePreview(cell) {
    const stone = cell.querySelector('.stone');
    stone.classList.remove("preview");

    const i = Number(cell.dataset.row);
    const j = Number(cell.dataset.col);

    if (state.board?.[i][j] === 0) {
        stone.classList.remove("black", "white");
    }
}

export function clearAllPreviews() {
    const cells = document.getElementsByClassName('cell');

    for (const cell of cells) {
        const stone = cell.querySelector('.stone');

        if (!stone.classList.contains("preview")) {
            continue;
        }

        stone.classList.remove("preview");

        const i = Number(cell.dataset.row);
        const j = Number(cell.dataset.col);

        if (state.board?.[i][j] === 0) {
            stone.classList.remove("black", "white");
        }
    }
}

export function toggleCellHighlight(cell) {
    cell.classList.toggle("marked");
}

export function toggleEditorMode() {
    state.editorMode = !state.editorMode;

    clearAllPreviews();

    if (state.editorMode) {
        state.editorBoard = structuredClone(state.board);
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
            localPlayer: state.localPlayerIndex,
            time: time,
            increment: increment,
            level: level,
        }),
    });

    state.editorMode = false;
    state.editorBoard = null;
    state.editorPlayer = null;

    state.gameId = data.gid;
    state.players = data.players;
    state.localPlayerIndex = state.players[0].isBot ? 1 : 0,

    await updateFromServer();
    await maybeTriggerBotMove();
}

function emptyBoard() {
    return Array.from({ length: BOARD_SIZE }, () =>
        Array.from({ length: BOARD_SIZE }, () => 0)
    );
}
