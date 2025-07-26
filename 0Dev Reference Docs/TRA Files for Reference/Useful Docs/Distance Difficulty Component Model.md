
This model calculates the base difficulty score purely based on the distance of the route. This score is then modified by the Elevation Factor (EF) to produce the `Total_Difficulty`.

**1. Core Concept:**

- The difficulty increases quadratically with distance, meaning longer distances become disproportionately harder.
    
- The model is designed to produce a score on a 0-100 scale.
    

**2. Parameters & Formula:**

- **Input Metric:**
    
    - `distance_km`: The total distance of the route in kilometers.
        
- **Difficulty Scale:**
    
    - Minimum Difficulty: 0 (for 0 km)
        
    - Maximum Target Difficulty (`D_max`): **99.99**
        
- **Reference Maximum Distance:**
    
    - The distance at which `D_max` is achieved: **200 km**
        
- **Parabolic Coefficient (`a`):**
    
    - Calculated as: `a = D_max / (reference_max_distance_km)²`
        
    - `a = 99.99 / (200)²`
        
    - `a = 99.99 / 40000`
        
    - `a = **0.00249975**`
        
- **Distance Difficulty Formula:**
    
    - `Distance_Difficulty = a * distance_km²`
        
    - `Distance_Difficulty = 0.00249975 * distance_km²`
        

**3. Output:**

- `Distance_Difficulty`: A raw score representing the difficulty contribution from distance alone, scaled from 0 up to approximately 99.99 (for 200km). This value is then used in the `Total_Difficulty` calculation:
    
    - `Total_Difficulty = Distance_Difficulty * EF`