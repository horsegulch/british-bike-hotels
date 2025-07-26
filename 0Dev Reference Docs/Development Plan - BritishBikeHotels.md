# Development Plan: BritishBikeHotels.com

## 1. Project Vision & Core Technologies

- **Vision:** A modern, immersive, map-centric web application for cyclists to discover bike-friendly hotels. The platform will feature SEO-rich content, powerful trip-planning tools, community features, and provide valuable analytics and promotional opportunities to partner hotels.
- **Primary Technologies:**
  - **Backend:** Python (Flask)
  - **Database:** MongoDB
  - **Frontend:** HTML, CSS, JavaScript
  - **Mapping Library:** Leaflet.js
  - **Key Python Libraries:** `Flask-PyMongo`, `Flask-Login`, `gpxpy`, `pyotp`, `Flask-Bcrypt`
  - **Key JS Libraries:** `Leaflet.markercluster`, `Chart.js`

---

## Phase 0: UI/UX Design & Style Guide

*Goal: Define the visual identity and user interaction patterns to ensure a polished, professional, and consistent user experience.*

### Task 0.1: Define Core Aesthetics

1. **Theme:** "Premium Adventure"

2. **Color Palette:**
   
   - **Primary:** Slate Blue / Charcoal (`#2c3e50`)
   - **Accent:** Amber / Gold (`#ffc107`)
   - **Background:** Light Off-White (`#f8f9fa`)

3. **Typography:**
   
   - **Headings & UI:** Montserrat or Poppins
   
   - **Body & Descriptions:** Merriweather or Lora
     
     ### Task 0.2: Design Key UI Components & Interactions

4. **Homepage:** Full-page map with a floating, semi-transparent "frosted glass" navbar.

5. **Filters:** A primary search bar in the navbar, with an adjacent "Filters" button that smoothly reveals an advanced filter panel.

6. **Onboarding:** A "Welcome" modal on the first visit of a session.

7. **Map Interaction:** Custom markers that change color and show routes on hover. Clicking a marker opens a slide-in sidebar with hotel summary info.

---

## Phase 1: Project Scaffolding & Backend Core (The Foundation)

*Goal: Set up the project structure, establish a database connection, define data models, and create the basic API endpoints.*

### Task 1.1: Project & Environment Setup

- Create the project directory, virtual environment, and initial file structure (including new blueprints for `blog.py`, `tracking.py`, and `planner.py`).

- Install initial dependencies: `Flask`, `Flask-PyMongo`, `gpxpy`, `python-dotenv`.
  
  ### Task 1.2: Database Schema Definition (MongoDB)
  
  *Define the structure for all data collections.*
1. **`hotels` Collection:**
   
   - Add `is_featured` (Boolean) field for promotions.
   - Schema otherwise as previously defined.

2. **`routes` Collection:**
   
   - Add `surface_type` (String: 'Road', 'Gravel', 'Mixed') and `tags` (Array of Strings) fields to enable filtering.

3. **`reviews` Collection:** (No changes)

4. **`blog_posts` Collection:** (No changes)

5. **`analytics_events` Collection:**
   
   - Add `inquiry_sent` and `photo_submission` to `event_type`.

6. **<!-- NEW --> `points_of_interest` Collection:**
   
   ```json
   {
   "_id": "ObjectID",
   "route_id": "ObjectID", // Can be linked to a specific route
   "name": "String",
   "type": "String ('cafe', 'pub', 'viewpoint', 'bike_shop')",
   "location": { "type": "Point", "coordinates": [ <lon>, <lat> ] }
   }
   ```

7. **<!-- NEW --> `user_photos` Collection:**
   
   ```json
   {
   "_id": "ObjectID",
   "hotel_id": "ObjectID",
   "user_name": "String",
   "image_url": "String",
   "status": "String ('pending', 'approved')",
   "uploaded_at": "ISODate"
   }
   ```

8. **<!-- NEW --> `itineraries` Collection:**
   
   ```json
   {
   "_id": "ObjectID",
   "session_id": "String", // To link to a user's browser session
   "name": "String",
   "items": [
   { "type": "String ('hotel' or 'route')", "item_id": "ObjectID" }
   ],
   "created_at": "ISODate"
   }
   ```
   
   ### Task 1.3: Core API Endpoints
- Implement `api.py` endpoints as previously defined.
- Implement `tracking.py` endpoint as previously defined.
- **<!-- NEW -->** Create endpoints for itinerary management (`GET`, `POST /add`, `POST /remove`).
- **<!-- NEW -->** Create an endpoint for the direct booking inquiry form (`POST /api/hotel/<hotel_id>/inquiry`) which will trigger an email.

---

## Phase 2: Admin Portal & Data Management

*Goal: Build a secure area for an administrator to manage all site content.*

### Task 2.1: Admin Authentication with MFA

- Implement the full username/password + TOTP login flow.
  
  ### Task 2.2: Hotel Management (CRUD)

- Enhance the "Add/Edit Hotel" form to include a checkbox for **"Mark as Featured"**.

- Implement route management (GPX upload/parsing) and deletion.
  
  ### Task 2.3: Blog Content Management

- Build the interface for creating, editing, and publishing blog posts.
  
  ### Task 2.4: <!-- NEW --> Content Moderation & Management
1. **User Photo Approval:** Create a moderation queue page (`/admin/moderation`) that lists all user-submitted photos with `status: 'pending'`. Admin can approve or reject.
2. **POI Management:** Create an interface for the admin to add, edit, and delete Points of Interest and associate them with routes.

---

## Phase 3: Frontend Development & User Experience

*Goal: Build the public-facing website based on the UI/UX plan.*

### Task 3.1: Homepage Map Implementation

- Implement the full-page map, floating navbar, and filter panel.

- Implement the welcome modal and all map interactions.

- **"Featured" hotels should have a distinct, more prominent map marker** (e.g., with a gold border).
  
  ### Task 3.2: Hotel & Route Profile Pages

- Build the `hotel_profile.html` and `route_profile.html` templates.

- **<!-- NEW -->** On the hotel profile page, add the **"Direct Booking Inquiry"** form.

- **<!-- NEW -->** Add a community photo gallery section to display approved user-submitted photos.

- **<!-- NEW -->** Add an "Add to Trip" button on both hotel and route profiles.
  
  ### Task 3.3: Public Blog Section

- Build the blog index and individual post pages.
  
  ### Task 3.4: <!-- NEW --> Advanced User & Planning Tools
1. **Advanced Route Filtering:** On a hotel's profile page, add controls to filter its list of routes by distance, elevation, and surface type.
2. **"My Trip" Itinerary Page:** Create a new template (`/my-trip`) that fetches the user's saved itinerary items via the API and displays them in a clean list.
3. **POI Display:** On the route profile map, fetch and display all associated POI icons.

---

## Phase 4: Content Strategy, Reporting & Deployment

*Goal: Add high-value content and commercial features, and prepare the application for a live audience.*

### Task 4.1: Hotel Self-Service Form

- Implement the token-generation system and the public-facing onboarding form.

- Create the admin approval queue for hotel-submitted content.
  
  ### Task 4.2: Hotel Analytics & Reporting

- Build the `/admin/hotel/<hotel_id>/report` view and template.

- Implement the backend logic using MongoDB Aggregation to generate statistics on profile views, website clicks, route downloads, and inquiries.

- Use `Chart.js` to visualize the data.
  
  ### Task 4.3: <!-- NEW --> Content & SEO Strategy
1. **Regional Cycling Guides:** Use the blog system to create long-form, SEO-focused guides for key cycling regions (e.g., "A Cyclist's Guide to the Peak District").

2. **Internal Linking:** These guides will strategically link to multiple hotel and route profiles within that region, driving traffic and boosting search rankings.
   
   ### Task 4.4: Deployment
- Prepare the Flask application for production and deploy to a PaaS or VPS.
- Configure DNS.
