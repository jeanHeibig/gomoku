import { dom } from "./dom.js";
import { state } from "./state.js";
import { stopClock } from "./clock.js";

export function handleGameEnd() {
    stopClock();

    const isMorpionMode = dom.app.classList.contains("morpion-mode");

    setTimeout(() => {
        alert(
            state.winner === 0 ? (isMorpionMode ? "X wins!" : "Black wins!") :
            state.winner === 1 ? (isMorpionMode ? "O wins!" : "White wins!") :
            "Draw."
        );
    }, 50);
}
