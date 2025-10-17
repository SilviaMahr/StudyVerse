function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('toggleIcon');
    const main = document.querySelector('.main-content');

    if (!sidebar || !icon) {
        console.error("Sidebar oder Icon nicht gefunden!");
        return;
    }

    // Sidebar ein-/ausklappen
    sidebar.classList.toggle('collapsed');

    // Hauptbereich anpassen (optional)
    if (main) {
        main.classList.toggle('sidebar-collapsed', sidebar.classList.contains('collapsed'));
    }

    // Icon ändern
    if (sidebar.classList.contains('collapsed')) {
        icon.src = "../assets/openSidebarIcon.png";   // Pfeil nach rechts
        icon.alt = "Sidebar öffnen";
    } else {
        icon.src = "../assets/closeSidebarIcon.png";  // Pfeil nach links
        icon.alt = "Sidebar schließen";
    }
}

console.log("✅ Studyverse.js geladen!");
