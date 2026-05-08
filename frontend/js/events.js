import { dom } from "./dom.js";
import {
    newGame,
    playCell,
    showPreview,
    hidePreview,
    cycleMarker,
    clearAllMarkers,
    toggleMirrorHorizontal,
    cycleRotation,
    toggleEditorMode,
    toggleEditorPlayer,
    clearEditorBoard,
    swapEditorColors,
    submitEditorBoard,
} from "./actions.js";
import { cycleTheme, toggleMorpionMode } from "./preferences.js";
import { state } from "./state.js";

export function initEvents() {
    initKeyboard();
    initBoardEvents();

    dom.controls.newGameBtn.addEventListener("click", newGame);
}

function initKeyboard() {
    document.addEventListener("keydown", async (e) => {
        const tag = document.activeElement.tagName.toLowerCase();

        if (tag === "input" || tag === "textarea") {
            return;
        }

        switch (e.key.toLowerCase()) {
            case "m":
                toggleMorpionMode();
                break;

            case "e":
                toggleEditorMode();
                break;

            case "f":
                toggleMirrorHorizontal();
                break;

            case "r":
                cycleRotation();
                break;

            case "d":
                cycleTheme(e.shiftKey);
                break;

            case "c":
                clearEditorBoard();
                break;

            case "s":
                swapEditorColors();
                break;

            case " ":
                e.preventDefault();
                toggleEditorPlayer();
                break;

            case "enter":
                if (state.editorMode) {
                    await submitEditorBoard();
                } else if (state.finished) {
                    await newGame();
                }
                break;
        }
    });
}

function initBoardEvents() {
    dom.board.addEventListener("click", async (e) => {
        const cell = e.target.closest(".cell");
        if (!cell) {
            return;
        }

        await playCell(cell);
    });

    dom.board.addEventListener("mousedown", (e) => {
        if (e.button !== 1) {
            return;
        }

        e.preventDefault();

        clearAllMarkers();
    })

    dom.board.addEventListener("mouseover", (e) => {
        const cell = e.target.closest(".cell");
        if (!cell || state.editorMode) {
            return;
        }

        state.hoveredCell = cell;
        showPreview(cell);
    });

    dom.board.addEventListener("mouseout", (e) => {
        const cell = e.target.closest(".cell");
        if (!cell || state.editorMode) {
            return;
        }

        state.hoveredCell = null;
        hidePreview(cell);
    });

    dom.board.addEventListener("contextmenu", (e) => {
        e.preventDefault();

        const cell = e.target.closest(".cell");
        if (!cell) {
            return;
        }

        cycleMarker(cell, e.shiftKey);
    });
}
