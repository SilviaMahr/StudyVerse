document.addEventListener("DOMContentLoaded", function () {
    const textarea = document.querySelector(".chat-input");

    if (!textarea) return;

    textarea.addEventListener("input", () => {
        // Höhe kurz auf "auto" setzen, um richtige Scrollhöhe zu messen
        textarea.style.height = "auto";

        const maxHeight = parseFloat(getComputedStyle(textarea).lineHeight) * 5; // 5 Zeilen
        const newHeight = Math.min(textarea.scrollHeight, maxHeight);

        textarea.style.height = newHeight + "px";
    });
});