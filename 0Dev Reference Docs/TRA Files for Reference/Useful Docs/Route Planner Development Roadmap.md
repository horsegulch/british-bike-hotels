# Route Planner Development Roadmap

This document outlines a phased approach to developing a fully integrated route planning tool within The Ride Archive. The goal is to allow users to create their own routes directly on the site, which are then automatically saved and processed.

---

## Open Source Foundation: Key Components

Building a route planner from scratch is a massive undertaking. Fortunately, we can build upon incredible open-source software. A planner has three main components:

1. **The Interactive Map (Map Library):** This is the visual map interface where users click and draw.
   
   * **Recommendation:** **[Leaflet.js](https://leafletjs.com/)**. It is a lightweight, mobile-friendly, and extremely popular open-source JavaScript library. Its biggest strength is a massive ecosystem of plugins, including ones for drawing, editing, and exporting routes as GPX files.

2. **The Routing Engine:** This is the "brain" that calculates the actual path between two points, following roads and trails. The map library itself doesn't know about roads; it just displays tiles and lines.
   
   * **Recommendation (Simple Start):** Use a **Hosted API** based on an open-source engine. Since you already use **Jawg.io** for map tiles, their **[Jawg Routing API](https://www.jawg.io/docs/routing/)** would be a perfect starting point. It uses open-source engines like Valhalla and OSRM on the backend, so you don't have to manage the complex server infrastructure yourself.
   * **Recommendation (Advanced/Self-Hosted):** **[Open Source Routing Machine (OSRM)](http://project-osrm.org/)** or **[GraphHopper](https://www.graphhopper.com/)**. These are powerful open-source routing engines that you can host on your own server. This provides more control and can be cheaper at scale, but has a significantly higher setup and maintenance overhead.

3. **The Map Tiles:** These are the visual map images themselves.
   
   * **Recommendation:** Continue using **Jawg.io** or another provider based on **OpenStreetMap (OSM)** data. Your existing setup is perfect for this.

---

## Development Roadmap

This roadmap breaks the project into four manageable phases.

### Phase 1: Basic Map and Drawing Interface

**Goal:** Create the basic page with an interactive map where a user can click to draw a simple, straight line (a "polyline"). No road routing yet.

| Category     | Task                        | Details                                                                                                                                                                                       | Status        |
|:------------ |:--------------------------- |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:------------- |
| **Backend**  | **Create Planner Route**    | In `routes.py`, create a new route `/planner` that renders a new `planner.html` template.                                                                                                     | ⚪ Not Started |
| **Frontend** | **Integrate Leaflet.js**    | In the `planner.html` template, include the Leaflet.js CSS and JS files. Create a new `static/js/planner.js` file for our custom code.                                                        | ⚪ Not Started |
| **Frontend** | **Implement Basic Drawing** | In `planner.js`, write code to initialize the Leaflet map. Add an event listener that captures user clicks on the map and draws a simple line (a `L.Polyline`) connecting the clicked points. | ⚪ Not Started |

### Phase 2: "Click-to-Route" on Roads

**Goal:** Make the planner "smart" by integrating the routing engine, so that clicking two points draws a route that follows the road network.

| Category      | Task                        | Details                                                                                                                                                                                               | Status        |
|:------------- |:--------------------------- |:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:------------- |
| **Technical** | **Sign Up for Routing API** | Choose a routing provider (e.g., Jawg.io) and get an API key. Add this key to your `.env` file and Flask config.                                                                                      | ⚪ Not Started |
| **Frontend**  | **Fetch Route from API**    | In `planner.js`, modify the click handler. When a user adds a new point, send the coordinates of the last two points to the routing API using an AJAX (Fetch) request.                                | ⚪ Not Started |
| **Frontend**  | **Display the Routed Path** | Parse the response from the routing API (which will be a series of points in GeoJSON or similar format) and draw this new, more detailed path on the Leaflet map instead of the simple straight line. | ⚪ Not Started |

### Phase 3: Full-Featured Planner UI

**Goal:** Add the essential user interface controls that make a route planner feel complete and intuitive.

| Category     | Task                    | Details                                                                                                                                                                  | Status        |
|:------------ |:----------------------- |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |:------------- |
| **UI/UX**    | **Live Stats Display**  | As the route is drawn, update a section of the page to show the total distance and estimated elevation gain in real-time. This data comes from the routing API response. | ⚪ Not Started |
| **Features** | **Undo/Redo & Clear**   | Add "Undo", "Redo", and "Clear" buttons that allow the user to easily manage the points they've added to their route.                                                    | ⚪ Not Started |
| **Features** | **Draggable Waypoints** | Allow users to drag existing points on the route to a new location. The JavaScript should then trigger a new API call to re-calculate the affected route segments.       | ⚪ Not Started |
| **Features** | **"Save Route" Button** | Add a "Save" button to the UI. For now, this button won't do anything, but it completes the planner's visual layout.                                                     | ⚪ Not Started |

### Phase 4: Backend Integration

**Goal:** Connect the frontend planner to your backend, allowing users to save their created route and have it processed by your existing Celery worker.

| Category        | Task                                 | Details                                                                                                                                                                                                                                | Status        |
|:--------------- |:------------------------------------ |:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:------------- |
| **Frontend**    | **Export Route as GPX**              | Use a Leaflet plugin (like `leaflet-gpx`) or a simple JS library to convert the final list of route coordinates from the frontend into the standard GPX file format (as a string or Blob).                                             | ⚪ Not Started |
| **Backend**     | **Create "Save Route" API Endpoint** | In `api.py`, create a new route, e.g., `POST /api/planner/save`. This endpoint will expect the GPX data to be sent from the frontend.                                                                                                  | ⚪ Not Started |
| **Integration** | **Connect Frontend to Backend**      | In `planner.js`, make the "Save" button send the generated GPX data to your new API endpoint.                                                                                                                                          | ⚪ Not Started |
| **Integration** | **Trigger Celery Task**              | In the `/api/planner/save` endpoint, save the received GPX data to a temporary file and trigger your existing `process_route_task` in the exact same way that the file upload does. The user experience will be seamless from here on. | ⚪ Not Started |
