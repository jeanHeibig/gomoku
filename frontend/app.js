const board = document.getElementById("board")
const btn = document.getElementById("new-game-btn");

let gid = null

let displayTimes = [0, 0];
let clockPly = 0;
let currentPlayer = 0;
let lastBoard = null;
let lastUpdate = Date.now();
let clockInterval = null;
let finished = false;

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

async function newGame() {
    if (clockInterval) clearInterval(clockInterval);
    btn.style.display = "none";

    const res = await fetch("/new_game", { method: "GET" });
    const data = await res.json();

    gid = data.gid;
    players = data.players;

    renderNicknames();
    update()
}

async function play(i, j) {
    if (lastBoard[i][j] !== 0)  {
        console.log("Illegal move.");
        return;
    }

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

    const cells = document.getElementsByClassName("cell");

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const cell = cells[row * 8 + col];

            cell.innerHTML = "";

            if (data.board[row][col] === 1) {
                cell.innerHTML = '<div class="stone black"></div>';
            } else if (data.board[row][col] === 2) {
                cell.innerHTML = '<div class="stone white"></div>';
            }
        }
    }

    displayTimes = [...data.times["times"]];
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
    botSpan = ' <span class="bot-label">BOT</span>';

    document.title = `Game ${bNN} - ${wNN}`;

    blackNickname = document.getElementById("player-name-black");
    blackNickname.innerHTML = `${bNN} (Black)` + (players[0].isBot ? botSpan : "");

    whiteNickname = document.getElementById("player-name-white");
    whiteNickname.innerHTML = `${wNN} (White)` + (players[1].isBot ? botSpan : "");

}

function renderClocks() {
    cBlack = document.getElementById("clock-black")
    cWhite = document.getElementById("clock-white")
    cBlack.innerHTML = formatTime(displayTimes[0]);
    cWhite.innerHTML = formatTime(displayTimes[1]);

    cBlack.classList.toggle("low-time", (displayTimes[0] < 10));
    cWhite.classList.toggle("low-time", (displayTimes[1] < 10));

    cBlack.classList.toggle("active-clock", currentPlayer === 0);
    cWhite.classList.toggle("active-clock", currentPlayer === 1);
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
    }, 100);
}

function formatTime(t) {
    if (t >= 20) {
        const m = Math.floor(t / 60);
        const s = Math.floor(t % 60);

        return `${m.toString().padStart(2, "0")}<span class="colon">:</span>${s.toString().padStart(2, "0")}`;
    } else {
        const s = Math.floor(t);
        const cs = Math.floor((t - s) * 100);

        return `${s.toString().padStart(2, "0")}<span class="centi-seconds">${cs.toString().padStart(2, "0")}</span>`;
    }
}

// setInterval(update, 2000);

newGame();
