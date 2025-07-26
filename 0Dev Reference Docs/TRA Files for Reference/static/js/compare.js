document.addEventListener('DOMContentLoaded', () => {
    // This is a check to ensure the data from your compare.html template is available
    if (typeof initialCompareData === 'undefined' || !initialCompareData || initialCompareData.length === 0) {
        console.error('Comparison data not found or is empty. Cannot initialize charts.');
        return;
    }

    const routes = initialCompareData;
    const chartColors = ['#f3ba19', '#5F734C', '#DDA717', '#2B3A13', '#A5AF9B', '#3a501a'];

    // --- RENDER THE RADAR CHART (No changes needed here) ---
    const radarCanvas = document.getElementById('metricsRadarChart');
    if (radarCanvas) {
        const refMaxValues = { distance_km: 250, TEGa: 4500, ACg: 10, MCg: 25, ADg: 8 };
        const normalize = (val, key) => (val != null && refMaxValues[key]) ? Math.min(parseFloat(val), refMaxValues[key]) / refMaxValues[key] * 100 : 0;
        new Chart(radarCanvas.getContext('2d'), {
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
                    backgroundColor: chartColors[i % chartColors.length] + '33'
                }))
            },
            options: { responsive: true, maintainAspectRatio: true, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } }
        });
    }

    // --- RENDER THE INTERACTIVE ELEVATION CHART (This is the corrected version) ---
    const elevationCanvas = document.getElementById('elevationProfileChart');
    if (elevationCanvas) {
        new Chart(elevationCanvas.getContext('2d'), {
            type: 'line',
            data: {
                datasets: routes.map((route, i) => ({
                    label: route.route_name || 'Unnamed',
                    data: route.track_points.map(p => ({ x: parseFloat(p.dist.toFixed(2)), y: parseFloat(p.ele.toFixed(1)) })),
                    borderColor: chartColors[i % chartColors.length],
                    tension: 0.1,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    borderWidth: 2
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                
                // --- THIS IS THE CRITICAL FIX ---
                // This configuration ensures the hover and tooltip trigger anywhere
                // on the chart's vertical axis, just like on the route profile page.
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                // ------------------------------------

                scales: {
                    x: { type: 'linear', title: { display: true, text: 'Distance (km)' } },
                    y: { title: { display: true, text: 'Elevation (m)' } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            // This logic correctly formats the tooltip for multiple routes
                            title: function(context) { return `Distance: ${context[0].parsed.x.toFixed(2)} km`; },
                            label: function(context) { return `${context.dataset.label}:`; },
                            afterLabel: function(context) {
                                const route = initialCompareData[context.datasetIndex];
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
    }
});