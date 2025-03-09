// static/gps.js
function updateLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.watchPosition(
            position => {
                const params = new URLSearchParams(window.location.search);
                params.set('lat', position.coords.latitude);
                params.set('lon', position.coords.longitude);
                window.history.replaceState({}, '', `${location.pathname}?${params}`);
            },
            error => {
                console.error('Error getting location:', error);
            },
            { 
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 5000
            }
        );
    } else {
        alert("La géolocalisation n'est pas supportée par ce navigateur.");
    }
}

// Démarre la mise à jour de la position
updateLocation();