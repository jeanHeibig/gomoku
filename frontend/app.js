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

resetGame();

// const params = new URLSearchParams(window.location.search);
// const name = params.get("name") || "guest";
// let ws = new WebSocket(`ws://localhost:8000/ws/0?name=${name}`);

// ws.onmessage = (event) => {
//     let data = JSON.parse(event.data);
//     update(data);
// };

// function renderBoard(board) {
//     let cells = document.getElementsByClassName("cell");

//     for (let i = 0; i < 8; i++) {
//         for (let j = 0; j < 8; j++) {
//             let val = board[i][j];
//             cells[i * 8 + j].innerText =
//                 val === 1 ? "X" :
//                 val === 2 ? "O" : "";
//         }
//     }
// }

function renderBoard(board) {
    let cells = document.getElementsByClassName("cell");

    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 8; j++) {
            let cell = cells[i * 8 + j];

            if ((i + j) % 2 === 0) {
                cell.classList.add("light");
                cell.classList.remove("dark");
            } else {
                cell.classList.add("dark");
                cell.classList.remove("light");
            }

            // pièces
            cell.innerHTML = "";

            if (board[i][j] === 1) {
                cell.innerHTML = '<div class="piece black"></div>';
            } else if (board[i][j] === 2) {
                cell.innerHTML = '<div class="piece white"></div>';
            }
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

    document.getElementById("p1").innerText =
        "Joueur 1: " + (data.player_names[0] || "-");
    document.getElementById("p2").innerText =
        "Joueur 2: " + (data.player_names[1] || "-");

    if (!finished) {
        document.getElementById("turn").innerText =
            "Au tour de : Joueur " + (data.player + 1);
    } else {
        document.getElementById("turn").innerText = "";
    }

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
                showMessage("Match nul !");
            } else {
                showMessage("Joueur " + (data.winner + 1) + " gagne !");
            }
        }, 10);
    }
}

async function play(index) {
    if (finished) return;

    const i = Math.floor(index / 8);
    const j = index % 8;

    const res = await fetch(`/move/${game_id}?i=${i}&j=${j}`, { method: "POST" });
    const data = await res.json();

    update(data);
}

function showMessage(msg) {
    document.getElementById("message").innerText = msg;
}

function clearMessage(msg) {
    document.getElementById("message").innerText = "";
}

// function play(index) {
//     if (finished) return;

//     const i = Math.floor(index / 8);
//     const j = index % 8;

//     ws.send(JSON.stringify({
//         type: "move",
//         i: i,
//         j: j,
//     }));
// }

// async function init() {
//     const res = await fetch("/new_game?time_control=120&increment=2");
//     const data = await res.json();
//     game_id = data.game_id;
//     update(data);
// }

function getTimeSettings() {
    const tcInput = document.getElementById("time_control");
    const incInput = document.getElementById("increment");

    let time_control = 60;
    let increment = 0;

    if (tcInput !== null) {
        time_control = parseInt(tcInput.value);
    }

    if (incInput !== null) {
        increment = parseInt(incInput.value);
    }

    return { time_control, increment };
}

async function resetGame() {
    stopClock();
    clearMessage();

    const { time_control, increment } = getTimeSettings();

    const res = await fetch(`/new_game?time_control=${time_control}&increment=${increment}`);
    const data = await res.json();

    game_id = data.game_id;
    hasStarted = false;
    finished = false;

    update(data);
}
