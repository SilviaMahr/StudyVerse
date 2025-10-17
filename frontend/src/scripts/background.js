function generateStars(count = 100) {
    const starfield = document.getElementById('starfield');

    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.classList.add('star');

        const size = Math.random() * 2 + 1;
        star.style.width=`${size}px`;
        star.style.height=`${size}px`;

        star.style.top = `${Math.random() * 100}%`;
        star.style.left = `${Math.random() * 100}%`;

        starfield.appendChild(star);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    generateStars(150); // Anzahl der Sterne
});

function generateRandomPlanets(count = 8) {
    const container = document.getElementById('dayUniverse');
    const planetImages = [
        'greenPlanet.png',
        'flederPlanet.png',
        'redPlanet.png',
        'yellowPlanet.png'
    ];

    for (let i = 0; i < count; i++) {
        const planet = document.createElement('img');
        planet.classList.add('planet');

        const src = planetImages[Math.floor(Math.random() * planetImages.length)];
        planet.src = `../../assets/${src}`;


        planet.style.top = `${Math.random() * 90}%`;
        planet.style.left = `${Math.random() * 90}%`;

        // Zufällige Größe
        const size = Math.random() * 40 + 40; // 40–80px
        planet.style.width = `${size}px`;
        planet.style.height = `${size}px`;

        container.appendChild(planet);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    if (!document.body.classList.contains('dark-mode')) {
        generateRandomPlanets(10);
    }
});
