/*function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('toggleIcon');

    if (!sidebar || !icon) {
        console.error("Sidebar oder Icon nicht gefunden!");
        return;
    }

    sidebar.classList.toggle('collapsed');

    if (main) {
        main.classList.toggle('sidebar-collapsed', sidebar.classList.contains('collapsed'));
    }

    if (sidebar.classList.contains('collapsed')) {
        icon.src = "../assets/openSidebarIcon.png";
        icon.alt = "Sidebar öffnen";
    } else {
        icon.src = "../assets/closeSidebarIcon.png";
        icon.alt = "Sidebar schließen";
    }
}
*/

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('toggleIcon');
    const body = document.body;

    if (!sidebar || !icon) {
        console.error("Sidebar oder Icon nicht gefunden!");
        return;
    }

    sidebar.classList.toggle('collapsed');
    body.classList.toggle('sidebar-collapsed', sidebar.classList.contains('collapsed'));

    if (sidebar.classList.contains('collapsed')) {
        icon.src = "../assets/openSidebarIcon.png";
        icon.alt = "Sidebar öffnen";
    } else {
        icon.src = "../assets/closeSidebarIcon.png";
        icon.alt = "Sidebar schließen";
    }
}

