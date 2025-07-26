### Glossary of Difficulty Model Terms (v3 - 2025-05-08)

This glossary defines the terms and abbreviations used in the cycling route difficulty model, reflecting the latest definitions for metric extraction and calculation logic.

**I. General / Final Score**

- **`Total_Difficulty`**: The final, overall difficulty score for a route. It's calculated by multiplying the `Distance_Difficulty` by the `Elevation_Factor (EF)` and ensuring a minimum of 0.0. The score is currently **uncapped** on the upper end.
    
- **`MIN_DIFFICULTY_SCORE`**: The absolute minimum score the `Total_Difficulty` can be (currently `0.0`).
    
- **`CONCEPTUAL_MAX_DIFFICULTY_SCORE`**: A conceptual upper limit (e.g., `100.0`) that might be used for a future capped version of the model, but is not applied in the current uncapped primary model.
    

**II. Distance Component**

- **`distance_km`**: The total distance of the cycling route in kilometers.
    
- **`Distance_Difficulty`**: The base difficulty score derived from `distance_km`.
    
    - Formula: `Distance_Difficulty = DISTANCE_BASE_ADDITION + (DISTANCE_DIFFICULTY_COEFFICIENT_A * distance_km²)`
        
- **`DISTANCE_BASE_ADDITION`**: A flat value (currently `5.0`) added to the distance-based score.
    
- **`DISTANCE_DIFFICULTY_COEFFICIENT_A` (or `a`)**: The coefficient (currently `0.005`) for the quadratic term in the `Distance_Difficulty` formula.
    

**III. Elevation Factor (EF)**

The `Elevation_Factor (EF)` modifies the `Distance_Difficulty`. It is composed of an Uphill Factor (UF) and a Downhill Reduction Factor (DRF).

- **`EF = UF * DRF`**
    
    **A. Uphill Impact Component => Uphill Factor (`UF`)** This component quantifies the added difficulty due to climbing.
    
    - **`UF` (Uphill Factor)**: A multiplier (>= 1.0) that increases difficulty based on the climbing challenge. Uses a **linear model**.
        
        - Formula: `UF = 1 + (LINEAR_UF_SLOPE * US)`
            
    - **`TEGa` (Total Elevation Gain - Ascent)**: The total meters climbed on the route, typically calculated from **smoothed** elevation data.
        
    - **`ACg` (Average Climb Gradient of Significant Climb Sections)**: The average of the individual average gradients of all "Significant Climb Sections" identified on the route. If no such sections exist, `ACg = 0`.
        
    - **`MCg` (Max Climb Gradient over ~100m segment)**: The maximum positive gradient found when analyzing the route in rolling or consecutive segments of approximately 100 meters (with a minimum calculation distance of 50m). Calculated from **smoothed** elevation data. If all segments are flat or downhill, `MCg = 0`.
        
    - **"Significant Climb Segment" Criteria**: A segment identified for `ACg` calculation, meeting all of:
        
        1. `climb_segment_distance_meters * average_gradient_of_segment >= 3500`
            
        2. `climb_segment_distance_meters >= 250`
            
        3. `average_gradient_of_segment >= 3%`
            
    - **`max_expected_TEGa`**: Normalization ceiling for `TEGa` (currently `3500m`).
        
    - **`max_expected_ACg`**: Normalization ceiling for `ACg` (currently `12%`).
        
    - **`max_expected_MCg`**: Normalization ceiling for `MCg` (currently `20%`).
        
    - **`US` (Uphill Score)**: A weighted sum (0-1 scale) of the normalized `TEGa`, `ACg`, and `MCg` values.
        
        - `WEIGHT_TEGA`: `0.50`
            
        - `WEIGHT_ACG`: `0.40`
            
        - `WEIGHT_MCG`: `0.10`
            
    - **`LINEAR_UF_SLOPE`**: The slope (currently `0.6`) determining the impact of `US` on `UF`. Max `UF` is `1 + LINEAR_UF_SLOPE`.
        
    
    **B. Downhill Reduction Component => Downhill Reduction Factor (`DRF`)** This component reduces difficulty if a ride is predominantly downhill and meets certain criteria.
    
    - **`DRF` (Downhill Reduction Factor)**: A multiplier (<= 1.0) that decreases difficulty if a ride qualifies. If `DRF = 1.0`, there's no reduction.
        
        - Formula: `DRF = MAX_DOWNHILL_REDUCTION_FACTOR ^ DS`
            
    - **`PDD` (Proportion of Distance Downhill)**: The fraction of the total route distance that is spent descending (0 to 1), calculated from **smoothed** elevation data.
        
    - **`ADg` (Average Descent Gradient of Significant Descent Sections)**: The average of the _absolute values_ of the individual average gradients of all "Significant Descent Sections" identified on the route. Calculated from **smoothed** elevation data. If no such sections exist, `ADg = 0`.
        
    - **"Significant Descent Segment" Criteria**: A segment identified for `ADg` calculation, meeting all of:
        
        1. `average_gradient_of_segment <= -3%`
            
        2. `descent_segment_distance_meters >= 500m`
            
    - **Qualifying Conditions for DRF (all must be true):**
        
        1. `PDD > PDD_THRESHOLD` (currently `0.65`)
            
        2. `TEGa < MAX_ASCENT_FOR_DOWNHILL_REDUCTION` (currently `1000m`)
            
        3. `ADg > MIN_AVG_DESCENT_GRADIENT_THRESHOLD` (currently `3%`) _(Note: Comparing calculated ADg, which is positive, to the positive threshold)_
            
    - **`PDD_Threshold`**: Minimum `PDD` (currently `0.65`) for DRF eligibility.
        
    - **`MAX_ASCENT_FOR_DOWNHILL_REDUCTION`**: Max `TEGa` (currently `1000m`) for DRF eligibility.
        
    - **`MIN_AVG_DESCENT_GRADIENT_THRESHOLD`**: Minimum absolute `ADg` (currently `3%`) for DRF eligibility.
        
    - **`Target_ADg_For_Max_Reduction`**: The absolute `ADg` (currently `7%`) at which descents provide the maximum contribution to the `DS`.
        
    - **`DS` (Downhill Score)**: A weighted sum (0-1 scale) of the normalized `PDD` and `ADg` scores.
        
        - `WEIGHT_PDD_SCORE`: `0.7`
            
        - `WEIGHT_ADG_SCORE`: `0.3`
            
    - **`MAX_DOWNHILL_REDUCTION_FACTOR`**: The base (currently `0.8`) for the exponentiation that calculates `DRF` from `DS`. Max reduction is 20%.