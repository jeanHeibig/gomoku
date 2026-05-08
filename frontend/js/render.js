import { BOARD_SIZE } from "./constants.js";
import { dom } from "./dom.js";
import { state, currentBoard } from "./state.js";

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
        }
    }
}

export function render() {
    renderAppState();
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
    const boardData = currentBoard();

    const effectiveLastMove = state.editorMode ? null : state.lastMove;
    const effectiveWinningTiles = state.editorMode ? [] : state.winningTiles;
    const cells = document.getElementsByClassName('cell');

    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const cell = cells[row * BOARD_SIZE + col];
            const stone = cell.querySelector('.stone');
            const value = boardData[row][col];

            cell.classList.toggle(
                "last-move",
                Boolean(
                    effectiveLastMove &&
                    effectiveLastMove[0] === row &&
                    effectiveLastMove[1] === col
                )
            );

            cell.classList.toggle(
                "win",
                effectiveWinningTiles.some(([i, j]) => i === row && j === col)
            );

            cell.classList.toggle("occupied", value !== 0);

            stone.classList.toggle("black", value === 1);
            stone.classList.toggle("white", value === 2);

            if (value !== 0) {
                stone.classList.remove("preview");
            }
        }
    }
}

export function renderCursor() {
    const canClick =
        !state.finished &&
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

    state.moveList.forEach(([i, j], idx) => {
        const label = document.createElement("div");
        label.className = "move-number";
        label.textContent = idx + 1;
        dom.board.children[i * BOARD_SIZE + j].appendChild(label);
    });
}

export function renderPlayers() {
    const activePlayer = state.editorMode ? state.editorPlayer : state.currentPlayer;

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
