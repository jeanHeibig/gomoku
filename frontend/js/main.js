import { loadSystemPreferences, initSliders } from "./preferences.js";
import { createBoard } from "./render.js";
import { initEvents } from "./events.js";
import { newGame, updateFromServer } from "./actions.js";
import { configureClock } from "./clock.js";

function init() {
    loadSystemPreferences();
    initSliders();
    createBoard();
    initEvents();

    configureClock({
        onFlagged: updateFromServer,
    });

    newGame();
}

document.addEventListener("DOMContentLoaded", init);
