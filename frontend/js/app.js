// 1. DOM refs
const dom = {
    app: document.getElementById("app"),
    board: document.getElementById("board"),

    controls: {
        newGameBtn: document.getElementById("new-game-btn"),
        timeSlider: document.getElementById("time-slider"),
        timeLabel: document.getElementById("time-label"),
        incrementSlider: document.getElementById("increment-slider"),
        incrementLabel: document.getElementById("increment-label"),
        levelSlider: document.getElementById("level"),
        levelLabel: document.getElementById("level-label"),
    },

    players: {
        black: {
            app: document.getElementById("player-black"),
            clock: document.getElementById("clock-black"),
            name: document.getElementById("player-name-black"),
        },
        white: {
            app: document.getElementById("player-white"),
            clock: document.getElementById("clock-white"),
            name: document.getElementById("player-name-white"),
        }
    },

    editor: {
        indicator: document.getElementById("editor-indicator"),
    },
};

const TIME_PRESETS = [
    3, 15, 30, 60, 120, 180, 300, 600, 900, 1800, 3600
];

const INCREMENT_PRESETS = [
    0, 1, 2, 3, 5, 10, 15, 30, 60
];

const levelLabels = {
    0: "Random",
    1: "Very easy",
    2: "Easy",
    3: "Medium",
    4: "Hard",
};

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

    loadSystemPreferences();
    initSliders();
    createBoard();
    initEvents();

    newGame();  // initialize a new game on page load
}

function loadSystemPreferences() {
    const isMorpionMode = localStorage.getItem("morpionMode");
    if (isMorpionMode === "false") {
        dom.app.classList.remove("morpion-mode");
    }

    const isDark = localStorage.getItem("darkMode");
    if (isDark === "true") {
        document.body.classList.add("dark-mode");
    }
}

function initSliders() {
    dom.controls.timeSlider.max = TIME_PRESETS.length - 1;
    dom.controls.incrementSlider.max = INCREMENT_PRESETS.length - 1;

    dom.controls.timeSlider.value = localStorage.getItem("time") || 6;  // defaut 5+2
    dom.controls.incrementSlider.value = localStorage.getItem("increment") || 2;

    updateTimeLabels();

    dom.controls.timeSlider.addEventListener("input", updateTimeLabels);
    dom.controls.incrementSlider.addEventListener("input", updateTimeLabels);

    dom.controls.levelSlider.value = localStorage.getItem("level") || 4;
    dom.controls.levelLabel.textContent = levelLabels[dom.controls.levelSlider.value];

    dom.controls.levelSlider.addEventListener("input", () => {
        dom.controls.levelLabel.textContent = levelLabels[dom.controls.levelSlider.value];
        localStorage.setItem("level", dom.controls.levelSlider.value);
    });
}

function createBoard() {
    dom.board.innerHTML = "";

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
            dom.board.appendChild(cell);
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
                toggleMorpionMode();
                break;

            case "e":
                toggleEditorMode();
                break;

            case "d":
                toggleDarkMode();
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
    dom.board.addEventListener("click", (e) => {
        const cell = e.target.closest(".cell");
        if (cell) {
            play(cell);
        }
    });

    dom.board.addEventListener("mouseover", (e) => {
        const cell = e.target.closest(".cell");
        if (cell && !state.editorMode) {
            showPreview(cell);
        }
    });

    dom.board.addEventListener("mouseout", (e) => {
        const cell = e.target.closest(".cell");
        if (cell && !state.editorMode) {
            hidePreview(cell);
        }
    });
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

    const time = TIME_PRESETS[dom.controls.timeSlider.value];
    const increment = INCREMENT_PRESETS[dom.controls.incrementSlider.value];

    const data = await api(`/new_game?level=${dom.controls.levelSlider.value}&time=${time}&increment=${increment}`, {
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
        dom.app.classList.add("finished");
        dom.controls.newGameBtn.style.display = "block";
    } else {
        dom.app.classList.remove("finished");
        dom.controls.newGameBtn.style.display = "none";
    }
}

function applyServerState(data) {
    state.board = data.board;
    state.lastMove = data.lastMove;
    state.winningTiles = data.winningTiles;

    state.remainingTimes = [...data.times.times];
    state.increments = [...data.times.increments];
    state.clockPly = data.clockPly;
    state.currentPlayer = data.currentPlayer;
    state.finished = data.finished;
    state.winner = data.winner;

    state.lastUpdate = Date.now();
}

function updateTimeLabels() {
    localStorage.setItem("time", dom.controls.timeSlider.value);
    localStorage.setItem("increment", dom.controls.incrementSlider.value);

    const time = TIME_PRESETS[dom.controls.timeSlider.value];
    const increment = INCREMENT_PRESETS[dom.controls.incrementSlider.value];

    dom.controls.timeLabel.textContent = formatTime(time);
    dom.controls.incrementLabel.textContent = formatTime(increment);
}

function formatTime(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        return `${Math.floor(seconds / 60)}m`;
    } else {
        return `${Math.floor(seconds / 3600)}h`;
    }
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

            cell.classList.toggle("occupied", v !== 0);
        }
    }
}

function renderPlayers() {
    dom.players.black.app.classList.toggle("active", state.currentPlayer === 0);
    dom.players.white.app.classList.toggle("active", state.currentPlayer === 1);
}

function renderNicknames() {
    const b = state.players[0];
    const w = state.players[1];

    document.title = `Game ${b.nickname} - ${w.nickname}`;

    dom.players.black.name.querySelector(".player-name-text").textContent = b.nickname;
    dom.players.black.name.querySelector(".bot-label").classList.toggle("bot-hidden", !b.isBot);

    dom.players.white.name.querySelector(".player-name-text").textContent = w.nickname;
    dom.players.white.name.querySelector(".bot-label").classList.toggle("bot-hidden", !w.isBot);

    state.localPlayerIndex = b.isBot ? 1 : 0;
}

function renderClocks() {
    updateClockDisplay(dom.players.black.clock, state.remainingTimes[0]);
    updateClockDisplay(dom.players.white.clock, state.remainingTimes[1]);

    dom.players.black.clock.classList.toggle("low-time", state.remainingTimes[0] < 10);
    dom.players.white.clock.classList.toggle("low-time", state.remainingTimes[1] < 10);

    dom.players.black.clock.classList.toggle("active-clock", state.currentPlayer === 0);
    dom.players.white.clock.classList.toggle("active-clock", state.currentPlayer === 1);
}

function renderEndGame() {
    if (!state.finished) {
        startClock();
        return;
    }

    stopClock();
    dom.app.classList.add("finished");
    dom.controls.newGameBtn.style.display = "block";

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

function toggleMorpionMode() {
    const isMorpionMode = dom.app.classList.toggle("morpion-mode");
    localStorage.setItem("morpionMode", isMorpionMode);
}

function toggleDarkMode() {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("darkMode", isDark);
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
        dom.app.classList.add("editor-mode");
    } else {
        state.editorBoard = null;
        dom.app.classList.remove("editor-mode");
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
            time: TIME_PRESETS[dom.controls.timeSlider.value],
            increment: INCREMENT_PRESETS[dom.controls.incrementSlider.value],
            level: dom.controls.levelSlider.value,
        })
    });

    state.editorMode = false;
    state.editorBoard = null;
    dom.app.classList.remove("editor-mode");

    state.gameId = data.gid;
    state.players = data.players;

    renderNicknames();
    update();
}

document.addEventListener("DOMContentLoaded", init);
