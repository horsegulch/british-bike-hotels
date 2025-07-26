// app/static/js/map.js

document.addEventListener('DOMContentLoaded', function () {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error("Map container not found!");
        return;
    }

    const jawgAccessToken = mapContainer.dataset.jawgToken;
    if (!jawgAccessToken) {
        mapContainer.innerHTML = '<p class="text-red-500 p-4">Error: Map service access token is missing.</p>';
        return;
    }

    // Initialize the map
    const map = L.map('map', {
        zoomControl: false // Disable the default zoom control
    }).setView([54.5, -3.5], 6); // Centered on the UK

    // **FIX:** Create a non-conflicting global variable for the map instance.
    window.leafletMap = map;

    // Add new zoom control to the bottom right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Add Jawg map tiles
    L.tileLayer(
        `https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
            attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            minZoom: 5,
            maxZoom: 22
        }
    ).addTo(map);

    // Fetch hotel data from the API
    fetch('/api/map-data')
        .then(response => response.json())
        .then(data => {
            const hotels = data.hotels;
            if (!hotels || hotels.length === 0) {
                console.warn("No hotel data received from API.");
                return;
            }

            const markers = L.markerClusterGroup();

            hotels.forEach(hotel => {
                let iconHtml;
                if (hotel.is_featured) {
                    iconHtml = `<i class='fa-solid fa-location-dot text-amber-400'></i>`;
                } else {
                    iconHtml = `<i class='fa-solid fa-location-dot text-slate-800'></i>`;
                }

                const customIcon = L.divIcon({
                    className: 'custom-icon-only',
                    html: iconHtml,
                    iconSize: [36, 36],
                    iconAnchor: [18, 18]
                });

                const marker = L.marker([hotel.location.coordinates[1], hotel.location.coordinates[0]], {
                    icon: customIcon
                });

                marker.bindPopup(`
                    <div class="p-1 font-poppins">
                        <h3 class="font-bold text-md mb-1">${hotel.name}</h3>
                        <a href="/hotel/${hotel._id}" class="text-amber-500 hover:text-amber-600 font-semibold text-sm">View Details &rarr;</a>
                    </div>
                `);
                markers.addLayer(marker);
            });
            map.addLayer(markers);
        })
        .catch(error => {
            console.error("Error fetching map data:", error);
            mapContainer.innerHTML = '<p class="text-red-500 p-4">Could not load hotel data.</p>';
        });
});
