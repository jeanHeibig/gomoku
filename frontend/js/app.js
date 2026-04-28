// 1. DOM refs
// const dom = {
//     appEl: document.getElementById("app"),
//     board: document.getElementById("board"),

//     controls: {
//         newGameBtn: document.getElementById("new-game-btn"),
//         levelSlider: document.getElementById("level"),
//         levelValue: document.getElementById("level-value"),
//     },

//     players: {
//         black: {
//             appEl: document.getElementById("player-black"),
//             clock: document.getElementById("clock-black"),
//             name: document.getElementById("player-name-black"),
//         },
//         white: {
//             appEl: document.getElementById("player-white"),
//             clock: document.getElementById("clock-white"),
//             name: document.getElementById("player-name-white"),
//         }
//     },

//     editor: {
//         indicator: document.getElementById("editor-indicator"),
//     },
// };


const appEl = document.getElementById("app");
const boardEl = document.getElementById("board");

const newGameBtn = document.getElementById("new-game-btn");

const levelSlider = document.getElementById("level");
const levelLabel = document.getElementById("level-label");
const levelLabels = {
    0: "Random",
    1: "Very easy",
    2: "Easy",
    3: "Medium",
    4: "Hard",
    5: "Very hard",
};

const clockBlackEl = document.getElementById("clock-black");
const clockWhiteEl = document.getElementById("clock-white");

const playerBlackEl = document.getElementById("player-black");
const playerWhiteEl = document.getElementById("player-white");

const playerNameBlackEl = document.getElementById("player-name-black");
const playerNameWhiteEl = document.getElementById("player-name-white");

const editorIndicator = document.getElementById("editor-indicator");

// 2. state
const state = {
    gameId: null,
    players: null,

    board: null,
    lastMove: null,
    winningTiles: [],

    currentPlayer: 0,
    finished: false,
    localPlayerIndex: 0,

    remainingTimes: [0, 0],
    increments: [0, 0],
    clockPly: 0,
    lastUpdate: Date.now(),
    clockInterval: null,

    editorMode: false,
    editorBoard: null,
    editorPlayer: 0,
};

// 3. init
function init() {
    initSlider();
    createBoard();
    initEvents();

    newGame();  // initialize a new game on page load
}

function initSlider() {
    levelSlider.value = localStorage.getItem("level") || 5;
    levelLabel.textContent = levelLabels[levelSlider.value];

    levelSlider.addEventListener("input", () => {
        levelLabel.textContent = levelLabels[levelSlider.value];
        localStorage.setItem("level", levelSlider.value);
    });
}

function createBoard() {
    boardEl.innerHTML = "";

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cell = document.createElement("div");
            cell.classList.add("cell");

            cell.classList.add((row + col) % 2 === 0 ? "light" : "dark");

            cell.dataset.row = row;
            cell.dataset.col = col;
            cell.dataset.index = row * 8 + col;

            const stone = document.createElement("div");
            stone.classList.add("stone");

            cell.appendChild(stone);
            boardEl.appendChild(cell);
        }
    }
}

// 4. events
function initEvents() {
    initKeyboard();
    initBoardEvents();
}

function initKeyboard() {
    document.addEventListener("keydown", (e) => {
        const tag = document.activeElement.tagName.toLowerCase();
        if (tag === "input" || tag === "textarea") {
            return; // ignore when typing in inputs
        }

        switch (e.key.toLowerCase()) {
            case "m":
                appEl.classList.toggle("morpion-mode");
                break;

            case "e":
                toggleEditorMode();
                break;
        }

        if (e.key === " ") {
            if (state.editorMode) {
                state.editorPlayer = 1 - state.editorPlayer;
                updateEditorIndicator();
            }
        }

        if (e.key === "Enter") {
            if (state.editorMode) {
                submitEditorBoard();
            } else if (state.finished) {
                newGame();
            }
        }
    });
}

function initBoardEvents() {
    const cells = document.getElementsByClassName('cell');
    for (let n = 0; n < cells.length; n++) {
        const cell = cells[n];

        cell.addEventListener("click", () => play(cell));

        cell.addEventListener("mouseenter", () => {
            if (!state.editorMode) {
                showPreview(cell);
            }
        });

        cell.addEventListener("mouseleave", () => {
            if (!state.editorMode) {
                hidePreview(cell);
            }
        });
    }
}

// 5. api
async function api(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();
    return data;
}

// 6. actions
async function newGame() {
    stopClock();
    setFinished(false);

    const data = await api(`/new_game?level=${levelSlider.value}`, {
        method: 'POST',
    });
    state.gameId = data.gid;
    state.players = data.players;

    renderNicknames();
    update();
}

async function play(cell) {
    const i = parseInt(cell.dataset.row);
    const j = parseInt(cell.dataset.col);

    if (state.editorMode) {
        state.editorBoard[i][j] = (state.editorBoard[i][j] + 1) % 3;
        renderBoard();
        return;
    }

    if (!canPlay(cell)) {
        return;
    }

    // optimistically update the board
    state.board[i][j] = state.currentPlayer + 1;
    hidePreview(cell);
    state.lastMove = [i, j];
    state.remainingTimes[state.currentPlayer] += state.increments[state.currentPlayer];

    state.currentPlayer = 1 - state.currentPlayer;
    state.lastUpdate = Date.now();

    renderBoard();
    renderClocks();

    await api(`/move?gid=${state.gameId}&i=${i}&j=${j}`, {
        method: 'POST',
    });

    update();
}

async function update() {
    const data = await api(`/state?gid=${state.gameId}`);

    applyServerState(data);
    render();
}

// 7. helpers
function setFinished(finished) {
    state.finished = finished;

    if (finished) {
        stopClock();
        appEl.classList.add("finished");
        newGameBtn.style.display = "block";
    } else {
        appEl.classList.remove("finished");
        newGameBtn.style.display = "none";
    }
}

function applyServerState(data) {
    state.board = data.board;
    state.lastMove = data.last_move;
    state.winningTiles = data.winningTiles;

    state.remainingTimes = [...data.times.times];
    state.increments = [...data.times.increments];
    state.clockPly = data.clockPly;
    state.currentPlayer = data.currentPlayer;
    state.finished = data.finished;
    state.winner = data.winner;

    state.lastUpdate = Date.now();
}

// 8. render
function render() {
    renderBoard();
    renderPlayers();
    renderClocks();
    renderEndGame();
}

function renderBoard() {
    const boardData = state.editorMode ? state.editorBoard : state.board;
    const cells = document.getElementsByClassName('cell');

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cell = cells[row * 8 + col];
            const stone = cell.querySelector('.stone');

            cell.classList.remove("last-move", "win");
            stone.classList.remove("black", "white");

            if (state.lastMove?.[0] === row && state.lastMove?.[1] === col) {
                cell.classList.add("last-move");
            }

            if (state.winningTiles.some(([i, j]) => i === row && j === col)) {
                cell.classList.add("win");
            }

            const v = boardData[row][col];
            if (v === 1) {
                stone.classList.add("black");
            } else if (v === 2) {
                stone.classList.add("white");
            }
        }
    }
}

function renderPlayers() {
    document.getElementById("player-black").classList.toggle("active", state.currentPlayer === 0);
    document.getElementById("player-white").classList.toggle("active", state.currentPlayer === 1);
}

function renderNicknames() {
    const b = state.players[0];
    const w = state.players[1];

    document.title = `Game ${b.nickname} - ${w.nickname}`;

    const black = document.getElementById("player-name-black");
    black.querySelector(".player-name-text").textContent = b.nickname;
    black.querySelector(".bot-label").classList.toggle("hidden", !b.isBot);

    const white = document.getElementById("player-name-white");
    white.querySelector(".player-name-text").textContent = w.nickname;
    white.querySelector(".bot-label").classList.toggle("hidden", !w.isBot);

    state.localPlayerIndex = b.isBot ? 1 : 0;
}

function renderClocks() {
    const cBlack = document.getElementById("clock-black");
    const cWhite = document.getElementById("clock-white");

    updateClockDisplay(cBlack, state.remainingTimes[0]);
    updateClockDisplay(cWhite, state.remainingTimes[1]);

    cBlack.classList.toggle("low-time", state.remainingTimes[0] < 10);
    cWhite.classList.toggle("low-time", state.remainingTimes[1] < 10);

    cBlack.classList.toggle("active-clock", state.currentPlayer === 0);
    cWhite.classList.toggle("active-clock", state.currentPlayer === 1);
}

function renderEndGame() {
    if (!state.finished) {
        startClock();
        return;
    }

    stopClock();
    appEl.classList.add("finished");
    newGameBtn.style.display = "block";

    setTimeout(() => {
        alert(
            state.winner === 0 ? "Black wins!" :
            state.winner === 1 ? "White wins!" :
            "Draw."
        );
    }, 50);
}

// 9. ui
function canPlay(cell) {
    const i = parseInt(cell.dataset.row);
    const j = parseInt(cell.dataset.col);

    return (
        state.board &&
        state.localPlayerIndex === state.currentPlayer &&
        state.board[i][j] === 0 &&
        !state.finished &&
        !state.editorMode
    );
}

function showPreview(cell) {
    if (!canPlay(cell)) {
        return;
    }

    const stone = cell.querySelector('.stone');
    stone.classList.add(state.currentPlayer === 0 ? "black" : "white", "preview");
}

function hidePreview(cell) {
    const stone = cell.querySelector('.stone');
    stone.classList.remove("black", "white", "preview");

    const i = parseInt(cell.dataset.row);
    const j = parseInt(cell.dataset.col);

    if (state.board?.[i][j] !== 0) {
        stone.classList.add(state.board[i][j] === 1 ? "black" : "white");
    }
}

// 10. clock
function startClock() {
    if (state.clockPly < 2) {
        return;
    }

    stopClock();

    state.clockInterval = setInterval(() => {
        if (state.finished) {
            return;
        }

        const now = Date.now();
        const dt = (now - state.lastUpdate) / 1000;

        state.lastUpdate = now;
        state.remainingTimes[state.currentPlayer] -= dt;

        checkTimeout();
        renderClocks();
    }, 73);
}

function stopClock() {
    if (state.clockInterval) {
        clearInterval(state.clockInterval);
        state.clockInterval = null;
    }
}

async function checkTimeout() {
    if (state.finished) {
        return;
    }

    if (state.remainingTimes[state.currentPlayer] <= 0) {
        state.remainingTimes[state.currentPlayer] = 0;

        try {
            await api(`/flag?gid=${state.gameId}`, {
                method: 'POST',
            });
        } catch (e) {
            console.error("Error occurred while checking timeout:", e);
        }

        update();
    }
}

function updateClockDisplay(el, t) {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    const cs = Math.floor((t * 100) % 100);

    el.querySelector(".minutes").textContent = m.toString().padStart(2, "0")
    el.querySelector(".seconds").textContent = s.toString().padStart(2, "0")
    el.querySelector(".centi-seconds").textContent = (t >= 20) ? "" : cs.toString().padStart(2, "0");
}

// 11. editor
function toggleEditorMode() {
    state.editorMode = !state.editorMode;

    if (state.editorMode) {
        state.editorBoard = structuredClone(state.board);
        appEl.classList.add("editor-mode");
    } else {
        state.editorBoard = null;
        appEl.classList.remove("editor-mode");
    }

    renderBoard();
}

function updateEditorIndicator() {
    const el = document.getElementById("editor-indicator");

    el.textContent = state.editorPlayer === 0 ? "Black to move" : "White to move";
}

async function submitEditorBoard() {
    stopClock();
    setFinished(false);

    const data = await api(`/submit_board`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            board: state.editorBoard,
            player: state.editorPlayer,
            level: levelSlider.value,
        })
    });

    state.editorMode = false;
    state.editorBoard = null;
    appEl.classList.remove("editor-mode");

    state.gameId = data.gid;
    state.players = data.players;

    renderNicknames();
    update();
}

document.addEventListener("DOMContentLoaded", init);
