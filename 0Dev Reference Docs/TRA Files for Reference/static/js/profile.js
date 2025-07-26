document.addEventListener('DOMContentLoaded', () => {
        // --- New Tab Switching Logic ---
        const tabLinks = document.querySelectorAll('.tab-link');
        const tabContents = document.querySelectorAll('.tab-content');
        tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                const tabId = link.getAttribute('data-tab');
                tabLinks.forEach(l => l.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                link.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });

        // --- Existing Comparison Logic (largely unchanged) ---
        const compareBtnProfile = document.getElementById('compareBtnProfile');
        const clearSelectionBtnProfile = document.getElementById('clearSelectionBtnProfile');
        const modalOverlay = document.getElementById('comparisonModal');
        const modalCloseBtn = document.getElementById('modalCloseBtn');
        const modalTableContainer = document.getElementById('modalTableContainer');
        
        let selectedRouteIdsProfile = new Set();
        let radarChartInstance = null;
        let elevationChartInstance = null;

        function updateProfileCompareButtonVisibility() {
            if (!compareBtnProfile) return;
            const selectedCount = document.querySelectorAll('.route-checkbox-profile:checked').length;
            if (selectedCount >= 2) {
                compareBtnProfile.disabled = false;
                compareBtnProfile.style.opacity = '1';
                compareBtnProfile.style.cursor = 'pointer';
            } else {
                compareBtnProfile.disabled = true;
                compareBtnProfile.style.opacity = '0.5';
                compareBtnProfile.style.cursor = 'not-allowed';
            }
        }
        
        // This event listener now covers checkboxes in any tab
        document.querySelector('.container').addEventListener('change', (event) => {
            if (event.target.classList.contains('route-checkbox-profile')) {
                updateProfileCompareButtonVisibility();
            }
        });

        if (clearSelectionBtnProfile) {
            clearSelectionBtnProfile.addEventListener('click', () => {
                document.querySelectorAll('.route-checkbox-profile:checked').forEach(checkbox => {
                    checkbox.checked = false;
                });
                updateProfileCompareButtonVisibility();
            });
        }

        if (compareBtnProfile) {
            compareBtnProfile.addEventListener('click', async () => {
                if (compareBtnProfile.disabled) return;
                
                selectedRouteIdsProfile.clear();
                document.querySelectorAll('.route-checkbox-profile:checked').forEach(cb => {
                    selectedRouteIdsProfile.add(cb.dataset.routeId);
                });

                if (selectedRouteIdsProfile.size < 2) return;

                const ids = Array.from(selectedRouteIdsProfile).join(',');
                modalOverlay.classList.remove('hidden');
                
                // Clear old charts and table
                if (radarChartInstance) radarChartInstance.destroy();
                if (elevationChartInstance) elevationChartInstance.destroy();
                modalTableContainer.innerHTML = '<p>Loading comparison...</p>';

                try {
                    const response = await fetch(`/api/compare_data?ids=${ids}`);
                    if (!response.ok) throw new Error('Failed to fetch comparison data');
                    const routes = await response.json();
                    if (!routes || routes.error || (Array.isArray(routes) && routes.length === 0)) {
                        throw new Error('No matching routes found for comparison.');
                    }
                    renderComparisonModal(routes);
                } catch (error) {
                    modalTableContainer.innerHTML = `<p>Error loading comparison data: ${error.message}</p>`;
                }
            });
        }

        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', () => modalOverlay.classList.add('hidden'));
        }
        modalOverlay.addEventListener('click', (event) => {
            if (event.target === modalOverlay) {
                modalOverlay.classList.add('hidden');
            }
        });

        // The renderComparisonModal function remains the same as before
        function renderComparisonModal(routes) {
            const chartColors = ['#f3ba19', '#5F734C', '#DDA717', '#2B3A13', '#A5AF9B', '#3a501a'];
            const chartBackgroundColors = chartColors.map(color => color + '33');
            const refMaxValues = { distance_km: 250, TEGa: 4500, ACg: 10, MCg: 25, ADg: 8 };

            function normalizeMetric(value, metricName) {
                if (value === null || value === undefined || refMaxValues[metricName] === undefined) return 0;
                return Math.min(parseFloat(value) || 0, refMaxValues[metricName]) / refMaxValues[metricName] * 100;
            }

            const radarDatasets = routes.map((route, index) => ({
                label: route.route_name || 'Unnamed',
                data: [
                    normalizeMetric(route.metrics_summary.distance_km, 'distance_km'),
                    normalizeMetric(route.metrics_summary.TEGa, 'TEGa'),
                    normalizeMetric(route.metrics_summary.ACg, 'ACg'),
                    normalizeMetric(route.metrics_summary.MCg, 'MCg'),
                    normalizeMetric(Math.abs(route.metrics_summary.ADg || 0), 'ADg')
                ],
                borderColor: chartColors[index % chartColors.length],
                backgroundColor: chartBackgroundColors[index % chartBackgroundColors.length],
                borderWidth: 2, pointRadius: 3
            }));
            radarChartInstance = new Chart(document.getElementById('modalRadarChart'), {
                type: 'radar',
                data: { labels: ['Distance', 'Ascent', 'Avg Climb %', 'Max Climb %', 'Avg Descent %'], datasets: radarDatasets },
                options: { responsive: true, maintainAspectRatio: false, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } }
            });

            const elevationDatasets = routes.map((route, index) => ({
                label: route.route_name || 'Unnamed',
                data: route.track_points.map(p => ({ x: p.dist, y: p.ele })),
                borderColor: chartColors[index % chartColors.length],
                fill: false, tension: 0.1, pointRadius: 0, borderWidth: 2
            }));
            elevationChartInstance = new Chart(document.getElementById('modalElevationChart'), {
                type: 'line',
                data: { datasets: elevationDatasets },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { type: 'linear', title: { display: true, text: 'Distance (km)' } }, y: { title: { display: true, text: 'Elevation (m)' } } } }
            });

            let tableHTML = '<table><thead><tr><th>Metric</th>';
            routes.forEach(route => {
                tableHTML += `<th><a href="/route/${route._id}" target="_blank">${route.route_name || 'Unnamed'}</a></th>`;
            });
            tableHTML += '</tr></thead><tbody>';
            const metricsToDisplay = [
                { label: 'Difficulty Score', key: 'difficulty_score', format: (val) => val !== null ? parseFloat(val).toFixed(2) : 'N/A' },
                { label: 'Distance (km)', key: 'metrics_summary.distance_km', format: (val) => val !== null ? parseFloat(val).toFixed(2) : 'N/A' },
                { label: 'Total Ascent (m)', key: 'metrics_summary.TEGa', format: (val) => val !== null ? parseFloat(val).toFixed(0) : 'N/A' },
                { label: 'Max Gradient (%)', key: 'metrics_summary.MCg', format: (val) => val !== null ? parseFloat(val).toFixed(1) : 'N/A' },
                { label: 'Avg. Climb Gradient (%)', key: 'metrics_summary.ACg', format: (val) => val !== null ? parseFloat(val).toFixed(1) : 'N/A' },
            ];
            metricsToDisplay.forEach(metric => {
                tableHTML += `<tr><td><strong>${metric.label}</strong></td>`;
                routes.forEach(route => {
                    let value = metric.key.includes('.') ? metric.key.split('.').reduce((o, i) => o ? o[i] : null, route) : route[metric.key];
                    tableHTML += `<td>${metric.format(value)}</td>`;
                });
                tableHTML += '</tr>';
            });
            tableHTML += '</tbody></table>';
            modalTableContainer.innerHTML = tableHTML;
        }
        
        updateProfileCompareButtonVisibility();
    });