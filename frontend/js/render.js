import { BOARD_SIZE, BOARD_TRANSFORMS } from "./constants.js";
import { dom } from "./dom.js";
import { state, currentBoard, currentActivePlayer } from "./state.js";

const cells = [];

export function createBoard() {
    dom.board.innerHTML = "";

    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const cell = document.createElement("div");

            cell.classList.add("cell");
            cell.classList.add((row + col) % 2 === 0 ? "light" : "dark");

            cell.dataset.row = row;
            cell.dataset.col = col;
            cell.dataset.index = row * BOARD_SIZE + col;

            const stone = document.createElement("div");
            stone.classList.add("stone");

            cell.appendChild(stone);
            dom.board.appendChild(cell);

            cells.push(cell);
        }
    }
}

export function getCell(row, col) {
    return cells[row * BOARD_SIZE + col];
}

export function render() {
    renderAppState();
    renderOrientation();
    renderBoard();
    renderCursor();
    renderMoveNumbers();
    renderPlayers();
    renderNicknames();
    renderClocks();
}

function renderAppState() {
    dom.app.classList.toggle("finished", state.finished);
    dom.app.classList.toggle("editor-mode", state.editorMode);
    dom.app.classList.toggle("local-black", state.localPlayerIndex === 0);
}

export function renderBoard() {
    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            renderCell(row, col);
        }
    }
}

export function renderOrientation() {
    dom.app.dataset.transform = BOARD_TRANSFORMS[state.transformIndex];
}

export function renderCell(row, col) {
    const cell = getCell(row, col);
    const marker = state.markers[`${row},${col}`];

    const boardData = currentBoard();
    const value = boardData[row][col];

    let effectiveLastMove = null;
    let effectiveWinningTiles = [];

    if (!state.editorMode) {
        if (state.replayMode) {
            if (state.replayPly > 0) {
                effectiveLastMove = state.moveList[state.replayPly - 1];
            }
            if (state.replayPly === state.moveList.length) {
                effectiveWinningTiles = state.winningTiles;
            }
        } else {
            effectiveLastMove = state.lastMove;
            effectiveWinningTiles = state.winningTiles;
        }
    }

    cell.dataset.state =
        value === 1 ? "black" :
        value === 2 ? "white" :
        "empty";

    cell.dataset.occupied = value !== 0;

    if (marker) {
        cell.dataset.marker = marker;
    } else {
        delete cell.dataset.marker;
    }

    if (state.tacticalData?.[row][col]) {
        cell.dataset.marker = "threat";
    }

    if (
        effectiveLastMove &&
        effectiveLastMove[0] === row &&
        effectiveLastMove[1] === col
    ) {
        cell.dataset.lastMove = "true";
    } else {
        delete cell.dataset.lastMove;
    }

    if (
        effectiveWinningTiles.some(
            ([i, j]) => i === row && j === col
        )
    ) {
        cell.dataset.win = "true";
    } else {
        delete cell.dataset.win;
    }
}

export function renderCursor() {
    const canClick =
        !state.finished &&
        !state.replayMode &&
        state.players &&
        !state.players[state.currentPlayer].isBot &&
        state.localPlayerIndex === state.currentPlayer;

    dom.board.classList.toggle("no-click", !canClick)
}

export function renderMoveNumbers() {
    document.querySelectorAll(".move-number").forEach(el => el.remove());

    if (!state.finished || !state.moveList || state.editorMode) {
        return;
    }

    const visibleMoves = state.replayMode ? state.moveList.slice(0, state.replayPly) : state.moveList;

    visibleMoves.forEach(([i, j], idx) => {
        const label = document.createElement("div");
        label.className = "move-number";
        label.textContent = idx + 1;
        dom.board.children[i * BOARD_SIZE + j].appendChild(label);
    });
}

export function renderPlayers() {
    const activePlayer = currentActivePlayer();

    dom.players.black.app.classList.toggle("player-active", activePlayer === 0);
    dom.players.white.app.classList.toggle("player-active", activePlayer === 1);
}

export function renderNicknames() {
    const black = state.players[0];
    const white = state.players[1];

    document.title = `Game ${black.nickname} - ${white.nickname}`;

    renderPlayerName(dom.players.black.name, black);
    renderPlayerName(dom.players.white.name, white);
}

function renderPlayerName(playerDom, playerData) {
    const nameSpan = playerDom.querySelector(".player-name-text");
    nameSpan.textContent = playerData.nickname;

    const existing = playerDom.querySelector(".bot-label");
    if (existing) {
        existing.remove();
    }

    if (playerData.isBot) {
        const botLabel = document.createElement("span");
        botLabel.classList.add("bot-label");
        botLabel.textContent = "BOT";
        playerDom.appendChild(botLabel);
    }
}

export function renderClocks() {
    updateClockDisplay(dom.players.black.clock, state.remainingTimes[0]);
    updateClockDisplay(dom.players.white.clock, state.remainingTimes[1]);

    dom.players.black.clock.classList.toggle("low-time", state.remainingTimes[0] < 10);
    dom.players.white.clock.classList.toggle("low-time", state.remainingTimes[1] < 10);

    dom.players.black.clock.classList.toggle("active-clock", state.currentPlayer === 0);
    dom.players.white.clock.classList.toggle("active-clock", state.currentPlayer === 1);
}

export function renderReplay() {
    renderBoard();
    renderPlayers();
    renderMoveNumbers();
    renderCursor();
}

function updateClockDisplay(clockEl, time) {
    const safeTime = Math.max(0, time);

    const m = Math.floor(safeTime / 60);
    const s = Math.floor(safeTime % 60);
    const cs = Math.floor((safeTime * 100) % 100);

    clockEl.querySelector(".minutes").textContent = m.toString().padStart(2, "0");
    clockEl.querySelector(".seconds").textContent = s.toString().padStart(2, "0");
    clockEl.querySelector(".centi-seconds").textContent =
        safeTime >= 20 ? "" : cs.toString().padStart(2, "0");
}
