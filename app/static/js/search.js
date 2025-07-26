// app/static/js/search.js

document.addEventListener('DOMContentLoaded', function () {
    const waitForMap = setInterval(() => {
        if (window.leafletMap) {
            clearInterval(waitForMap);
            initializeSearch();
        }
    }, 100);

    // Debounce function to limit the rate of API calls
    function debounce(func, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    function initializeSearch() {
        const container = document.querySelector('#autocomplete-container');
        if (!container) {
            console.error('Autocomplete container not found.');
            return;
        }

        accessibleAutocomplete({
            element: container,
            id: 'locationSearch',
            source: debounce(async (query, populateResults) => {
                if (!query) return;
                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}&countrycodes=gb`);
                    const data = await response.json();
                    const suggestions = data.map(item => item.display_name);
                    populateResults(suggestions);
                } catch (error) {
                    console.error('Error fetching search results:', error);
                }
            }, 300), // Wait for 300ms of inactivity before searching
            onConfirm: async (confirmed) => {
                if (!confirmed) return;
                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${confirmed}&countrycodes=gb&limit=1`);
                    const data = await response.json();
                    if (data.length > 0) {
                        const location = data[0];
                        window.leafletMap.setView([location.lat, location.lon], 13);
                    }
                } catch (error) {
                    console.error('Error geocoding selected location:', error);
                }
            },
            placeholder: 'Where would you like to go?',
            dropdownArrow: () => '<span class="sr-only">Show suggestions</span>',
        });
    }
});
