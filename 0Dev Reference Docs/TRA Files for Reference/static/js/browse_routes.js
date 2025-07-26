document.addEventListener('DOMContentLoaded', () => {
    const routesTableEl = document.getElementById('routesTable');
    const routesTableBodyEl = document.getElementById('routesTableBody');
    const selectAllCheckboxEl = document.getElementById('selectAllCheckbox');
    const browseMapContainerEl = document.getElementById('browseMapContainer');
    const searchInputEl = document.getElementById('searchInput'); 
    const startLocationFilterEl = document.getElementById('startLocationFilter'); 
    const difficultySliderValueEl = document.getElementById('difficultySliderValue'); 
    const distanceSliderValueEl = document.getElementById('distanceSliderValue'); 
    const tegaSliderValueEl = document.getElementById('tegaSliderValue'); 
    const resetFiltersButtonEl = document.getElementById('resetFiltersButton'); 
    const loadingMessageEl = document.getElementById('loadingMessage');
    const errorMessageEl = document.getElementById('errorMessage');
    const noRoutesMessageEl = document.getElementById('noRoutesMessage');
    const toggleFiltersBtn = document.getElementById('toggleFiltersBtn');
    const collapsibleFilters = document.getElementById('collapsibleFilters');
    const compareBtn = document.getElementById('compareBtn');
    const modalOverlay = document.getElementById('comparisonModal');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalTableContainer = document.getElementById('modalTableContainer');
    const surfaceTypeFilterEl = document.getElementById('surfaceTypeFilter');
    const tagFilterInputEl = document.getElementById('tagFilterInput');

    let browseMapInstance = null;
    let currentMarkersLayer = null;
    let currentRouteTraceLayer = null;
    let displayedTraceRouteId = null;
    let currentSortColumnIndex = -1;
    let currentSortAscending = true;
    let allFetchedRoutes = []; 
    let selectedRouteIds = new Set();
    let radarChartInstance = null;
    let elevationChartInstance = null;

    const defaultMinDifficulty = 0, defaultMaxDifficulty = 500, difficultyStep = 5;
    const defaultMinDistance = 0, defaultMaxDistance = 500, distanceStep = 10;
    const defaultMinTEGa = 0, defaultMaxTEGa = 5000, tegaStep = 100;
    const TRACE_DISPLAY_ZOOM_THRESHOLD = 8; 

    const greenIcon = L.divIcon({
        html: `<svg viewBox="0 0 24 24" width="28px" height="28px" fill="#3a501a" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>`,
        className: 'custom-leaflet-div-icon', 
        iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] 
    });

    function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

    async function fetchAndDisplayRoutes() {
        loadingMessageEl.style.display = 'block';
        errorMessageEl.style.display = 'none';
        routesTableEl.style.display = 'none'; 
        noRoutesMessageEl.style.display = 'none'; 

        initBrowseMapIfNeeded();

        try {
            const response = await fetch('/api/list_saved_routes');
            if (!response.ok) {
                let errorDetails = `HTTP error! Status: ${response.status}`;
                try { const errorData = await response.json(); if (errorData && errorData.error) { errorDetails = errorData.error; } } catch (e) { /* ignore */ }
                throw new Error(errorDetails);
            }
            allFetchedRoutes = await response.json();
            resetAllFilters(false); 
            applyAllFiltersAndSort();
        } catch (error) {
            console.error('Error fetching routes:', error);
            loadingMessageEl.style.display = 'none';
            errorMessageEl.textContent = `Error loading routes: ${error.message}. Please check console.`;
            errorMessageEl.style.display = 'block';
        }
    }

    function initBrowseMapIfNeeded() {
        if (!browseMapInstance && document.body.contains(browseMapContainerEl)) {
            browseMapInstance = L.map('browseMapContainer').setView([54.5, -2.5], 6);
            const jawgAccessToken = 'YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p'; 
            L.tileLayer(`https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
                maxZoom: 22,
                attribution: '&copy; <a href="http://www.jawg.io/">Tiles Jawg Maps</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(browseMapInstance);
            
            if (L.control.fullscreen) {
                L.control.fullscreen().addTo(browseMapInstance);
            }
            browseMapInstance.on('zoomend', handleMapZoomEnd);

            // This will re-apply filters whenever the user stops moving or zooming the map.
            browseMapInstance.on('moveend zoomend', debounce(function() {
                if (document.getElementById('filterByMapToggle').checked) {
                    applyAllFiltersAndSort();
                 }
            }, 250)); // 250ms delay

        }
    }

    function clearCurrentRouteTrace() {
            if (currentRouteTraceLayer && browseMapInstance) {
            browseMapInstance.removeLayer(currentRouteTraceLayer);
            currentRouteTraceLayer = null;
        }
    }

    async function displayRouteTrace(routeId) {
        if (!browseMapInstance || !routeId) return;
        if (displayedTraceRouteId === routeId && currentRouteTraceLayer) return; 

        clearCurrentRouteTrace();
        browseMapContainerEl.style.cursor = 'wait';
        try {
            const response = await fetch(`/api/routes/${routeId}`);
            if (!response.ok) throw new Error(`Failed to fetch route details. Status: ${response.status}`);
            const routeData = await response.json();
            if (routeData && routeData.track_points && routeData.track_points.length > 0) {
                const latLngs = routeData.track_points.map(p => [p.lat, p.lon]).filter(p => p[0] != null && p[1] != null);
                if (latLngs.length > 0) {
                    currentRouteTraceLayer = L.polyline(latLngs, { 
                        color: '#f3ba19',
                        weight: 3,
                        fill: false,
                        interactive: false 
                    }).addTo(browseMapInstance); 
                    displayedTraceRouteId = routeId;
                }
            }
        } catch (error) {
            console.error(`Error displaying route trace for ${routeId}:`, error);
        } finally {
            browseMapContainerEl.style.cursor = '';
        }
    }

    function handleMapZoomEnd() {
        if (!browseMapInstance) return;
        const currentZoom = browseMapInstance.getZoom();
        if (currentZoom < TRACE_DISPLAY_ZOOM_THRESHOLD) {
            clearCurrentRouteTrace();
        } else if (displayedTraceRouteId && !currentRouteTraceLayer) {
            displayRouteTrace(displayedTraceRouteId); 
        }
    }

    function updateBrowseMapMarkers(routesToDisplay) {
        if (!browseMapInstance) initBrowseMapIfNeeded();

        if (currentMarkersLayer) currentMarkersLayer.clearLayers(); 
        else { 
            currentMarkersLayer = L.markerClusterGroup({
                showCoverageOnHover: false,
                iconCreateFunction: function(cluster) {
                    return L.divIcon({ 
                        html: `<div class="marker-cluster-custom"><span>${cluster.getChildCount()}</span></div>`,
                        className: '', 
                        iconSize: L.point(40, 40) 
                    });
                }
            });
            browseMapInstance.addLayer(currentMarkersLayer); 
        }

        if (!routesToDisplay || routesToDisplay.length === 0) return;

        let validMarkersExist = false;
        routesToDisplay.forEach(route => {
            if (route.start_coordinates && route.start_coordinates.lat != null && route.start_coordinates.lon != null) {
                const marker = L.marker([route.start_coordinates.lat, route.start_coordinates.lon], { icon: greenIcon }); 
                marker.bindPopup(`<b><a href="/route/${route._id}" target="_blank">${route.route_name || 'Unnamed'}</a></b><br>Score: ${parseFloat(route.difficulty_score || 0).toFixed(1)}`);
                marker.on('click', () => {
                    const clickedRouteId = route._id; 
                    if (browseMapInstance.getZoom() >= TRACE_DISPLAY_ZOOM_THRESHOLD) {
                        displayRouteTrace(clickedRouteId);
                    } else {
                        clearCurrentRouteTrace(); 
                        displayedTraceRouteId = clickedRouteId; 
                    }
                });
                currentMarkersLayer.addLayer(marker); 
                validMarkersExist = true;
            }
        });
    }

    function applyAllFiltersAndSort() {
    const searchTerm = searchInputEl.value.toLowerCase().trim();
    const startLocationTerm = startLocationFilterEl.value.toLowerCase().trim();
    const [minDifficulty, maxDifficulty] = $("#difficultySlider").slider("values");
    const [minDistance, maxDistance] = $("#distanceSlider").slider("values");
    const [minTEGa, maxTEGa] = $("#tegaSlider").slider("values");
    const surfaceFilter = surfaceTypeFilterEl.value;
    const tagFilter = tagFilterInputEl.value.toLowerCase().trim();
    
    // --- NEW: Get the state of our new checkbox and the map bounds ---
    const filterByMap = document.getElementById('filterByMapToggle').checked;
    const mapBounds = browseMapInstance ? browseMapInstance.getBounds() : null;
    // ---

    let filteredRoutes = allFetchedRoutes.filter(route => {
        // Standard text and slider filters (no change here)
        const nameMatch = (route.route_name || '').toLowerCase().includes(searchTerm);
        const startLocationMatch = (route.start_location_name || '').toLowerCase().includes(startLocationTerm);
        const surfaceMatch = !surfaceFilter || (route.surface_type === surfaceFilter);
        const tagMatch = !tagFilter || (route.tags && route.tags.some(tag => tag.toLowerCase() === tagFilter));
        const difficultyMatch = (route.difficulty_score ?? 0) >= minDifficulty && (route.difficulty_score ?? Infinity) <= maxDifficulty;
        const distanceMatch = (route.metrics_summary?.distance_km ?? 0) >= minDistance && (route.metrics_summary?.distance_km ?? Infinity) <= maxDistance;
        const tegaMatch = (route.metrics_summary?.TEGa ?? 0) >= minTEGa && (route.metrics_summary?.TEGa ?? Infinity) <= maxTEGa;

        // --- NEW: Map bounds filtering logic ---
        let isWithinMapBounds = true; // Default to true
        if (filterByMap && mapBounds && route.start_coordinates) {
            const routeLatLng = L.latLng(route.start_coordinates.lat, route.start_coordinates.lon);
            isWithinMapBounds = mapBounds.contains(routeLatLng);
        }
        // ---

        // The final check now includes the map bounds
        return nameMatch && startLocationMatch && surfaceMatch && tagMatch && difficultyMatch && distanceMatch && tegaMatch && isWithinMapBounds;
    });

    // The sorting logic below this remains unchanged...
    if (currentSortColumnIndex !== -1) {
        const propMap = [
            'route_name', 
            'start_location_name', 
            'metrics_summary.distance_km', 
            'metrics_summary.TEGa',
            'difficulty_score',
            'published_at', // Sort by the correct date field
            'creator_username'
        ];
        const sortProperty = propMap[currentSortColumnIndex];

        // This is a robust sorting function that handles numbers, strings, and missing values
        filteredRoutes.sort((a, b) => {
            // Get nested properties safely
            const valA = sortProperty.split('.').reduce((o, i) => o?.[i], a);
            const valB = sortProperty.split('.').reduce((o, i) => o?.[i], b);

            const valueA = valA ?? (typeof valA === 'string' ? '' : -Infinity);
            const valueB = valB ?? (typeof valB === 'string' ? '' : -Infinity);

            if (valueA < valueB) return currentSortAscending ? -1 : 1;
            if (valueA > valueB) return currentSortAscending ? 1 : -1;
            return 0;
        });
    }

    // ... (rest of the function is the same)
    if (displayedTraceRouteId && !filteredRoutes.find(r => r._id === displayedTraceRouteId)) clearCurrentRouteTrace();
    updateBrowseMapMarkers(filteredRoutes);
    renderTable(filteredRoutes);
    loadingMessageEl.style.display = 'none';
    routesTableEl.style.display = filteredRoutes.length > 0 ? 'table' : 'none';
    noRoutesMessageEl.style.display = filteredRoutes.length === 0 ? 'block' : 'none';
}

    function updateSelectAllCheckboxState() {
        if (!selectAllCheckboxEl) return;
        const allCheckboxes = routesTableBodyEl.querySelectorAll('.route-checkbox');
        const checkedCount = routesTableBodyEl.querySelectorAll('.route-checkbox:checked').length;

        if (checkedCount === 0) {
            selectAllCheckboxEl.checked = false;
            selectAllCheckboxEl.indeterminate = false;
        } else if (checkedCount === allCheckboxes.length) {
            selectAllCheckboxEl.checked = true;
            selectAllCheckboxEl.indeterminate = false;
        } else {
            selectAllCheckboxEl.checked = false;
            selectAllCheckboxEl.indeterminate = true;
        }
    }

    function renderTable(routes) {
        routesTableBodyEl.innerHTML = '';
        routes.forEach(route => {
            const row = routesTableBodyEl.insertRow();
            row.insertCell().innerHTML = `<input type="checkbox" class="route-checkbox" data-route-id="${route._id}">`;
            row.insertCell().innerHTML = `<a href="/route/${route._id}">${route.route_name || 'Unnamed'}</a>`;
            row.insertCell().textContent = route.start_location_name || 'N/A';
            row.insertCell().textContent = route.metrics_summary?.distance_km?.toFixed(2) ?? 'N/A';
            row.insertCell().textContent = route.metrics_summary?.TEGa?.toFixed(0) ?? 'N/A';
            row.insertCell().textContent = route.difficulty_score?.toFixed(2) ?? 'N/A';
            const dateValue = route.published_at || route.processed_at;
row.insertCell().textContent = dateValue ? new Date(dateValue).toLocaleDateString() : 'N/A';
            row.insertCell().textContent = route.creator_username || 'Anonymous';
        });
        updateCompareButtonVisibility();
        updateSelectAllCheckboxState(); // Update checkbox state whenever table is re-rendered
    }

    function sortTable(columnIndex) {
        currentSortAscending = currentSortColumnIndex === columnIndex ? !currentSortAscending : true;
        currentSortColumnIndex = columnIndex;
        applyAllFiltersAndSort();
        document.querySelectorAll('#routesTable th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        const header = document.querySelector(`#routesTable th[data-column-index="${columnIndex}"]`);
        if (header) {
            if (currentSortAscending) {
                header.classList.add('sort-asc');
            } else {
                header.classList.add('sort-desc');
            }
        }
    }

    function resetAllFilters(render = true) {
        searchInputEl.value = '';
        startLocationFilterEl.value = '';
        surfaceTypeFilterEl.value = '';
        tagFilterInputEl.value = ''; 
        $("#difficultySlider").slider("values", [defaultMinDifficulty, defaultMaxDifficulty]);
        $("#distanceSlider").slider("values", [defaultMinDistance, defaultMaxDistance]);
        $("#tegaSlider").slider("values", [defaultMinTEGa, defaultMaxTEGa]);
        difficultySliderValueEl.textContent = `${defaultMinDifficulty} - ${defaultMaxDifficulty}`;
        distanceSliderValueEl.textContent = `${defaultMinDistance} - ${defaultMaxDistance} km`;
        tegaSliderValueEl.textContent = `${defaultMinTEGa} - ${defaultMaxTEGa} m`;
        filterByMapToggle.checked = false;
        currentSortColumnIndex = -1;
        document.querySelectorAll('#routesTable th').forEach(th => th.classList.remove('th-sort-asc', 'th-sort-desc'));
        if (render) applyAllFiltersAndSort();
    }

    function updateCompareButtonVisibility() {
        const checkedCount = document.querySelectorAll('.route-checkbox:checked').length;
        compareBtn.disabled = checkedCount < 2;
        compareBtn.style.opacity = checkedCount < 2 ? '0.5' : '1';
        compareBtn.style.cursor = checkedCount < 2 ? 'not-allowed' : 'pointer';
    }

    function renderComparisonModal(routes) {
        // Destroy previous chart instances to prevent memory leaks
        if (radarChartInstance) radarChartInstance.destroy();
        if (elevationChartInstance) elevationChartInstance.destroy();

        // --- Setup variables for charts ---
        const chartColors = ['#f3ba19', '#5F734C', '#DDA717', '#2B3A13', '#A5AF9B', '#3a501a'];
        const chartBackgroundColors = chartColors.map(color => color + '33');

        // --- Render Radar Chart ---
        const radarCtx = document.getElementById('modalRadarChart').getContext('2d');
        const refMaxValues = { distance_km: 250, TEGa: 4500, ACg: 10, MCg: 25, ADg: 8 };
        const normalize = (val, key) => (val != null && refMaxValues[key]) ? Math.min(parseFloat(val), refMaxValues[key]) / refMaxValues[key] * 100 : 0;
        radarChartInstance = new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: ['Distance', 'Ascent', 'Avg Climb %', 'Max Climb %', 'Avg Descent %'],
                datasets: routes.map((r, i) => ({
                    label: r.route_name || 'Unnamed',
                    data: [
                        normalize(r.metrics_summary?.distance_km, 'distance_km'),
                        normalize(r.metrics_summary?.TEGa, 'TEGa'),
                        normalize(r.metrics_summary?.ACg, 'ACg'),
                        normalize(r.metrics_summary?.MCg, 'MCg'),
                        normalize(Math.abs(r.metrics_summary?.ADg || 0), 'ADg')
                    ],
                    borderColor: chartColors[i % chartColors.length],
                    backgroundColor: chartBackgroundColors[i % chartColors.length]
                }))
            },
            options: { responsive: true, maintainAspectRatio: true, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } }
        });
        
        // --- Render Interactive Elevation Chart ---
        const elevationCtx = document.getElementById('modalElevationChart').getContext('2d');
        elevationChartInstance = new Chart(elevationCtx, {
            type: 'line',
            data: {
                datasets: routes.map((r, i) => ({
                    label: r.route_name || 'Unnamed',
                    data: r.track_points.map(p => ({ x: p.dist, y: p.ele })),
                    borderColor: chartColors[i % chartColors.length],
                    fill: false, tension: 0.1, pointRadius: 0, pointHoverRadius: 5, borderWidth: 2
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { 
                    x: { type: 'linear', title: { display: true, text: 'Distance (km)' } }, 
                    y: { title: { display: true, text: 'Elevation (m)' } } 
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(context) { return `Distance: ${context[0].parsed.x.toFixed(2)} km`; },
                            label: function(context) { return `${context.dataset.label}:`; },
                            afterLabel: function(context) {
                                const route = routes[context.datasetIndex];
                                const dataPoint = route.track_points[context.dataIndex];
                                let gradient = 0.0;
                                if (context.dataIndex > 0) {
                                    const prevPoint = route.track_points[context.dataIndex - 1];
                                    const eleDiff = dataPoint.ele - prevPoint.ele;
                                    const distDiff = (dataPoint.dist - prevPoint.dist) * 1000;
                                    if (distDiff > 0) { gradient = (eleDiff / distDiff) * 100; }
                                }
                                return `  Elevation: ${context.parsed.y.toFixed(1)} m\n  Gradient: ${gradient.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });

        // --- Render Metrics Table ---
        let tableHTML = '<div class="chart-container"><h2>Key Metrics</h2><table id="routesTable"><thead><tr><th>Metric</th>' + routes.map(r => `<th><a href="/route/${r._id}" target="_blank">${r.route_name || 'Unnamed'}</a></th>`).join('') + '</tr></thead><tbody>';
        const metrics = [
            { label: 'Difficulty Score', key: 'difficulty_score', format: v => v?.toFixed(2) ?? 'N/A' },
            { label: 'Distance (km)', key: 'metrics_summary.distance_km', format: v => v?.toFixed(2) ?? 'N/A' },
            { label: 'Total Ascent (m)', key: 'metrics_summary.TEGa', format: v => v?.toFixed(0) ?? 'N/A' }
        ];
        metrics.forEach(m => {
            tableHTML += `<tr><td><strong>${m.label}</strong></td>` + routes.map(r => {
                const val = m.key.includes('.') ? m.key.split('.').reduce((o, i) => o?.[i], r) : r[m.key];
                return `<td>${m.format(val)}</td>`;
            }).join('') + '</tr>';
        });
        tableHTML += '</tbody></table></div>';
        
        // --- Render Top Rated Reviews Section ---
        const renderStars = (rating) => {
            let stars = '';
            if (rating === null || rating === undefined) return '<span style="opacity: 0.6;">Not rated</span>';
            for (let i = 1; i <= 5; i++) {
                stars += `<span class="star ${i <= rating ? 'filled' : ''}">★</span>`;
            }
            return stars;
        };

        let reviewsHTML = `<div class="top-reviews-section"><h2>Top Rated Reviews</h2><div class="comparison-reviews-grid">`;
        routes.forEach((route, i) => {
            const routeColor = chartColors[i % chartColors.length];
            reviewsHTML += `<div class="comment-item" style="border-top: 5px solid ${routeColor};">`;
            
            if (route.top_review) {
                const review = route.top_review;
                const avatarUrl = review.author_avatar_url || '/static/images/default_avatar.png';
                const username = review.creator_username || 'Anonymous';
                const report = review.ride_report || 'No report text.';
                const score = review.score ?? 'N/A';
                const ratings = review.ratings || {};

                reviewsHTML += `
                    <div class="review-main-content" style="flex-grow: 1;">
                        <div class="review-header">
                            <img src="${avatarUrl}" alt="${username}" class="comment-author-avatar">
                            <div><span class="comment-author">${username}</span></div>
                        </div>
                        <div class="review-ratings">
                            <div><strong>Scenery:</strong> ${renderStars(ratings.scenery)}</div>
                            <div><strong>Lack of Traffic:</strong> ${renderStars(ratings.traffic)}</div>
                            <div><strong>Pit Stops:</strong> ${renderStars(ratings.pit_stops)}</div>
                            <div><strong>Points of Interest:</strong> ${renderStars(ratings.points_of_interest)}</div>
                        </div>
                        <div class="review-body" style="margin-top: 15px;"><p class="comment-text">"${report.substring(0, 200)}${report.length > 200 ? '...' : ''}"</p></div>
                    </div>
                    <div class="trending-review-meta">
                        <span>For: <a href="/route/${route._id}" target="_blank">${route.route_name || 'Unnamed'}</a></span>
                        <span class="vote-score-display">★ ${score}</span>
                    </div>
                `;
            } else {
                reviewsHTML += `<p>No reviews have been submitted for this route yet.</p>`;
            }
            reviewsHTML += `</div>`;
        });
        reviewsHTML += `</div></div>`;
        
        // --- Combine and inject the final HTML ---
        modalTableContainer.innerHTML = tableHTML + reviewsHTML;
    }


    // --- Event Listeners and Initial Calls ---
    $("#difficultySlider").slider({ range: true, min: defaultMinDifficulty, max: defaultMaxDifficulty, step: difficultyStep, values: [defaultMinDifficulty, defaultMaxDifficulty], slide: (e, ui) => difficultySliderValueEl.textContent = `${ui.values[0]} - ${ui.values[1]}`, change: applyAllFiltersAndSort });
    $("#distanceSlider").slider({ range: true, min: defaultMinDistance, max: defaultMaxDistance, step: distanceStep, values: [defaultMinDistance, defaultMaxDistance], slide: (e, ui) => distanceSliderValueEl.textContent = `${ui.values[0]} - ${ui.values[1]} km`, change: applyAllFiltersAndSort });
    $("#tegaSlider").slider({ range: true, min: defaultMinTEGa, max: defaultMaxTEGa, step: tegaStep, values: [defaultMinTEGa, defaultMaxTEGa], slide: (e, ui) => tegaSliderValueEl.textContent = `${ui.values[0]} - ${ui.values[1]} m`, change: applyAllFiltersAndSort });
    
    surfaceTypeFilterEl.addEventListener('change', applyAllFiltersAndSort);
    tagFilterInputEl.addEventListener('input', applyAllFiltersAndSort);
    searchInputEl.addEventListener('input', applyAllFiltersAndSort);
    startLocationFilterEl.addEventListener('input', applyAllFiltersAndSort);
    resetFiltersButtonEl.addEventListener('click', () => resetAllFilters(true));
 
    const filterByMapToggle = document.getElementById('filterByMapToggle');
        if (filterByMapToggle) {
            filterByMapToggle.addEventListener('change', applyAllFiltersAndSort);
        }

    if (routesTableEl) routesTableEl.addEventListener('click', e => {
        const header = e.target.closest('th[data-column-index]');
        if (header) sortTable(parseInt(header.dataset.columnIndex, 10));
    });

    if (selectAllCheckboxEl) {
        selectAllCheckboxEl.addEventListener('click', (e) => {
            const isChecked = e.target.checked;
            routesTableBodyEl.querySelectorAll('.route-checkbox').forEach(cb => {
                cb.checked = isChecked;
            });
            updateCompareButtonVisibility();
        });   
    }

    if(routesTableBodyEl) {
        routesTableBodyEl.addEventListener('change', e => {
            if (e.target.classList.contains('route-checkbox')) {
                updateCompareButtonVisibility();
                updateSelectAllCheckboxState(); // Update the master checkbox state
            }
        });
    }
    if (compareBtn) {
        compareBtn.addEventListener('click', async () => {
            if (compareBtn.disabled) return;
            
            const ids = Array.from(document.querySelectorAll('.route-checkbox:checked')).map(cb => cb.dataset.routeId).join(',');
            if (!ids) return;
    
            modalOverlay.classList.remove('hidden');
            modalTableContainer.innerHTML = '<p>Loading comparison...</p>';
    
            try {
                const routeRes = await fetch(`/api/compare_data?ids=${ids}`);
                if (!routeRes.ok) throw new Error('Failed to fetch route data');
                const routes = await routeRes.json();
    
                const reviewRes = await fetch(`/api/get_top_reviews?ids=${ids}`);
                if (!reviewRes.ok) throw new Error('Failed to fetch review data');
                const topReviewsMap = await reviewRes.json();
    
                routes.forEach(route => {
                    if (topReviewsMap[route._id]) {
                        route.top_review = topReviewsMap[route._id];
                    } 
                    else {
                        route.top_review = null;
                    }
                });
    
                renderComparisonModal(routes);
    
            } catch (err) {
                modalTableContainer.innerHTML = `<p>Error loading comparison: ${err.message}</p>`;
            }
        });
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', () => modalOverlay.classList.add('hidden'));
    
    fetchAndDisplayRoutes();
    updateCompareButtonVisibility();
});