## 1. Project Overview

The Cycling Route Difficulty Rating System is a web application that evaluates cycling routes and assigns them a difficulty score based on various factors such as distance, elevation gain, surface type, and more. The system will process route data from GPX/TCX files or popular cycling platforms' APIs, calculate a comprehensive difficulty score, and present it to users along with a breakdown of contributing factors.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Frontend (SPA)  | <-> |  Backend API     | <-> |  External APIs   |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                               |
                               v
                         +------------------+
                         |                  |
                         |  Database        |
                         |                  |
                         +------------------+
```

### 2.2 Technology Stack

#### Frontend:

- **Framework**: React.js
- **State Management**: React Context API (can upgrade to Redux later if needed)
- **UI Framework**: Tailwind CSS
- **Build Tool**: Vite

#### Backend:

- **Runtime**: Node.js
- **Framework**: Express.js
- **File Processing**: gpxparser, tcx-js
- **Authentication**: JWT (for future user accounts)

#### Database:

- **Initial Phase**: MongoDB (flexible schema for rapid iteration)
- **Future Consideration**: PostgreSQL with PostGIS for advanced geospatial queries

#### Deployment:

- **Frontend**: Vercel or Netlify
- **Backend**: Render, Railway, or Heroku
- **Database**: MongoDB Atlas or similar managed service

## 3. Core Features & Requirements

### 3.1 MVP Features

1. **Route Input**:
    
    - GPX/TCX file upload
    - URL input for routes from Strava, RideWithGPS, Komoot
2. **Route Analysis**:
    
    - Distance calculation
    - Elevation gain analysis
    - Surface type determination (where data available)
3. **Difficulty Scoring**:
    
    - Customizable difficulty algorithm
    - Adjustable based on rider level
4. **Results Display**:
    
    - Overall difficulty score (e.g., 1-10 scale)
    - Visual breakdown of contributing factors
    - Interactive route map
    - Elevation profile

### 3.2 Post-MVP Features

1. **User Accounts**:
    
    - Saved routes
    - Personalized difficulty settings
2. **Integration with Cycling Platforms**:
    
    - OAuth integration with Strava, RideWithGPS
    - Import user history for personalized scoring
3. **Route Recommendations**:
    
    - Suggest routes matching user preferences and ability
4. **Social Features**:
    
    - Share routes with custom difficulty ratings
    - Discuss route experiences

## 4. Difficulty Scoring Algorithm

### 4.1 Core Algorithm

The difficulty score will be calculated as a weighted sum of factors:

```
DifficultyScore = 
    (w₁ × distanceFactor) + 
    (w₂ × elevationGainFactor) + 
    (w₃ × surfaceTypeFactor) + 
    (w₄ × steepSegmentsFactor) + 
    (w₅ × weatherExposureFactor) + 
    (w₆ × trafficFactor) + 
    (w₇ × resourceAvailabilityFactor)
```

Where `w₁` through `w₇` are weights that will be calibrated based on user feedback and analysis of known routes.

### 4.2 Factor Calculation

Each factor will be normalized to a 0-1 scale:

1. **Distance Factor**:
    
    ```
    distanceFactor = min(distance / referenceDistance, 1)
    ```
    
    Where `referenceDistance` varies by rider level (e.g., 100km for intermediate)
    
2. **Elevation Gain Factor**:
    
    ```
    elevationGainFactor = min(elevationGain / referenceElevation, 1)
    ```
    
    Where `referenceElevation` varies by rider level (e.g., 1000m for intermediate)
    
3. **Surface Type Factor**:
    
    ```
    surfaceTypeFactor = surfaceTypeScore / maxSurfaceTypeScore
    ```
    
    Where surface types are scored (e.g., paved=1, gravel=2, singletrack=3)
    

Similar calculations will be made for other factors.

### 4.3 Rider Level Adjustment

Five rider levels will be supported:

- Beginner
- Recreational
- Intermediate
- Advanced
- Professional

Each level will have different reference values and weights for the algorithm.

## 5. Data Processing Pipeline

### 5.1 GPX/TCX Processing

1. Parse file to extract track points
2. Calculate distance using Haversine formula between consecutive points
3. Calculate elevation gain (filtering noise)
4. Analyze grade distribution
5. Identify steep segments

### 5.2 API Integration

#### 5.2.1 Strava API

- Route details extraction
- Surface type identification
- Weather data correlation

#### 5.2.2 RideWithGPS API

- Route import
- Elevation data enhancement

#### 5.2.3 Komoot API

- Route details
- Surface type data

## 6. User Interface Design

### 6.1 Main Components

1. **Route Input Component**:
    
    - File drag & drop area
    - URL input field
    - Platform connection buttons
2. **Rider Profile Component**:
    
    - Experience level selection
    - Personal preferences
    - Physical characteristics (optional)
3. **Results Dashboard**:
    
    - Primary difficulty score display
    - Factor breakdown visualization
    - Interactive route map
    - Elevation profile chart
4. **Recommendations Component**:
    
    - Similar routes suggestion
    - Training progression recommendations

## 7. API Endpoints

### 7.1 Backend API

|Endpoint|Method|Description|
|---|---|---|
|`/api/routes/analyze`|POST|Analyze route from file upload|
|`/api/routes/analyze-url`|POST|Analyze route from external URL|
|`/api/routes/:id`|GET|Get saved route details|
|`/api/users/profile`|GET|Get user profile (future)|
|`/api/users/profile`|PUT|Update user profile (future)|

### 7.2 External API Usage

1. **Strava API**:
    
    - Authentication: OAuth 2.0
    - Key endpoints: route details, segment details
2. **RideWithGPS API**:
    
    - Authentication: API key
    - Key endpoints: route details, elevation data
3. **Open Weather Map API**:
    
    - Historical weather data for routes

## 8. Project Implementation Plan

### Phase 1: Foundation (Weeks 1-3)

- [x]  Set up project repositories
- [ ]  Create basic React frontend structure
- [ ]  Set up Express backend
- [ ]  Implement GPX/TCX file parsing
- [ ]  Develop distance and elevation calculation
- [ ]  Create basic difficulty algorithm
- [ ]  Build simple UI for file upload and results

### Phase 2: Core Functionality (Weeks 4-6)

- [ ]  Implement URL input for external routes
- [ ]  Develop route visualization
- [ ]  Build rider level adjustment
- [ ]  Enhance algorithm with surface type analysis
- [ ]  Create detailed results breakdown UI
- [ ]  Add basic error handling

### Phase 3: Integration & Enhancement (Weeks 7-10)

- [ ]  Integrate Strava API
- [ ]  Integrate RideWithGPS API
- [ ]  Implement weather factor analysis
- [ ]  Add traffic density estimation
- [ ]  Build interactive map features
- [ ]  Create responsive UI for mobile devices

### Phase 4: Refinement & Deployment (Weeks 11-12)

- [ ]  Algorithm calibration based on test routes
- [ ]  Performance optimization
- [ ]  Comprehensive error handling
- [ ]  Security review
- [ ]  Deploy MVP
- [ ]  Set up analytics

### Phase 5: Post-MVP (Future)

- [ ]  Implement user accounts
- [ ]  Add route recommendations
- [ ]  Develop personalized scoring
- [ ]  Create social sharing features
- [ ]  Build route planning capabilities

## 9. Data Models

### 9.1 Route Model

```javascript
{
  id: String,
  name: String,
  source: String, // 'file', 'strava', 'ridewithgps', 'komoot'
  sourceId: String,
  points: [
    {
      lat: Number,
      lng: Number,
      elevation: Number,
      distance: Number, // cumulative distance
      time: Date // optional
    }
  ],
  stats: {
    totalDistance: Number,
    totalElevationGain: Number,
    maxElevation: Number,
    minElevation: Number,
    averageGrade: Number,
    steepSegmentsCount: Number
  },
  surfaceInfo: {
    paved: Number, // percentage
    gravel: Number,
    dirt: Number,
    unknown: Number
  },
  difficultyScore: {
    overall: Number,
    factors: {
      distance: Number,
      elevation: Number,
      surface: Number,
      steepness: Number,
      weather: Number,
      traffic: Number,
      resources: Number
    }
  },
  createdAt: Date,
  userId: String // optional, for logged in users
}
```

### 9.2 User Model (Future)

```javascript
{
  id: String,
  email: String,
  passwordHash: String,
  profile: {
    displayName: String,
    riderLevel: String, // 'beginner', 'recreational', 'intermediate', 'advanced', 'professional'
    preferences: {
      preferredSurface: String,
      maxDistance: Number,
      maxElevation: Number
    }
  },
  connections: {
    strava: {
      connected: Boolean,
      accessToken: String,
      refreshToken: String,
      expiresAt: Date
    },
    ridewithgps: {
      connected: Boolean,
      accessToken: String
    }
  },
  savedRoutes: [String], // references to Route IDs
  createdAt: Date,
  updatedAt: Date
}
```

## 10. Security Considerations

### 10.1 Authentication & Authorization

- JWT-based authentication for user accounts
- API rate limiting to prevent abuse
- Secure token storage

### 10.2 Data Protection

- HTTPS for all connections
- PII encryption
- API token security for third-party services

### 10.3 Input Validation

- File size and type validation
- URL validation
- Data sanitization

## 11. Testing Strategy

### 11.1 Unit Testing

- Algorithm component tests
- File processing tests
- API endpoint tests

### 11.2 Integration Testing

- End-to-end route analysis flow
- API integration tests
- Database interaction tests

### 11.3 Performance Testing

- File processing efficiency
- API response times
- Algorithm calculation speed

## 12. Maintenance & Monitoring

### 12.1 Logging

- Request logging
- Error logging
- Performance metrics

### 12.2 Monitoring

- Uptime monitoring
- Performance monitoring
- Error rate tracking

### 12.3 Backup Strategy

- Database regular backups
- Configuration backups
- Disaster recovery plan

## 13. Launch Strategy

### 13.1 Initial Release

- Private beta with cycling clubs
- Feedback collection system
- Algorithm calibration period

### 13.2 Public Launch

- Product hunt launch
- Cycling forum announcements
- Social media campaign

## 14. Metrics for Success

### 14.1 Technical Metrics

- Average processing time < 2 seconds
- Uptime > 99.9%
- Error rate < 0.5%

### 14.2 User Metrics

- User growth rate
- Route analysis count
- User retention
- Score accuracy satisfaction

## 15. Resources & References

### 15.1 API Documentation

- [Strava API Documentation](https://developers.strava.com/)
- [RideWithGPS API Documentation](https://ridewithgps.com/api)
- [OpenWeatherMap API Documentation](https://openweathermap.org/api)

### 15.2 Technical Libraries

- [GPX Parser](https://github.com/Luuka/GPXParser.js)
- [TCX Parser](https://github.com/tcx-js/tcx-js)
- [React Leaflet](https://react-leaflet.js.org/) for maps
- [Recharts](https://recharts.org/) for data visualization

### 15.3 Cycling References

- [UCI Road Categories](https://www.uci.org/docs/default-source/rules-and-regulations/part-ii-road/2-roa-20200612-e.pdf)
- [Strava Relative Effort](https://support.strava.com/hc/en-us/articles/360033357354-Relative-Effort-for-Runs-Rides-and-Swims)