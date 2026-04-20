let board = document.getElementById("board");

let game_id = 0;
let hasStarted = false;
let finished = false;

let display_times = [60, 60];
let current_player = 0;
let last_update = Date.now();

let clockInterval = null;

// Create board
for (let i = 0; i < 64; i++) {
    let cell = document.createElement("div");
    cell.className = "cell";
    cell.onclick = () => play(i);
    board.appendChild(cell);
}

init();

function renderBoard(board) {
    let cells = document.getElementsByClassName("cell");
    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 8; j++) {
            let val = board[i][j];
            cells[i * 8 + j].innerText =
                val === 1 ? "X" :
                val === 2 ? "O" : "";
        }
    }
}

function renderClocks() {
    document.getElementById("t1").innerText = Math.max(0, display_times[0]).toFixed(1);
    document.getElementById("t2").innerText = Math.max(0, display_times[1]).toFixed(1);
}

function stopClock() {
    if (clockInterval !== null) {
        clearInterval(clockInterval);
        clockInterval = null;
    }
}

function startClock() {
    stopClock();

    clockInterval = setInterval(() => {
        if (finished) return;

        const now = Date.now();
        const dt = (now - last_update) / 1000;
        last_update = now;

        display_times[current_player] -= dt;
        renderClocks();

        if (display_times[current_player] < 0 && !finished) {
            finished = true;

            fetch(`/check_timeout/${game_id}`, { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    update(data);
                });
        }
    }, 1000);
}

function update(data) {
    display_times = [...data.time];
    current_player = data.player;
    hasStarted = data.started;
    finished = data.finished;
    last_update = Date.now();

    renderBoard(data.board);
    renderClocks();

    if (hasStarted) {
        startClock();
    } else {
        stopClock();
    }

    if (finished) {
        stopClock();
        setTimeout(() => {
            if (data.winner === null) {
                alert("Match nul !");
            } else {
                alert("Joueur " + (data.winner + 1) + " gagne !");
            }
        }, 10);
    }
}

async function init() {
    const res = await fetch("/new_game");
    const data = await res.json();
    game_id = data.game_id;
    update(data);
}

async function play(index) {
    if (finished) return;

    const i = Math.floor(index / 8);
    const j = index % 8;

    const res = await fetch(`/move/${game_id}?i=${i}&j=${j}`, { method: "POST" });
    const data = await res.json();

    update(data);
}

async function resetGame() {
    stopClock();

    const res = await fetch("/new_game");
    const data = await res.json();

    game_id = data.game_id;
    hasStarted = false;
    finished = false;

    update(data);
}
