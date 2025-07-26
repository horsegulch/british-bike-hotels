// In static/js/index.js

document.addEventListener('DOMContentLoaded', function() {
    const trendingGrid = document.getElementById('trendingImagesGrid');

    // This function displays the images by creating HTML cards
    function displayTrendingImages(images) {
        if (!images || images.length === 0) {
            trendingGrid.innerHTML = '<p>No trending images yet. Upload and vote on photos to see them here!</p>';
            return;
        }

        trendingGrid.innerHTML = ''; // Clear loading message

        images.forEach(image => {
            const score = (image.upvotes?.length || 0) - (image.downvotes?.length || 0);
            
            // Create a div with the 'route-card' class to match the existing style
            const card = document.createElement('div');
            card.className = 'route-card';

            // Set the inner HTML using the standard route card structure
            card.innerHTML = `
            <a href="/route/${image.route_details._id.$oid}" class="route-card-thumbnail-link">
                <div class="route-card-map-thumbnail">
                    <img src="/reviews/images/${image.filename}" alt="Trending ride image">
                </div>
            </a>
            <div class="route-card-content">
                <h3>
                    <a href="/route/${image.route_details._id.$oid}">${image.route_details.route_name}</a>
                </h3>
                
                <div class="route-card-creator-info">
                    <div class="creator-details">
                        <img src="${image.uploader_avatar_url}" alt="${image.uploader_details.username}" class="creator-avatar-thumbnail">
                        <span>by ${image.uploader_details.username}</span>
                    </div>
                    <span class="trending-card-score">★ ${score}</span>
                </div>
            </div>
        `;
        trendingGrid.appendChild(card);
        });
    }

    // This function fetches the data from the API
    async function fetchTrendingImages() {
        try {
            const response = await fetch('/api/trending_images');
            if (!response.ok) {
                throw new Error('Failed to fetch trending images.');
            }
            const images = await response.json();
            displayTrendingImages(images); // Call the display function
        } catch (error) {
            console.error(error);
            trendingGrid.innerHTML = '<p>Could not load trending images at this time.</p>';
        }
    }

    // --- SCRIPT EXECUTION STARTS HERE ---
    // If the grid element exists on the page, fetch the images.
    if (trendingGrid) {
        fetchTrendingImages();
    }
});