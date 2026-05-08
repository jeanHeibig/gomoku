import { state } from "./state.js";
import { api } from "./api.js";
import { renderClocks } from "./render.js";

let onFlagged = null;
let flagInProgress = false;

export function configureClock({ onFlagged: callback }) {
    onFlagged = callback;
}

export function startClock() {
    if (state.clockPly < 2 || state.finished) {
        return;
    }

    stopClock();

    state.clockInterval = setInterval(tickClock, 73);
}

export function stopClock() {
    if (state.clockInterval) {
        clearInterval(state.clockInterval);
        state.clockInterval = null;
    }
}

export function syncClockState() {
    if (state.finished) {
        stopClock();
    } else {
        startClock();
    }
}

async function tickClock() {
    if (state.finished) {
        stopClock();
        return;
    }

    const now = Date.now();
    const dt = (now - state.lastUpdate) / 1000;

    state.lastUpdate = now;
    state.remainingTimes[state.currentPlayer] -= dt;

    if (state.remainingTimes[state.currentPlayer] <= 0) {
        state.remainingTimes[state.currentPlayer] = 0;
        await flagCurrentPlayer();
    }

    renderClocks();
}

async function flagCurrentPlayer() {
    if (flagInProgress || state.finished) {
        return;
    }

    flagInProgress = true;

    await api(`/flag?gid=${state.gameId}`, {
        method: 'POST',
    });

    if (onFlagged) {
        await onFlagged();
    }

    flagInProgress = false;
}
