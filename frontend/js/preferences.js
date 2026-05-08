import { dom } from "./dom.js";
import { TIME_PRESETS, INCREMENT_PRESETS, LEVEL_LABELS, THEMES } from "./constants.js";

export function loadSystemPreferences() {
    const isMorpionMode = localStorage.getItem("morpionMode");

    if (isMorpionMode === "false") {
        dom.app.classList.remove("morpion-mode");
    }

    const theme = localStorage.getItem("theme") || "light";
    setTheme(theme);
}

export function setTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
}

export function cycleTheme(backward) {
    const current = document.body.getAttribute("data-theme") || "light";
    const current_idx = THEMES.indexOf(current);

    const nextTheme = THEMES[
        (current_idx + (backward ? THEMES.length - 1 : 1)) % THEMES.length
    ];

    setTheme(nextTheme);
}

export function toggleMorpionMode() {
    const enabled = dom.app.classList.toggle("morpion-mode");
    localStorage.setItem("morpionMode", enabled);
}

export function initSliders() {
    dom.controls.timeSlider.max = TIME_PRESETS.length - 1;
    dom.controls.incrementSlider.max = INCREMENT_PRESETS.length - 1;
    dom.controls.levelSlider.max = LEVEL_LABELS.length - 1;

    dom.controls.timeSlider.value = localStorage.getItem("time") || 6;  // defaut 5+2
    dom.controls.incrementSlider.value = localStorage.getItem("increment") || 2;
    dom.controls.levelSlider.value = localStorage.getItem("level") || 3;

    dom.controls.timeSlider.addEventListener("input", updateTimeLabel);
    dom.controls.incrementSlider.addEventListener("input", updateIncrementLabel);
    dom.controls.levelSlider.addEventListener("input", updateLevelLabel);

    updateSliders();
}

export function selectedSliders() {
    return {
        time: TIME_PRESETS[dom.controls.timeSlider.value],
        increment: INCREMENT_PRESETS[dom.controls.incrementSlider.value],
        level: dom.controls.levelSlider.value,
    }
}

function updateSliders() {
    updateTimeLabel();
    updateIncrementLabel();
    updateLevelLabel();
}

function updateTimeLabel() {
    localStorage.setItem("time", dom.controls.timeSlider.value);

    const time = TIME_PRESETS[dom.controls.timeSlider.value];

    dom.controls.timeLabel.textContent = formatTime(time);
}

function updateIncrementLabel() {
    localStorage.setItem("increment", dom.controls.incrementSlider.value);

    const increment = INCREMENT_PRESETS[dom.controls.incrementSlider.value];

    dom.controls.incrementLabel.textContent = formatTime(increment);
}

function updateLevelLabel() {
    localStorage.setItem("level", dom.controls.levelSlider.value);

    const level = LEVEL_LABELS[dom.controls.levelSlider.value];

    dom.controls.levelLabel.textContent = level;
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
