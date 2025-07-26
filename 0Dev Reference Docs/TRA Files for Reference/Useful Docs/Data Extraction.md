### Data Extraction Strategy for Route Difficulty Inputs (v3)

This document outlines the strategy to process uploaded route files (GPX, TCX, FIT) and extract the six key metrics required by the `calculate_total_difficulty` function, incorporating specific definitions for climbs and descents based on latest decisions.

**Required Metrics:**

1. `distance_km` (Total distance)
    
2. `TEGa` (Total Elevation Gain - Ascent) - _From smoothed data_
    
3. `ACg` (Average Climb Gradient of significant climb sections) - _From smoothed data_
    
4. `MCg` (Max Climb Gradient over ~100m segment) - _From smoothed data_
    
5. `PDD` (Proportion of Distance Downhill) - _From smoothed data_
    
6. `ADg` (Average Descent Gradient of significant descent sections) - _From smoothed data_
    

**1. File Parsing Libraries (Recommendation Unchanged)**

- **GPX:** `gpxpy`
    
- **TCX:** `python-tcxparser` or similar.
    
- **FIT:** `fitparse`
    
- **Goal:** Convert raw file data into a list of track points (each with latitude, longitude, elevation, and ideally time).
    

**2. Calculating Basic Metrics from Track Point Data**

- **`distance_km` (Total Distance):**
    
    - Iterate through consecutive original track points.
        
    - Calculate Haversine distance between each pair. Sum distances. Convert to km.
        
- **`TEGa` (Total Elevation Gain - Ascent):**
    
    - Apply **elevation smoothing** (e.g., moving average, window size 7) to the raw elevation data.
        
    - Iterate through consecutive **smoothed** track points.
        
    - Sum all positive elevation changes (`elevation_point_B - elevation_point_A`).
        
- **`PDD` (Proportion of Distance Downhill):**
    
    - Use the **smoothed** elevation data.
        
    - Iterate through consecutive points.
        
    - If `elevation_point_B < elevation_point_A` (a descending segment):
        
        - Calculate the distance of this segment (using original lat/lon).
            
        - Add this segment distance to `total_downhill_distance_km`.
            
    - `PDD = total_downhill_distance_km / distance_km` (if `distance_km > 0`, else 0).
        

**3. Calculating Gradient-Based Metrics (`ACg`, `MCg`, `ADg`) from Smoothed Data**

- **General Pre-processing:** Use the **smoothed** elevation profile for all gradient calculations.
    
- **`ACg` (Average Climb Gradient of Significant Climb Sections):**
    
    1. **Identify "Significant Climb" Segments:**
        
        - A continuous segment of the route (using smoothed elevation) meeting ALL criteria:
            
            - `climb_segment_distance_meters * average_gradient_of_segment >= 3500`
                
            - `climb_segment_distance_meters >= 250`
                
            - `average_gradient_of_segment >= 3%`
                
    2. **Process Segments:** Iterate through the route, identify all such segments, and calculate their individual average gradients.
        
    3. **Calculate `ACg`:** Average of the individual significant climb gradients. If none found, `ACg = 0`.
        
- **`MCg` (Max Climb Gradient over ~100m segment):**
    
    1. **Rolling Window Analysis:** Iterate through the **smoothed** track points, creating rolling/consecutive segments of approximately **100 meters**.
        
    2. **Calculate Segment Gradient:** Calculate the average gradient for each ~100m segment.
        
    3. **Determine `MCg`:** The maximum positive gradient found among all analyzed segments whose actual distance is at least **50 meters**. If all segments are flat/downhill, `MCg = 0`.
        
- **`ADg` (Average Descent Gradient of Significant Descent Sections):**
    
    1. **Identify "Significant Descent" Segments:**
        
        - A continuous segment of the route (using smoothed elevation) meeting ALL criteria:
            
            - `average_gradient_of_segment <= -3%`
                
            - `descent_segment_distance_meters >= 500m`
                
    2. **Process Segments:** Iterate through the route, identify all such segments, and calculate their individual average gradients (will be negative).
        
    3. **Calculate `ADg`:** Average of the _absolute values_ of the individual significant descent gradients. If none found, `ADg = 0`.
        

**4. Implementation Notes (Unchanged)**

- Logic for identifying continuous segments requires careful iteration and state management.
    
- Order of operations: parse -> smooth elevation -> calculate all metrics from appropriate (original or smoothed) data.