// app/static/js/map.js

document.addEventListener('DOMContentLoaded', function () {
    const mapContainer = document.getElementById('map');
    // --- ADDED: Get references to the list and indicator ---
    const hotelList = document.getElementById('hotel-list');
    const scrollIndicator = document.getElementById('scroll-indicator');

    if (!mapContainer || !hotelList) {
        console.error("Required map or hotel list elements not found!");
        return;
    }

    const jawgAccessToken = mapContainer.dataset.jawgToken;
    if (!jawgAccessToken) {
        mapContainer.innerHTML = '<p class="text-red-500 p-4">Error: Map service access token is missing.</p>';
        return;
    }

    // Initialize the map and make it globally accessible
    const leafletMap = L.map('map', {
        zoomControl: false // Disable the default zoom control
    }).setView([54.5, -3.5], 6); // Centered on the UK
    window.leafletMap = leafletMap; // Use a non-conflicting global variable name

    L.control.zoom({ position: 'bottomright' }).addTo(leafletMap);

    L.tileLayer(
        `https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
            attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">&copy; <b>Jawg</b>Maps</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            minZoom: 5,
            maxZoom: 22
        }
    ).addTo(leafletMap);

    const markers = L.markerClusterGroup();
    leafletMap.addLayer(markers);

    // --- ENHANCED: This function now also checks if the user is at the bottom ---
    function checkScrollIndicator() {
        if (!hotelList || !scrollIndicator) return;

        const isScrollable = hotelList.scrollHeight > hotelList.clientHeight;
        // Check if scrolled to the bottom (with a small 5px tolerance)
        const isAtBottom = hotelList.scrollTop + hotelList.clientHeight >= hotelList.scrollHeight - 5;

        if (isScrollable && !isAtBottom) {
            scrollIndicator.classList.remove('hidden');
        } else {
            scrollIndicator.classList.add('hidden');
        }
    }
    
    // --- ADDED: Add a scroll event listener to the list ---
    hotelList.addEventListener('scroll', checkScrollIndicator);


    // --- Function to update the sidebar ---
    function updateHotelList() {
        const bounds = leafletMap.getBounds();
        const north = bounds.getNorth();
        const south = bounds.getSouth();
        const east = bounds.getEast();
        const west = bounds.getWest();

        const apiUrl = `/api/hotels-in-view?north=${north}&south=${south}&east=${east}&west=${west}`;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                const hotelListContainer = document.getElementById('hotel-list');
                const hotels = data.hotels;

                hotelListContainer.innerHTML = '';
                markers.clearLayers();

                if (hotels && hotels.length > 0) {
                    const facilityIcons = {
                        'secure_storage': { icon: 'fa-shield-halved', title: 'Secure Bike Storage' },
                        'bike_wash': { icon: 'fa-shower', title: 'Bike Wash Station' },
                        'workshop_tools': { icon: 'fa-wrench', title: 'Workshop & Tools' },
                        'drying_room': { icon: 'fa-shirt', title: 'Drying Room' },
                        'packed_lunches': { icon: 'fa-box-archive', title: 'Packed Lunches' },
                        'laundry_service': { icon: 'fa-jug-detergent', title: 'Laundry Service' },
                        'ev_charging': { icon: 'fa-charging-station', title: 'EV Charging' },
                        'on-site_restaurant': { icon: 'fa-utensils', title: 'On-site Restaurant' }
                    };

                    hotels.forEach(hotel => {
                        const hotelCard = document.createElement('div');
                        hotelCard.className = 'bg-white/90 rounded-xl shadow border border-gray-200 overflow-hidden flex flex-col';

                        let facilitiesHtml = '';
                        if (hotel.facilities && hotel.facilities.length > 0) {
                            const iconsHtml = hotel.facilities.map(facilityKey => {
                                const facility = facilityIcons[facilityKey];
                                return facility ? `<i class="fa-solid ${facility.icon}" title="${facility.title}"></i>` : '';
                            }).join('');
                            facilitiesHtml = `<div class="flex items-center space-x-3 text-slate-600">${iconsHtml}</div>`;
                        }
                        
                        const featuredIconHtml = hotel.is_featured 
                            ? `<div class="flex items-center text-amber-500 font-poppins font-semibold text-xs ml-2">
                                   <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 7.91l6.572-.955L10 1l2.939 5.955 6.572.955-4.756 3.635 1.123 6.545z"></path></svg>
                                   <span>Premium</span>
                               </div>`
                            : '';

                        hotelCard.innerHTML = `
                            <div class="h-24 bg-slate-200">
                                <img src="https://placehold.co/400x200/2c3e50/f8f9fa?text=${encodeURIComponent(hotel.name)}" alt="Image of ${hotel.name}" class="w-full h-full object-cover">
                            </div>
                            <div class="p-3 flex-grow flex flex-col">
                                <div class="flex items-center justify-between">
                                    <h3 class="font-poppins text-md font-bold text-slate-800 leading-tight">${hotel.name}</h3>
                                    ${featuredIconHtml}
                                </div>
                                <p class="text-sm text-gray-600">${hotel.accommodation_type || 'Hotel'}</p>
                                
                                <div class="flex justify-between items-center mt-2 text-sm">
                                    <span class="font-bold text-slate-800">${hotel.price_range || ''}</span>
                                    <span class="text-gray-600">${hotel.route_count} Route${hotel.route_count !== 1 ? 's' : ''}</span>
                                </div>

                                <div class="mt-2 pt-2 border-t border-gray-200 flex justify-between items-center text-md">
                                    ${facilitiesHtml}
                                    <a href="/hotel/${hotel._id}" class="text-amber-500 hover:text-amber-600 font-semibold text-sm whitespace-nowrap">View &rarr;</a>
                                </div>
                            </div>
                        `;
                        hotelListContainer.appendChild(hotelCard);

                        let iconHtml;
                        if (hotel.is_featured) {
                            iconHtml = `<i class='fa-solid fa-location-dot text-amber-400'></i>`;
                        } else {
                            iconHtml = `<i class='fa-solid fa-location-dot text-slate-800'></i>`;
                        }
                        const customIcon = L.divIcon({
                            className: 'custom-icon-only', html: iconHtml, iconSize: [36, 36], iconAnchor: [18, 18]
                        });
                        const marker = L.marker([hotel.location.coordinates[1], hotel.location.coordinates[0]], { icon: customIcon });
                        marker.bindPopup(`<div class="p-1 font-poppins"><h3 class="font-bold text-md mb-1">${hotel.name}</h3><a href="/hotel/${hotel._id}" class="text-amber-500 hover:text-amber-600 font-semibold text-sm">View Details &rarr;</a></div>`);
                        markers.addLayer(marker);
                    });
                } else {
                    hotelListContainer.innerHTML = '<p class="text-gray-500 text-center py-8 px-4">No hotels found in the current map area.</p>';
                }

                // Use a short timeout to give the browser a moment to render the new content
                // before we check the scroll height. This is the most reliable way to fix the timing issue.
                setTimeout(checkScrollIndicator, 100); 
                
            })
            .catch(error => {
                console.error("Error fetching hotels in view:", error);
                document.getElementById('hotel-list').innerHTML = '<p class="text-red-500 text-center py-8 px-4">Could not load hotels.</p>';
            });
    }

    leafletMap.on('moveend', updateHotelList);
    leafletMap.whenReady(updateHotelList);
});
