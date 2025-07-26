// app/static/js/location_picker.js

// Use the most patient event: fires after all content (CSS, images) is loaded.
window.addEventListener('load', function () {
    const mapContainer = document.getElementById('location-picker-map');
    const coordinatesInput = document.getElementById('coordinates');

    if (!mapContainer || !coordinatesInput) {
        console.error("Map elements missing.");
        return;
    }

    const jawgAccessToken = mapContainer.dataset.jawgToken;
    if (!jawgAccessToken) {
        mapContainer.innerHTML = '<p class="text-red-500 font-semibold">Error: Access Token is missing.</p>';
        return;
    }
    
    // --- Determine Initial View ---
    let initialCoords = [54.5, -2.5]; // UK default
    let initialZoom = 6;
    const existingCoords = coordinatesInput.value;

    if (existingCoords) {
        // Parse lon, lat from the input field
        const parts = existingCoords.split(',').map(coord => parseFloat(coord.trim()));
        if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
            // Leaflet uses [lat, lon], but our input is [lon, lat]
            initialCoords = [parts[1], parts[0]]; 
            initialZoom = 14; // Zoom in closer for existing hotels
        }
    }

    // --- Initialize Map ---
    const map = L.map('location-picker-map').setView(initialCoords, initialZoom);

    L.tileLayer(
        `https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
            attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            minZoom: 0,
            maxZoom: 22
        }
    ).addTo(map);
    
    // A final resize check
    requestAnimationFrame(() => map.invalidateSize());

    // --- Initialize Marker ---
    let marker = L.marker(initialCoords, {
        draggable: true,
        icon: L.icon({
            iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
            shadowSize: [41, 41]
        })
    }).addTo(map);

    // --- Update Function ---
    function updateCoordinates(latlng) {
        // Store as lon, lat
        const lon = latlng.lng.toFixed(6);
        const lat = latlng.lat.toFixed(6);
        coordinatesInput.value = `${lon}, ${lat}`;
    }

    // --- Event Listeners ---
    marker.on('dragend', (e) => updateCoordinates(e.target.getLatLng()));
    map.on('click', (e) => {
        marker.setLatLng(e.latlng);
        updateCoordinates(e.latlng);
    });
});
