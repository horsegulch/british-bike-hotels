// app/static/js/route_profile.js

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('route-map');
    const chartCanvas = document.getElementById('elevation-chart');

    if (!mapContainer || !chartCanvas) {
        console.error("Map or chart container not found.");
        return;
    }

    const jawgAccessToken = mapContainer.dataset.jawgToken;
    const trackPointsJson = mapContainer.dataset.trackPoints;

    if (!jawgAccessToken || !trackPointsJson) {
        if (mapContainer) mapContainer.innerHTML = '<p class="text-red-500 p-4">Map data is missing.</p>';
        return;
    }

    try {
        const trackPoints = JSON.parse(trackPointsJson);

        if (trackPoints.length === 0) {
            mapContainer.innerHTML = '<p class="text-gray-500 p-4">No track points available for this route.</p>';
            return;
        }

        // --- Initialize Map ---
        const map = L.map('route-map');
        L.tileLayer(
            `https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
                attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }
        ).addTo(map);

        const latLngs = trackPoints.map(p => [p.lat, p.lon]);
        const polyline = L.polyline(latLngs, { color: '#ef4444', weight: 4 }).addTo(map);
        map.fitBounds(polyline.getBounds().pad(0.1));

        // --- Initialize Elevation Chart ---
        const chartData = {
            labels: trackPoints.map(p => p.dist.toFixed(1)), // Distance for x-axis
            datasets: [{
                label: 'Elevation (m)',
                data: trackPoints.map(p => p.ele), // Elevation for y-axis
                borderColor: '#2c3e50',
                backgroundColor: 'rgba(44, 62, 80, 0.1)',
                fill: true,
                pointRadius: 0,
                tension: 0.1
            }]
        };

        const chartConfig = {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Distance (km)' },
                        ticks: {
                            maxTicksLimit: 10 // Limit the number of ticks to avoid clutter
                        }
                    },
                    y: {
                        title: { display: true, text: 'Elevation (m)' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        };

        new Chart(chartCanvas, chartConfig);


    } catch (error) {
        console.error("Failed to parse track points or initialize map/chart:", error);
        if (mapContainer) mapContainer.innerHTML = '<p class="text-red-500 p-4">Error loading map.</p>';
    }
});
