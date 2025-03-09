let watchId = null;

function startTracking() {
    if (!navigator.geolocation) {
        alert("La géolocalisation n'est pas supportée par ce navigateur.");
        return;
    }
    
    watchId = navigator.geolocation.watchPosition(
        position => {
            const params = new URLSearchParams(window.location.search);
            params.set('lat', position.coords.latitude);
            params.set('lon', position.coords.longitude);
            window.history.replaceState({}, '', `${location.pathname}?${params}`);
        },
        error => {
            console.error('Erreur de géolocalisation:', error);
        },
        {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        }
    );
}

document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', (event) => {
        if (event.target.id === 'demarrer-course') {
            startTracking();
        }
    });
});