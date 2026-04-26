const board = document.getElementById("board")
const btn = document.getElementById("new-game-btn");

let gid = null;
let players = null;

let displayTimes = [0, 0];
let increments = [0, 0];
let clockPly = 0;
let currentPlayer = 0;
let lastMove = null;
let lastBoard = null;
let winningTiles = [];
let lastUpdate = Date.now();
let clockInterval = null;
let finished = false;

createBoard()

function createBoard() {
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cell = document.createElement("div");

            cell.classList.add("cell");

            if ((row + col) % 2 === 0) {
                cell.classList.add("light");
            } else {
                cell.classList.add("dark");
            }

            cell.dataset.row = row;
            cell.dataset.col = col;
            cell.dataset.index = row * 8 + col;

            cell.onclick = () => play(row, col);

            board.appendChild(cell);
        }
    }
}

async function newGame() {
    if (clockInterval) clearInterval(clockInterval);
    btn.style.display = "none";

    const res = await fetch("/new_game", { method: "POST" });
    const data = await res.json();

    gid = data.gid;
    players = data.players;

    renderNicknames();
    update();
}

async function play(i, j) {
    if (lastBoard[i][j] !== 0 || finished || !lastBoard) return;

    lastBoard[i][j] = currentPlayer + 1;
    lastMove = [i, j];
    displayTimes[currentPlayer] += increments[currentPlayer]
    currentPlayer = 1 - currentPlayer;
    lastUpdate = Date.now();
    renderBoard({
        gid: gid,
        players: players,
        board: lastBoard,
        lastMove: lastMove,
        winningTiles: [],
        times: { server_time: Date.now(), times: displayTimes, increments: increments },
        clockPly: clockPly,
        currentPlayer: currentPlayer,
        finished: false,
        winner: null,
    });
    renderClocks();

    await fetch(`/move?gid=${gid}&i=${i}&j=${j}`, { method: "POST" });

    update();
}

async function checkTimeout() {
    if (finished) return;

    if (displayTimes[currentPlayer] < 0) {
        displayTimes[currentPlayer] = 0;

        await fetch(`/flag?gid=${gid}`, { method: "POST" });

        update();
    }
}

async function update() {
    const res = await fetch(`/state?gid=${gid}`, { method: "GET" });
    const data = await res.json();

    renderBoard(data);
    renderPlayers();
}

function renderBoard(data) {
    lastBoard = data.board;
    lastMove = data.lastMove;
    winningTiles = data.winningTiles

    const cells = document.getElementsByClassName("cell");

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cell = cells[row * 8 + col];

            cell.classList.remove("last-move");

            if (lastMove !== null) {
                if (lastMove[0] === row && lastMove[1] === col) {
                    cell.classList.add("last-move");
                }
            }

            cell.classList.remove("win")

            if (winningTiles.some(([x, y]) => x === row && y === col)) {
                cell.classList.add("win");
            }

            cell.innerHTML = "";

            if (data.board[row][col] === 1) {
                cell.innerHTML = '<div class="stone black"></div>';
            } else if (data.board[row][col] === 2) {
                cell.innerHTML = '<div class="stone white"></div>';
            }
        }
    }

    displayTimes = [...data.times["times"]];
    increments = [...data.times["increments"]];
    clockPly = data.clockPly;
    currentPlayer = data.currentPlayer;
    finished = data.finished;
    lastUpdate = Date.now();

    renderClocks();

    if (!finished) {
        startClock()
    } else {
        setTimeout(() => {
            if (data.winner === 0) {
                alert("Black wins !");
            } else if (data.winner === 1) {
                alert("White wins !");
            } else {
                alert("Draw.");
            }
        }, 50);
        btn.style.display = "block";
    }
}

function renderPlayers() {
    document.getElementById("player-black").classList.toggle(
        "active", currentPlayer === 0
    );

    document.getElementById("player-white").classList.toggle(
        "active", currentPlayer === 1
    );
}

function renderNicknames() {
    bNN = players[0].nickname;
    wNN = players[1].nickname;
    blackStone = ' <span class="stone label black"></span>'
    whiteStone = ' <span class="stone label white"></span>'
    botSpan = ' <span class="bot-label">BOT</span>';

    document.title = `Game ${bNN} - ${wNN}`;

    blackNickname = document.getElementById("player-name-black");
    blackNickname.innerHTML = blackStone + bNN + (players[0].isBot ? botSpan : "");

    whiteNickname = document.getElementById("player-name-white");
    whiteNickname.innerHTML = whiteStone + wNN + (players[1].isBot ? botSpan : "");

}

function renderClocks() {
    cBlack = document.getElementById("clock-black")
    cWhite = document.getElementById("clock-white")

    updateClockDisplay(cBlack, displayTimes[0])
    updateClockDisplay(cWhite, displayTimes[1])

    cBlack.classList.toggle("low-time", (displayTimes[0] < 10));
    cWhite.classList.toggle("low-time", (displayTimes[1] < 10));

    cBlack.classList.toggle("active-clock", currentPlayer === 0);
    cWhite.classList.toggle("active-clock", currentPlayer === 1);
}

function updateClockDisplay(el, t) {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    const cs = Math.floor((t * 100) % 100);

    el.querySelector(".minutes").textContent = m.toString().padStart(2, "0")
    el.querySelector(".seconds").textContent = s.toString().padStart(2, "0")
    el.querySelector(".centi-seconds").textContent = (t >= 20) ? "" : cs.toString().padStart(2, "0");
}

function startClock() {
    if (clockPly < 2) return;

    if (clockInterval) clearInterval(clockInterval);

    clockInterval = setInterval(() => {
        if (finished) return;

        const now = Date.now();
        const dt = (now - lastUpdate) / 1000;

        lastUpdate = now;

        displayTimes[currentPlayer] -= dt

        checkTimeout();
        renderClocks();
    }, 73);
}

document.addEventListener("keydown", (e) => {
    const tag = document.activeElement.tagName;

    if (tag === "INPUT" || tag === "TEXTAREA") return;

    if (e.key === "Enter" && finished) {
        newGame();
    }
});

newGame();
