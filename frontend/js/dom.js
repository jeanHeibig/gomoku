export const dom = {
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
};
