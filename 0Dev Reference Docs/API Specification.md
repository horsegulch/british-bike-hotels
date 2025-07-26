# API Specification: BritishBikeHotels.com

This document defines the key API endpoints for the application.

---

### **`GET /api/map-data`**

- **Description:** Retrieves all necessary data to initialize the main homepage map, including hotels and featured routes. Designed to be a single, efficient call on page load.
- **Response `200 OK`:**
  
  ```json
  {
    "hotels": [
      {
        "_id": "60f5c3b3e2a7b8e8f8c7a6f2",
        "name": "The Grand Brighton",
        "location": { "type": "Point", "coordinates": [-0.1410, 50.8225] },
        "is_featured": true
      },
      {
        "_id": "60f5c3b3e2a7b8e8f8c7a6f3",
        "name": "Artist Residence Brighton",
        "location": { "type": "Point", "coordinates": [-0.1478, 50.8214] },
        "is_featured": false
      }
    ]
  }
  ```

---

### **`GET /api/hotel/<hotel_id>`**

- **Description:** Fetches the full profile for a single hotel, including its associated routes and approved community photos.
- **Response `200 OK`:**
  
  ```json
  {
    "_id": "60f5c3b3e2a7b8e8f8c7a6f2",
    "name": "The Grand Brighton",
    "description": "A historic Victorian hotel on the seafront...",
    "website": "[https://www.grandbrighton.co.uk/](https://www.grandbrighton.co.uk/)",
    "phone": "01273 224300",
    "location": { "type": "Point", "coordinates": [-0.1410, 50.8225] },
    "is_featured": true,
    "routes": [
      {
        "_id": "r1",
        "name": "Brighton Seafront Cruise",
        "distance_km": 15,
        "elevation_m": 50
      }
    ],
    "user_photos": [
      { "image_url": "/static/uploads/photo123.jpg", "user_name": "Chris F." }
    ]
  }
  ```

---

### **`POST /api/tracking/event`**

- **Description:** A fire-and-forget endpoint for tracking user interactions for analytics.
- **Request Body:**
  
  ```json
  {
    "event_type": "profile_view", // or "website_click", "route_download", "inquiry_sent"
    "hotel_id": "60f5c3b3e2a7b8e8f8c7a6f2"
  }
  ```
- **Response `204 No Content`**

---

### **`POST /api/itinerary/add`**

- **Description:** Adds an item (hotel or route) to the user's session-based trip plan.
- **Request Body:**
  
  ```json
  {
    "session_id": "unique_session_identifier",
    "item_type": "hotel", // or "route"
    "item_id": "60f5c3b3e2a7b8e8f8c7a6f2"
  }
  ```
- **Response `200 OK`:**
  
  ```json
  {
    "success": true,
    "item_count": 3
  }
  ```
