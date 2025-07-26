document.addEventListener('DOMContentLoaded', function () {
    // --- SETUP & STATE ---
    const mapContainer = document.getElementById('planner-map');
    const map = L.map(mapContainer).setView([52.48, -1.9], 8);
    
    let waypoints = [];
    let markers = [];
    let currentRouteCoords = []; // This will store {lat, lng, ele}
    const routeLayer = L.layerGroup().addTo(map);
    const markerLayer = L.layerGroup().addTo(map);
    let justFinishedDrag = false;

    // --- UI ELEMENTS ---
    const undoBtn = document.getElementById('undo-btn');
    const clearBtn = document.getElementById('clear-btn');
    const saveForm = document.getElementById('save-form');

    L.tileLayer(`https://{s}.tile.jawg.io/jawg-streets/{z}/{x}/{y}{r}.png?access-token=YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p`, {
        attribution: '<a href="https://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // --- Self-contained GPX building function ---
    function buildGpxString(points, title) {
        let gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="The Ride Archive Planner" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata><name>${title}</name></metadata>
  <trk><name>${title}</name><trkseg>`;
        points.forEach(p => {
            gpx += `
      <trkpt lat="${p.lat}" lon="${p.lng}"><ele>${p.ele || 0}</ele></trkpt>`;
        });
        gpx += `
    </trkseg></trk></gpx>`;
        return gpx;
    }

    // --- ELEVATION FUNCTION (calls our own backend) ---
    function fetchElevation(coordinates) {
        // Correctly formats coordinates as lat,lng
        const locations = coordinates.map(c => `${c.lat},${c.lng}`).join('|');
        
        fetch('/api/elevation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ locations: locations })
        })
        .then(response => {
            if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); }
            return response.json();
        })
        .then(elevationData => {
            let totalAscent = 0;
            if (Array.isArray(elevationData)) {
                for (let i = 0; i < elevationData.length; i++) {
                    const elevation = elevationData[i].elevation;
                    if (i < coordinates.length) {
                        coordinates[i].ele = elevation; // Add elevation to our main coordinate object
                    }
                    if (i > 0 && elevation > elevationData[i - 1].elevation) {
                        totalAscent += elevation - elevationData[i - 1].elevation;
                    }
                }
                document.getElementById('elevation').textContent = Math.round(totalAscent);
            }
        })
        .catch(error => console.error('Error fetching elevation:', error));
    }
    
    // --- ROUTING FUNCTION (gets the path) ---
    function fetchAndDrawRoute() {
        if (waypoints.length < 2) {
            currentRouteCoords = []; 
            routeLayer.clearLayers();
            document.getElementById('distance').textContent = '0.0';
            document.getElementById('elevation').textContent = '0';
            return;
        }
        const waypointsStr = waypoints.map(wp => `${wp.lng},${wp.lat}`).join(';');
        const url = `https://api.jawg.io/routing/route/v1/cycling/${waypointsStr}?overview=full&access-token=YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.routes && data.routes.length) {
                    const route = data.routes[0];
                    const decodedCoords = polyline.decode(route.geometry);
                    const coordinates = decodedCoords.map(c => L.latLng(c[0], c[1]));
                    currentRouteCoords = coordinates; 
                    routeLayer.clearLayers();
                    L.polyline(coordinates, { color: '#f3ba19', weight: 5, opacity: 0.8 }).addTo(routeLayer);
                    const distanceInKm = (route.distance / 1000).toFixed(2);
                    document.getElementById('distance').textContent = distanceInKm;
                    // Make the second call to our proxy to get elevation
                    fetchElevation(coordinates);
                }
            })
            .catch(error => { console.error('Error fetching route:', error); });
    }

    // --- SAVE FORM LISTENER ---
    saveForm.addEventListener('submit', function(event) {
        event.preventDefault(); 
        const title = document.getElementById('route-title').value;
        const description = document.getElementById('route-description').value;
        if (currentRouteCoords.length < 2) {
            alert("Please create a route on the map before saving.");
            return;
        }
        const gpxString = buildGpxString(currentRouteCoords, title);
        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('gpx_data', gpxString);
        fetch('/api/planner/save', {
            method: 'POST',
            body: formData 
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = `/publish/${data.draft_id}`;
            } else {
                alert("Error saving route: " + (data.error || "Unknown error"));
            }
        })
        .catch(error => {
            console.error('Error saving route:', error);
            alert("An error occurred while saving the route.");
        });
    });

    // --- Other Listeners and Functions ---
    function createAndBindMarker(latlng, index) {
        const marker = L.circleMarker(latlng, { radius: 6, color: '#3a501a', fillColor: '#FAF7F2', fillOpacity: 1 }).addTo(markerLayer);
        markers.push(marker);
        marker.on('mousedown', function (e) {
            map.dragging.disable();
            draggedMarker = { marker: markers[index], index: index };
            map.on('mousemove', onMouseMove);
            map.on('mouseup', onMouseUp);
        });
    }
    undoBtn.addEventListener('click', function() {
        if (waypoints.length > 0) {
            waypoints.pop();
            const lastMarker = markers.pop();
            if (lastMarker) { markerLayer.removeLayer(lastMarker); }
            fetchAndDrawRoute();
        }
    });
    clearBtn.addEventListener('click', function() {
        waypoints = [];
        markers = [];
        markerLayer.clearLayers();
        routeLayer.clearLayers();
        fetchAndDrawRoute();
    });
    let draggedMarker = null;
    function onMouseMove(e) { if (draggedMarker) { draggedMarker.marker.setLatLng(e.latlng); } }
    function onMouseUp(e) {
        if (draggedMarker) {
            waypoints[draggedMarker.index] = draggedMarker.marker.getLatLng();
            fetchAndDrawRoute();
            map.dragging.enable();
            map.off('mousemove', onMouseMove);
            map.off('mouseup', onMouseUp);
            draggedMarker = null;
            justFinishedDrag = true;
        }
    }
    map.on('click', function (e) {
        if (justFinishedDrag) {
            justFinishedDrag = false;
            return;
        }
        waypoints.push(e.latlng);
        const newIndex = waypoints.length - 1;
        createAndBindMarker(e.latlng, newIndex);
        fetchAndDrawRoute();
    });
    const resizeObserver = new ResizeObserver(() => { map.invalidateSize(); });
    resizeObserver.observe(mapContainer);
});