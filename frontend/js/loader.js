function load() {
    const morpion =
        localStorage.getItem("morpionMode");

    if (morpion === "false") {
        document.getElementById("app").classList.remove("morpion-mode");
    }

    const theme =
        localStorage.getItem("theme");

    if (theme) {
        document.body?.setAttribute?.(
            "data-theme",
            theme
        );
    }
}

load();
