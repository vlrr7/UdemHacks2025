// static/gps.js
function updateGeolocation() {
    if (!navigator.geolocation) {
        console.error("La géolocalisation n'est pas supportée par ce navigateur.");
        return;
    }
    navigator.geolocation.watchPosition(
        function(position) {
            const params = new URLSearchParams(window.location.search);
            params.set('lat', position.coords.latitude);
            params.set('lon', position.coords.longitude);
            window.history.replaceState({}, '', `${location.pathname}?${params}`);
            console.log("Position mise à jour:", position.coords);
        },
        function(error) {
            console.error("Erreur de géolocalisation:", error);
        },
        {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        }
    );
}
document.addEventListener('DOMContentLoaded', updateGeolocation);
