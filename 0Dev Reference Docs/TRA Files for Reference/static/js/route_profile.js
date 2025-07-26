// REPLACE the top section of route_profile.js with this corrected version

document.addEventListener('DOMContentLoaded', function() {
    // --- CORRECTED DOM ELEMENT SELECTION ---
    // We only select elements that actually exist in the new HTML.
    // Notice loadingMessageEl, errorMessageEl, and the old creatorUsernameEl are gone.
    const likesCountEl = document.getElementById('likesCount');
    const commentsListEl = document.getElementById('commentsList');
    const commentFormEl = document.getElementById('commentForm');
    const commentTextInputEl = document.getElementById('commentText');
    const favoriteButtonEl = document.getElementById('favoriteButton');
    const mapContainer = document.getElementById('map');
    const elevationCanvas = document.getElementById('elevationProfileChart');
    const accessFileButtonEl = document.getElementById('accessFileButton');
    const likeButtonEl = document.getElementById('likeButton');

    // Initialize state variables
    let elevationChartInstance = null;
    let mapInstance = null;
    let currentRouteId = null;
    let elevationMarker =  null;
    // Note: isCurrentlyLiked and isCurrentlyFavorited logic might need to be revisited,
    // but we'll focus on fixing the crash first.

    function getRouteIdFromUrl() {
        const pathSegments = window.location.pathname.split('/');
        return pathSegments[pathSegments.length - 1];
    }

    // --- CORRECTED fetchRouteData FUNCTION ---
    // This function no longer tries to access elements that don't exist.
    async function fetchRouteData(routeId) {
        currentRouteId = routeId;
        try {
            const response = await fetch(`/api/routes/${routeId}`);
            if (!response.ok) throw new Error('Route not found');
            const data = await response.json();
            displayRouteData(data);
        } catch (error) {
            // If an error occurs, we update the elements that DO exist to show the error.
            const routeNameEl = document.getElementById('routeName');
            routeNameEl.textContent = 'Error Loading Route';
            document.getElementById('routeDescription').textContent = `Details: ${error.message}. Please try again.`;
        }
    }

// The 'displayRouteData' function follows this. We'll make a small change there next.

    // REPLACE the existing displayRouteData function with this one

function displayRouteData(data) {
    // Get new elements from the DOM
    const routeNameEl = document.getElementById('routeName');
    const tagsBarEl = document.getElementById('tagsBar');
    const routeDescriptionEl = document.getElementById('routeDescription');
    const keyStatsEl = document.getElementById('keyStats');
    
    // --- Populate Header ---
    const pageTitle = data.route_name || 'Unnamed Route';
    routeNameEl.textContent = pageTitle;
    document.title = `${pageTitle} | The Ride Archive`;

    // --- Populate Creator Info (if it exists) ---
    const creatorInfoEl = document.getElementById('creatorInfo');
    if (data.creator_username) {
        document.getElementById('creatorUsername').textContent = data.creator_username;
        const creatorAvatarEl = document.getElementById('creatorAvatar');
        creatorAvatarEl.src = data.creator_avatar_url || '/static/images/default_avatar.png';
        creatorInfoEl.style.display = 'flex';
    }

    // --- Populate Tags ---
    tagsBarEl.innerHTML = ''; 
    if (data.surface_type) {
        const surfaceTag = document.createElement('span');
        surfaceTag.className = 'tag-item surface-tag';
        surfaceTag.textContent = data.surface_type;
        tagsBarEl.appendChild(surfaceTag);
    }
    if (data.tags && data.tags.length > 0) {
        data.tags.forEach(tagText => {
            const tag = document.createElement('span');
            tag.className = 'tag-item';
            tag.textContent = tagText;
            tagsBarEl.appendChild(tag);
        });
    }

    // --- Populate Key Stats ---
    keyStatsEl.innerHTML = ''; // Clear old stats
    const summary = data.metrics_summary || {};
    const stats = {
        'Difficulty Score': data.difficulty_score?.toFixed(2) ?? 'N/A',
        'Distance': `${summary.distance_km?.toFixed(2) ?? 'N/A'} km`,
        'Elevation Gain': `${summary.TEGa?.toFixed(0) ?? 'N/A'} m`,
        'Max Gradient': `${summary.MCg?.toFixed(1) ?? 'N/A'}%`,
        'Avg. Climb': `${summary.ACg?.toFixed(1) ?? 'N/A'}%`,
        'Avg. Descent': `${summary.ADg?.toFixed(1) ?? 'N/A'}%`
    };
    
    for (const [key, value] of Object.entries(stats)) {
        const statItem = document.createElement('div');
        statItem.className = 'stat-item';
        statItem.innerHTML = `<span class="stat-label">${key}</span><span class="stat-value">${value}</span>`;
        keyStatsEl.appendChild(statItem);
    }

    // --- Populate Description ---
    routeDescriptionEl.textContent = data.description || 'No description has been provided for this route.';

    // --- FIX #1: Use the correct ID string here ---
    document.getElementById('likesCount').textContent = `Likes: ${data.likes_count ?? 0}`;
    const accessFileButtonEl = document.getElementById('accessFileButton');
    accessFileButtonEl.href = `/api/routes/${data._id.$oid}/access_file`; // Changed from data._id
    accessFileButtonEl.textContent = data.source_type === 'url' ? 'Go to Original Route' : `Download ${data.file_type?.toUpperCase()} File`;

    // --- FIX #2: Use the correct ID string here ---
    fetchAndDisplayHeaderGallery(data._id.$oid); // Changed from data._id

    fetch(`/api/routes/${currentRouteId}/reviews`)
        .then(res => res.json())
        .then(reviews => {
            displayReviews(reviews);
        });

    // --- Initialize Map and Chart (this logic doesn't need to change) ---
    if (data.track_points && data.track_points.length > 0) {
        initMap(data.track_points);
        initElevationProfile(data.track_points);
    } else {
        document.getElementById('map').innerHTML = '<p>No map data available.</p>';
        document.getElementById('elevationProfileChart').parentElement.innerHTML = '<p>No elevation data.</p>';
    }
}

async function fetchAndDisplayHeaderGallery(routeId) {
    const galleryContainer = document.getElementById('headerImageGalleryContainer');
    const galleryEl = document.getElementById('headerImageGallery');

    try {
        const response = await fetch(`/api/routes/${routeId}/images`);
        const images = await response.json();

        if (images && images.length > 0) {
            galleryEl.innerHTML = '';
            images.forEach(image => {
                const score = (image.upvotes?.length || 0) - (image.downvotes?.length || 0);

                // Create a container for the image and its score overlay
                const thumbContainer = document.createElement('div');
                thumbContainer.className = 'header-gallery-item';

                // Create the image element
                const imgElement = document.createElement('img');
                imgElement.src = `/reviews/images/${image.filename}`;
                imgElement.alt = "Route gallery image";
                imgElement.className = 'header-gallery-thumbnail';
                imgElement.dataset.fullsizeSrc = `/reviews/images/${image.filename}`;
                imgElement.dataset.imageId = image._id.$oid;
                imgElement.dataset.score = score;
                
                // Create the score element
                const scoreElement = document.createElement('span');
                scoreElement.className = 'thumbnail-score';
                scoreElement.innerHTML = `★ ${score}`;

                // Add the image and score to the container
                thumbContainer.appendChild(imgElement);
                thumbContainer.appendChild(scoreElement);
                
                // Add the container to the main gallery
                galleryEl.appendChild(thumbContainer);
            });
            galleryContainer.style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching header gallery images:', error);
        galleryContainer.style.display = 'none';
    }
}
 
    function initMap(trackPoints) {
        if (mapInstance) {
            mapInstance.remove();
        }
        mapInstance = L.map('map');
        const jawgAccessToken = 'YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p';
        L.tileLayer(`https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=${jawgAccessToken}`, {
            maxZoom: 22,
            attribution: '&copy; Jawg Maps &copy; OpenStreetMap contributors'
        }).addTo(mapInstance);

        const latLngs = trackPoints.map(p => [p.lat, p.lon]);
        const polyline = L.polyline(latLngs, { color: '#f3ba19', weight: 4 }).addTo(mapInstance);

        mapInstance.fitBounds(polyline.getBounds().pad(0.1));

        if (latLngs.length > 0) {
            const loopThresholdMeters = 500;
            const startPoint = L.latLng(latLngs[0]);
            const endPoint = L.latLng(latLngs[latLngs.length - 1]);
            const distance = startPoint.distanceTo(endPoint);

            if (distance < loopThresholdMeters) {
                const loopIcon = L.divIcon({
                    className: 'map-marker-icon loop-marker-icon',
                    html: '',
                    iconSize: [20, 20],
                    iconAnchor: [16, 17]
                });
                L.marker(startPoint, { icon: loopIcon }).addTo(mapInstance);
            } 
            else {
                const startIcon = L.divIcon({
                    className: 'map-marker-icon start-marker-icon',
                    html: '',
                    iconSize: [20, 20],
                    iconAnchor: [14, 15]
                });
                const endIcon = L.divIcon({
                    className: 'map-marker-icon end-marker-icon',
                    html: '',
                    iconSize: [20, 20],
                    iconAnchor: [14, 15]
                });

                L.marker(startPoint, { icon: startIcon }).addTo(mapInstance);
                L.marker(endPoint, { icon: endIcon }).addTo(mapInstance);
            } 
            
        const caretDivIcon = L.divIcon({
            className: 'chevron-marker',
            html: '⮝',
            iconSize: [20, 20],
            iconAnchor: [8, 8]
        });

        L.polylineDecorator(polyline, {
            patterns: [
                {
                    offset: '10%', 
                    repeat: '150px', 
                    symbol: L.Symbol.marker({
                        rotate: true,
                        markerOptions: {
                            icon: caretDivIcon
                        }
                    })
                }
            ]
        }).addTo(mapInstance);
        }    
    }

    function initElevationProfile(trackPoints) {
    if (elevationChartInstance) {
        elevationChartInstance.destroy();
    }

    // Filter out any points that might be missing data
    const validTrackPoints = trackPoints.filter(p => p.dist != null && p.ele != null);
    
    // --- CHANGE #1: Reformat data for a numerical X-axis ---
    // Instead of separate labels and data, we create points with x and y values.
    // This lets Chart.js create clean, evenly spaced axis ticks (0, 5, 10, etc.).
    const chartData = validTrackPoints.map(p => ({
        x: parseFloat(p.dist.toFixed(2)),
        y: parseFloat(p.ele.toFixed(1))
    }));

    if (chartData.length === 0) {
        elevationCanvas.parentElement.innerHTML = '<p style="text-align:center; padding: 20px;">No elevation data available.</p>';
        return;
    }

    const ctx = elevationCanvas.getContext('2d');
    elevationChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Elevation (m)',
                data: chartData, // Use the new data format here
                borderColor: '#3a501a',
                backgroundColor: 'rgba(58, 80, 26, 0.2)',
                tension: 3,
                fill: true,
                animation: false,
                pointRadius: 0,
                borderWidth: 2,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#f3ba19',
                pointHoverBorderWidth: 2,             // The 2px border width
                pointHoverBorderColor: '#f5d262'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
            padding: {
                top: 30 // Creates 30px of space at the top
            }
        },

        interaction: {
            mode: 'index',
            intersect: false
        },

            scales: {
                // --- CHANGE #2: Configure the X-axis for better labels ---
                x: {
                    type: 'linear', // Treat as a numerical axis
                    title: {
                        display: true,
                        text: 'Distance (km)'
                    },
                    ticks: {
                        // This suggests a step size to get intervals like 0, 5, 10...
                        // Chart.js will adjust this intelligently.
                        stepSize: 5 
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Elevation (m)'
                    }
                }
            },
            // --- CHANGE #3: Customize the tooltip content ---
            plugins: {
                
                 legend: {
                    display: false
                },

                tooltip: {
                    mode: 'index',
                    intersect: false,
                    yAlign: 'center',
                    xAlign: 'left',
                    callbacks: {
                        // Formats the main title of the tooltip
                        title: function(context) {
                            const xValue = context[0].parsed.x;
                            return `Distance: ${xValue.toFixed(2)} km`;
                        },
                        // Formats the elevation line
                        label: function(context) {
                            const yValue = context.parsed.y;
                            return `Elevation: ${yValue.toFixed(1)} m`;
                        },
                        // Adds a new line for the gradient after the elevation
                        afterLabel: function(context) {
                            const dataIndex = context.dataIndex;
                            // Cannot calculate gradient for the very first point
                            if (dataIndex > 0) {
                                const currentPoint = validTrackPoints[dataIndex];
                                const prevPoint = validTrackPoints[dataIndex - 1];

                                const eleDiff = currentPoint.ele - prevPoint.ele; // Elevation change in meters
                                const distDiff = (currentPoint.dist - prevPoint.dist) * 1000; // Distance change in meters

                                if (distDiff === 0) {
                                    return 'Gradient: -';
                                }
                                const gradient = (eleDiff / distDiff) * 100;
                                return `Gradient: ${gradient.toFixed(1)}%`;
                            }
                            return 'Gradient: 0.0%';
                        }
                    }
                }
            }
        }
    });

    // This section for map interaction remains unchanged and will still work.
    const canvas = elevationCanvas;
    const hoverIcon = L.divIcon({
        className: 'elevation-marker-icon',
        html: '',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });

    canvas.addEventListener('mousemove', (e) => {
        const elements = elevationChartInstance.getElementsAtEventForMode(e, 'index', { intersect: false }, true);
        if (elements.length > 0) {
            const dataIndex = elements[0].index;
            const hoveredPointData = validTrackPoints[dataIndex];
            if (hoveredPointData && hoveredPointData.lat && hoveredPointData.lon) {
                const latLng = [hoveredPointData.lat, hoveredPointData.lon];
                if (!elevationMarker) {
                    elevationMarker = L.marker(latLng, { icon: hoverIcon }).addTo(mapInstance);
                } else {
                    elevationMarker.setLatLng(latLng);
                }
            }
        }
    });

    canvas.addEventListener('mouseout', () => {
        if (elevationMarker) {
            mapInstance.removeLayer(elevationMarker);
            elevationMarker = null;
        }
    });
}
    
    
    async function fetchAndDisplayReviews(routeId, sortBy = 'latest') {
        const reviewsListEl = document.getElementById('commentsList');
        reviewsListEl.innerHTML = '<li>Loading reviews...</li>'; // Show loading message

        try {
            const response = await fetch(`/api/routes/${routeId}/reviews?sort=${sortBy}`);
            if (!response.ok) {
                throw new Error('Failed to fetch reviews.');
            }   
            const reviews = await response.json();
            displayReviews(reviews); // Reuse the existing display function
        } catch (error) {
            console.error('Error fetching reviews:', error);
            reviewsListEl.innerHTML = '<li>Error loading reviews.</li>';
        }
    }

    // In route_profile.js, replace the entire displayReviews function with this one

function displayReviews(reviews) {
    const reviewsListEl = document.getElementById('commentsList');
    reviewsListEl.innerHTML = '';

    if (reviews && reviews.length > 0) {
        reviews.forEach(review => {
            const reviewItem = document.createElement('li');
            reviewItem.className = 'comment-item';
            
            reviewItem.dataset.reviewId = review._id; 

            let avatarUrl = '';
            if (review.author_details && review.author_details.avatar_filename) {
                avatarUrl = `/avatars/${review.author_details.avatar_filename}`;
            } else if (review.author_details && review.author_details.gravatar_hash) {
                avatarUrl = `https://www.gravatar.com/avatar/${review.author_details.gravatar_hash}?s=40&d=identicon`;
            }

            const renderStars = (rating) => {
                let stars = '';
                if (rating === null || rating === undefined) return '<span class="text-muted">Not rated</span>';
                for (let i = 1; i <= 5; i++) {
                    stars += `<span class="star ${i <= rating ? 'filled' : ''}">★</span>`;
                }
                return stars;
            };
            
            let imagesHTML = '';
            if (review.images_data && review.images_data.length > 0) {
                
                // --- THIS SECTION HAS BEEN CORRECTED ---
                const imageElements = review.images_data.map(img => {
                    const score = (img.upvotes?.length || 0) - (img.downvotes?.length || 0);
                    return `
                        <a href="/reviews/images/${img.filename}" target="_blank" class="gallery-link">
                            <img src="/reviews/images/${img.filename}" 
                                 alt="Ride review image" 
                                 class="review-image-thumbnail"
                                 data-fullsize-src="/reviews/images/${img.filename}"
                                 data-image-id="${img._id.$oid}" 
                                 data-score="${score}">
                        </a>
                    `; // The template literal string ends here
                }).join(''); // The .join('') is now correctly placed after the .map()
                // --- END OF CORRECTION ---
                
                imagesHTML = `<div class="review-image-gallery">${imageElements}</div>`;
            }

            const upvotes = review.upvotes?.length || 0;
            const downvotes = review.downvotes?.length || 0;
            const voteScore = upvotes - downvotes;
            
            const reviewDate = new Date(review.created_at).toLocaleString();

            reviewItem.innerHTML = `
                <div class="review-main-content">
                    <div class="review-header">
                        <img src="${avatarUrl}" alt="${review.creator_username || 'Anonymous'}" class="comment-author-avatar">
                        <div>
                            <span class="comment-author">${review.creator_username || 'Anonymous'}</span>
                            <span class="comment-timestamp"> - ${reviewDate}</span>
                        </div>
                    </div>
                    <div class="review-ratings">
                        <div><strong>Scenery:</strong> ${renderStars(review.ratings.scenery)}</div>
                        <div><strong>Lack of Traffic:</strong> ${renderStars(review.ratings.traffic)}</div>
                        <div><strong>Pit Stops:</strong> ${renderStars(review.ratings.pit_stops)}</div>
                        <div><strong>Points of Interest:</strong> ${renderStars(review.ratings.points_of_interest)}</div>
                        <div><strong>Perceived Difficulty:</strong> ${renderStars(review.ratings.perceived_difficulty)}</div>
                    </div>
                    <div class="review-body">
                        <p class="comment-text">${review.ride_report}</p>
                    </div>
                    ${imagesHTML}
                </div>
                <div class="review-voting">
                    <button class="vote-btn upvote" aria-label="Upvote this review">▲</button>
                    <span class="vote-score">${voteScore}</span>
                    <button class="vote-btn downvote" aria-label="Downvote this review">▼</button>
                </div>
            `;
            reviewsListEl.appendChild(reviewItem);
        });
    } else {
        reviewsListEl.innerHTML = '<li>No reviews yet. Be the first!</li>';
    }
}
    if (commentFormEl) {
        commentFormEl.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = commentTextInputEl.value.trim();
            if (!text || !currentRouteId) return;
            try {
                const res = await fetch(`/api/routes/${currentRouteId}/comments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                if (!res.ok) throw new Error('Failed to post comment');
                fetchRouteData(currentRouteId);
                commentTextInputEl.value = '';
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        });
    }
      
    const reviewFormEl = document.getElementById('reviewForm');

    if (reviewFormEl) {
        reviewFormEl.addEventListener('submit', async (e) => {
            e.preventDefault(); 
            
            const submitButton = reviewFormEl.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Submitting...';

            const formData = new FormData(reviewFormEl);

            try {
                const response = await fetch(`/api/routes/${currentRouteId}/reviews`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to submit review.');
                }
                alert('Thank you! Your review has been submitted.');
                window.location.reload(); 

            } catch (err) {
                alert(`Error: ${err.message}`);
                submitButton.disabled = false;
                submitButton.textContent = 'Submit Review';
            }
        });
    }

    const commentsListElForClicks = document.getElementById('commentsList');
    if (commentsListElForClicks) {
        commentsListElForClicks.addEventListener('click', async (e) => {
            const voteButton = e.target.closest('.vote-btn');
            
            if (!voteButton) {
                return;
            }

            e.preventDefault();

            const reviewItem = voteButton.closest('.comment-item');
            const reviewId = reviewItem.dataset.reviewId;
            const direction = voteButton.classList.contains('upvote') ? 'up' : 'down';

            try {
                const response = await fetch(`/api/reviews/${reviewId}/vote`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ direction: direction })
                });
                
                if (response.status === 401 || !response.ok) {
                    if (confirm("You must be logged in to vote. Would you like to log in now?")) {
                        window.location.href = '/login';
                    }
                    if (response.status !== 401) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to register vote.');
                    }
                    return;
                }

                const data = await response.json();
                
                if (data.success) {
                    const scoreElement = reviewItem.querySelector('.vote-score');
                    scoreElement.textContent = data.new_score;

                    const upvoteBtn = reviewItem.querySelector('.upvote');
                    const downvoteBtn = reviewItem.querySelector('.downvote');

                    upvoteBtn.classList.remove('voted-up');
                    downvoteBtn.classList.remove('voted-down');

                    if (direction === 'up') {
                        upvoteBtn.classList.add('voted-up');
                    } else {
                        downvoteBtn.classList.add('voted-down');
                    }
                }

            } catch (err) {
                console.error("Voting error:", err);
                alert(`Error: ${err.message}`);
            }
        });
    }

    const sortControls = document.querySelector('.review-sort-controls');
    if (sortControls) {
        sortControls.addEventListener('click', (e) => {
            const clickedButton = e.target.closest('.sort-btn');
            if (!clickedButton || clickedButton.classList.contains('active')) {
                return;
            }
            const sortBy = clickedButton.dataset.sort;
            fetchAndDisplayReviews(currentRouteId, sortBy);
            sortControls.querySelector('.sort-btn.active').classList.remove('active');
            clickedButton.classList.add('active');
        });
    }

    // Initial fetch to start the page
    const routeId = getRouteIdFromUrl();
    if (routeId) {
        fetchRouteData(routeId);
    } 
    else {
        loadingMessageEl.style.display = 'none';
        errorMessageEl.textContent = 'No route ID found in URL.';
        errorMessageEl.style.display = 'block';
    }

    // --- Lightbox & Voting Functionality ---
   document.body.addEventListener('click', async function (event) {
    const clickedElement = event.target;
    
    // --- Part 1: Handle Thumbnail Clicks to OPEN the lightbox ---
    const isThumbnail = clickedElement.classList.contains('review-image-thumbnail') || 
                        clickedElement.classList.contains('header-gallery-thumbnail');

    if (isThumbnail) {
        event.preventDefault();
        const fullsizeUrl = clickedElement.dataset.fullsizeSrc;
        const imageId = clickedElement.dataset.imageId;
        const initialScore = clickedElement.dataset.score;

        if (fullsizeUrl && imageId) {
            const instance = basicLightbox.create(`
                <div class="image-lightbox-container">
                    <img src="${fullsizeUrl}" alt="Full size route image">
                    <div class="lightbox-controls">
                        <button class="vote-btn lightbox-vote-btn upvote" data-direction="up" data-image-id="${imageId}">▲</button>
                        <span class="vote-score lightbox-score">${initialScore}</span>
                        <button class="vote-btn lightbox-vote-btn downvote" data-direction="down" data-image-id="${imageId}">▼</button>
                    </div>
                </div>
            `);
            instance.show();
        }
    }

    // --- Part 2: Handle Vote Button Clicks INSIDE the lightbox ---
    const isVoteButton = clickedElement.classList.contains('lightbox-vote-btn');

    if (isVoteButton) {
        event.preventDefault();
        const imageId = clickedElement.dataset.imageId;
        const direction = clickedElement.dataset.direction;

        try {
            const response = await fetch(`/api/images/${imageId}/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: direction })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    if (confirm("You must be logged in to vote. Log in now?")) {
                        window.location.href = '/login';
                    }
                    return;
                }
                throw new Error('Vote failed.');
            }
            
            const data = await response.json();
            
            const lightbox = document.querySelector('.basicLightbox');
            if (lightbox) {
                // Update the score in the lightbox
                const scoreElement = lightbox.querySelector('.lightbox-score');
                scoreElement.textContent = data.new_score;

                // --- NEW: Add/Remove 'voted' classes ---
                const upvoteBtn = lightbox.querySelector('.upvote');
                const downvoteBtn = lightbox.querySelector('.downvote');
                
                upvoteBtn.classList.remove('voted-up');
                downvoteBtn.classList.remove('voted-down');

                if (direction === 'up') {
                    upvoteBtn.classList.add('voted-up');
                } else {
                    downvoteBtn.classList.add('voted-down');
                }
                // --- END OF NEW LOGIC ---
            }

        } catch (err) {
            console.error("Image voting error:", err);
            alert("Could not register your vote at this time.");
        }
    }
// In route_profile.js, add this at the end of the DOMContentLoaded listener

    // --- Review Modal Functionality (Corrected Version) ---
    const openReviewModalBtn = document.getElementById('openReviewModalBtn');
    const closeReviewModalBtn = document.getElementById('closeReviewModalBtn');
    const reviewModal = document.getElementById('reviewModal');

    if (openReviewModalBtn && reviewModal) {
        openReviewModalBtn.addEventListener('click', () => {
            // This is now a standard JavaScript 'if' statement
            // It reads the variable we created in the HTML template
            if (IS_USER_AUTHENTICATED) {
                // If the user is logged in, show the modal
                reviewModal.classList.remove('hidden');
            } else {
                // If the user is not logged in, show the confirmation dialog
                if (confirm("You must be logged in to leave a review. Log in now?")) {
                    window.location.href = '/login';
                }
            }
        });
    }

    // This logic for closing the modal remains the same
    if (closeReviewModalBtn && reviewModal) {
        closeReviewModalBtn.addEventListener('click', () => {
            reviewModal.classList.add('hidden');
        });
    }

    if (reviewModal) {
        reviewModal.addEventListener('click', (event) => {
            if (event.target === reviewModal) {
                reviewModal.classList.add('hidden');
            }
        });
    }
  
});
});