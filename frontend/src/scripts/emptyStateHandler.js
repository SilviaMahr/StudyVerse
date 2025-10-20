document.addEventListener("DOMContentLoaded", function () {
    const chatHistory = document.querySelector(".chat-history");
    const mainContent = document.querySelector(".main-content");

    function updateEmptyState() {
        if (chatHistory && mainContent) {
            const hasMessages = chatHistory.children.length > 0;
            mainContent.classList.toggle("empty", !hasMessages);
        }
    }

    updateEmptyState();

    const observer = new MutationObserver(updateEmptyState);
    if (chatHistory) {
        observer.observe(chatHistory, { childList: true });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const header = document.getElementById("HeaderJKU");
    const main = document.querySelector(".main-content");
    const chatHistory = document.querySelector(".chat-history");

    function updateLayoutHeight() {
        if (header && main) {
            const headerHeight = header.offsetHeight;
            document.documentElement.style.setProperty("--header-height", `${headerHeight}px`);
            document.body.style.height = `${window.innerHeight}px`;
        }
    }

    function updateEmptyState() {
        if (chatHistory && main) {
            const hasMessages = chatHistory.children.length > 0;
            main.classList.toggle("empty", !hasMessages);
            document.body.classList.toggle("empty-state", !hasMessages);
        }
    }

    updateLayoutHeight();
    updateEmptyState();

    window.addEventListener("resize", updateLayoutHeight);
    if (chatHistory) {
        const observer = new MutationObserver(updateEmptyState);
        observer.observe(chatHistory, { childList: true });
    }
});
