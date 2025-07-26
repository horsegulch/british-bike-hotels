

This model calculates an Elevation Factor (EF) which is then multiplied by the base `Distance_Difficulty` to get the `Total_Difficulty`. `Total_Difficulty = Distance_Difficulty * EF`

The `Distance_Difficulty` is calculated as: `Difficulty(distance) = 0.00249975 * distance²` (for a 0-100 scale, max 99.99 at 200km).

The Elevation Factor (EF) is composed of an Uphill Factor (UF) and a Downhill Reduction Factor (DRF): `EF = UF * DRF`

**Part 1: Uphill Impact Component => Uphill Factor (UF)**

1. **Input Metrics from Ride Data:**
    
    - `TEGa`: Total Elevation Gain - Ascent (meters)
        
    - `ACg`: Average Climb Gradient of climbing sections (%)
        
    - `MCg`: Max Climb Gradient encountered (%)
        
2. **Normalization Parameters:**
    
    - `max_expected_TEGa`: **3500m**
        
    - `max_expected_ACg`: **12%**
        
    - `max_expected_MCg`: **20%**
        
3. **Calculate Normalized Uphill Metrics:**
    
    - `TEGa_norm = min(TEGa / max_expected_TEGa, 1.0)`
        
    - `ACg_norm = min(ACg / max_expected_ACg, 1.0)`
        
    - `MCg_norm = min(MCg / max_expected_MCg, 1.0)`
        
4. **Calculate Uphill Score (`US`):**
    
    - Weights: 50% TEGa, 40% ACg, 10% MCg
        
    - `US = (0.50 * TEGa_norm) + (0.40 * ACg_norm) + (0.10 * MCg_norm)`
        
        - (US ranges from 0 to 1)
            
5. **Calculate Uphill Factor (`UF`):**
    
    - `Max_Uphill_Impact_Factor`: **2.5**
        
    - `UF = Max_Uphill_Impact_Factor ^ US`
        
        - (If US=0, UF=1. If US=1, UF=2.5)
            

**Part 2: Downhill Reduction Component => Downhill Reduction Factor (DRF)**

1. **Input Metrics from Ride Data:**
    
    - `PDD`: Proportion of Distance Downhill (0 to 1)
        
    - `TEGa`: Total Elevation Gain - Ascent (meters) (used for a condition)
        
    - `ADg`: Average Descent Gradient of descending sections (e.g., -5% is input as 5 for `abs(ADg)`)
        
2. **Qualifying Conditions for Downhill Reduction (ALL must be TRUE):**
    
    - **Condition A (Sufficient Downhill Distance):**
        
        - `PDD_Threshold`: **0.65**
            
        - `PDD > PDD_Threshold` (i.e., `PDD > 0.65`)
            
    - **Condition B (Limited Total Ascent):**
        
        - `Max_Ascent_For_Downhill_Reduction`: **1000m**
            
        - `TEGa < Max_Ascent_For_Downhill_Reduction` (i.e., `TEGa < 1000m`)
            
    - **Condition C (Effective Descents):**
        
        - `Min_Average_Descent_Gradient_Threshold`: **3%**
            
        - `abs(ADg) > Min_Average_Descent_Gradient_Threshold` (i.e., `abs(ADg) > 3%`)
            
3. **If ALL Qualifying Conditions are TRUE, Calculate Downhill Score (`DS`):**
    
    - **PDD Score Normalization:**
        
        - `PDD_Score_Norm = (PDD - PDD_Threshold) / (1.0 - PDD_Threshold)`
            
        - `PDD_Score_Norm = min(max(PDD_Score_Norm, 0), 1)` (Clamped between 0 and 1)
            
    - **ADg Score Normalization:**
        
        - `Target_ADg_For_Max_Reduction`: **7%**
            
        - `ADg_Score_Norm = (abs(ADg) - Min_Average_Descent_Gradient_Threshold) / (Target_ADg_For_Max_Reduction - Min_Average_Descent_Gradient_Threshold)`
            
        - `ADg_Score_Norm = min(max(ADg_Score_Norm, 0), 1)` (Clamped between 0 and 1)
            
    - **Combine for Downhill Score (`DS`):**
        
        - `w_pdd` (Weight for PDD Score): **0.7**
            
        - `w_adg` (Weight for ADg Score): **0.3**
            
        - `DS = (w_pdd * PDD_Score_Norm) + (w_adg * ADg_Score_Norm)`
            
            - (DS ranges from 0 to 1)
                
4. **Calculate Downhill Reduction Factor (`DRF`):**
    
    - `Max_Downhill_Reduction_Factor`: **0.25**
        
    - If ALL Qualifying Conditions were TRUE:
        
        - `DRF = Max_Downhill_Reduction_Factor ^ DS`
            
            - (If DS=0, DRF=1 (since 0.25^0 = 1). If DS=1, DRF=0.25. Note: this means more "downhillness" (DS closer to 1) leads to a _smaller_ DRF value, which is correct for reduction. The formula `Base ^ Score` where Base < 1 behaves such that a higher score means a _smaller_ result. For example, `0.25^0 = 1`, `0.25^0.5 = 0.5`, `0.25^1 = 0.25`. This is the desired behavior.)
                
    - If ANY Qualifying Condition was FALSE:
        
        - `DRF = 1.0` (No reduction)
            

**Part 3: Final Calculation**

1. **Calculate Elevation Factor (`EF`):**
    
    - `EF = UF * DRF`
        
2. **Calculate Total Difficulty:**
    
    - `Distance_Difficulty = 0.00249975 * distance_km²`
        
    - `Total_Difficulty = Distance_Difficulty * EF`
        
    - The `Total_Difficulty` should then be capped (e.g., at 0 and 100, or just ensure it doesn't go below a minimum like 1 if it's not 0km).