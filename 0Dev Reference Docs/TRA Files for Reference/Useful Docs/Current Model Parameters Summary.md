### Current Model Parameters Summary (v3 - 2025-05-08)

This document lists all the constants, thresholds, and weights currently used in the cycling route difficulty model and the associated metric extraction process. The model produces an **uncapped** final score (minimum 0.0).

**I. Metric Extraction Configuration**

- **Elevation Smoothing:**
    
    - `SMOOTHING_WINDOW_SIZE`: `7` (points for moving average)
        
- **MCg (Max Climb Gradient) Calculation:**
    
    - `MCG_SEGMENT_TARGET_DISTANCE_M`: `100.0` (meters) - Target length of segment to find max gradient over.
        
    - `MIN_DIST_FOR_MCG_GRADIENT_CALC_M`: `50.0` (meters) - Minimum actual segment distance required to calculate gradient for MCg.
        
- **ACg (Significant Climb) Identification:**
    
    - `SIG_CLIMB_FACTOR_THRESHOLD`: `3500.0` (distance_m * avg_gradient_percent)
        
    - `SIG_CLIMB_MIN_DISTANCE_M`: `250.0` (meters)
        
    - `SIG_CLIMB_MIN_GRADIENT_PERCENT`: `3.0` (%)
        
    - `POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD`: `1.0` (%)
        
- **ADg (Significant Descent) Identification:**
    
    - `SIG_DESCENT_MIN_DISTANCE_M`: `500.0` (meters)
        
    - `SIG_DESCENT_MIN_GRADIENT_PERCENT`: `-3.0` (%)
        
    - `POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD`: `-1.0` (%)
        

**II. Difficulty Calculation - Distance Component**

- **`DISTANCE_BASE_ADDITION`**: `5.0`
    
- **`DISTANCE_DIFFICULTY_COEFFICIENT_A`**: `0.005`
    
    - _Formula: `Distance_Difficulty = DISTANCE_BASE_ADDITION + (DISTANCE_DIFFICULTY_COEFFICIENT_A * distance_km²)`_
        

**III. Difficulty Calculation - Uphill Impact Component (Linear UF Model)**

- **Normalization Maximums (for Uphill Score `US` calculation):**
    
    - `MAX_EXPECTED_TEGA` (Total Elevation Gain - Ascent): `3500.0` meters
        
    - `MAX_EXPECTED_ACG` (Average Climb Gradient): `12.0` %
        
    - `MAX_EXPECTED_MCG` (Max Climb Gradient): `20.0` % _(Note: This normalizes the calculated MCg value)_
        
- **Weights for Uphill Score (`US`):**
    
    - `WEIGHT_TEGA`: `0.50` (50%)
        
    - `WEIGHT_ACG`: `0.40` (40%)
        
    - `WEIGHT_MCG`: `0.10` (10%)
        
- **Uphill Factor (`UF`) Calculation:**
    
    - `LINEAR_UF_SLOPE`: `0.6`
        
        - _Formula: `UF = 1 + (LINEAR_UF_SLOPE * US)`_
            
        - _Max UF = 1.6_
            

**IV. Difficulty Calculation - Downhill Reduction Component**

- **Qualifying Conditions for Downhill Reduction:**
    
    - `PDD_THRESHOLD`: `0.65`
        
    - `MAX_ASCENT_FOR_DOWNHILL_REDUCTION`: `1000.0` meters
        
    - `MIN_AVG_DESCENT_GRADIENT_THRESHOLD`: `3.0` % _(Based on calculated ADg)_
        
- **Normalization Targets (for Downhill Score `DS` calculation):**
    
    - `TARGET_ADG_FOR_MAX_REDUCTION`: `7.0` %
        
- **Weights for Downhill Score (`DS`):**
    
    - `WEIGHT_PDD_SCORE`: `0.7` (70%)
        
    - `WEIGHT_ADG_SCORE`: `0.3` (30%)
        
- **Downhill Reduction Factor (`DRF`) Calculation:**
    
    - `MAX_DOWNHILL_REDUCTION_FACTOR`: `0.8`
        
        - _Formula: `DRF = MAX_DOWNHILL_REDUCTION_FACTOR ^ DS` (Max 20% reduction)_
            

**V. Final Score Output**

- **`MIN_DIFFICULTY_SCORE`**: `0.0`
    
- **Score Capping**: **Uncapped** on the upper end.