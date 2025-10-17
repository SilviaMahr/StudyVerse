const body = document.body;

const lightModeBtn = document.getElementById("lightModeBtn");
const darkModeBtn = document.getElementById("darkModeBtn");

const savedMode = localStorage.getItem("mode");
if (savedMode === "dark") {
    body.classList.add("dark-mode");
} else {
    body.classList.remove("dark-mode");
}

updateModeIcons();

darkModeBtn.addEventListener("click", () => {
    body.classList.add("dark-mode");
    localStorage.setItem("mode", "dark");
    updateModeIcons();
});

lightModeBtn.addEventListener("click", () => {
    body.classList.remove("dark-mode");
    localStorage.setItem("mode", "day");
    updateModeIcons();
});

function updateModeIcons() {
    const assetPath = getAssetPath();

    if (body.classList.contains("dark-mode")) {
        darkModeBtn.src = assetPath + "moonFull.png";
        lightModeBtn.src = assetPath + "sunEmpty.png";
    } else {
        lightModeBtn.src = assetPath + "sunFull.png";
        darkModeBtn.src = assetPath + "moonEmpty.png";
    }
}

function getAssetPath() {
    const path = window.location.pathname;

    if (path.includes("/src/pages/")) {
        return "../../assets/";
    } else if (path.includes("/public/")) {
        return "../assets/";
    } else {
        return "./assets/";
    }
}
