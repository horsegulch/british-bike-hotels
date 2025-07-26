# difficulty_calculator.py - Calculates route difficulty based on extracted metrics

from math import pow 

# Import all configuration constants from config.py
# This makes them available as, e.g., config.DISTANCE_BASE_ADDITION
import config 

# --- Difficulty Calculation Functions ---

def calculate_distance_difficulty(distance_km: float) -> float:
    """
    Calculates the base difficulty score based purely on the distance.
    Uses DISTANCE_BASE_ADDITION and DISTANCE_DIFFICULTY_COEFFICIENT_A from config.
    """
    if distance_km < 0: 
        return 0.0 
    # The main calculate_total_difficulty function will handle 0km distance to return MIN_DIFFICULTY_SCORE
    difficulty = config.DISTANCE_BASE_ADDITION + \
                 (config.DISTANCE_DIFFICULTY_COEFFICIENT_A * (distance_km**2))
    return difficulty

def calculate_uphill_factor(tega: float, acg: float, mcg_val: float) -> float: 
    """
    Calculates the Uphill Factor (UF) using a LINEAR model.
    Uses normalization ceilings (MAX_EXPECTED_TEGA, etc.), 
    weights (WEIGHT_TEGA, etc.), and LINEAR_UF_SLOPE from config.
    mcg_val is the calculated MCg from the GPX/TCX file.
    """
    # Normalize metrics against their expected maximums
    tega_norm = min(max(0, tega) / (config.MAX_EXPECTED_TEGA if config.MAX_EXPECTED_TEGA > 0 else 1.0), 1.0)
    acg_norm = min(max(0, acg) / (config.MAX_EXPECTED_ACG if config.MAX_EXPECTED_ACG > 0 else 1.0), 1.0)
    mcg_norm = min(max(0, mcg_val) / (config.MAX_EXPECTED_MCG if config.MAX_EXPECTED_MCG > 0 else 1.0), 1.0) 
    
    # Calculate weighted Uphill Score (US)
    uphill_score = (config.WEIGHT_TEGA * tega_norm) + \
                   (config.WEIGHT_ACG * acg_norm) + \
                   (config.WEIGHT_MCG * mcg_norm)
    uphill_score = min(max(uphill_score, 0.0), 1.0) # Clamp US between 0 and 1
    
    # Calculate Uphill Factor (UF)
    uphill_factor = 1 + (config.LINEAR_UF_SLOPE * uphill_score)
    return uphill_factor

def calculate_downhill_reduction_factor(pdd: float, tega_for_downhill_check: float, adg: float) -> float:
    """
    Calculates the Downhill Reduction Factor (DRF).
    Uses PDD_THRESHOLD, MAX_ASCENT_FOR_DOWNHILL_REDUCTION, etc., from config.
    """
    # Check qualifying conditions
    condition_a_met = pdd > config.PDD_THRESHOLD
    condition_b_met = tega_for_downhill_check < config.MAX_ASCENT_FOR_DOWNHILL_REDUCTION
    condition_c_met = abs(adg) > config.MIN_AVG_DESCENT_GRADIENT_THRESHOLD # adg is positive
    
    if not (condition_a_met and condition_b_met and condition_c_met): 
        return 1.0 # No reduction if conditions not met

    # PDD Score Normalization
    pdd_norm_denominator = 1.0 - config.PDD_THRESHOLD
    pdd_score_norm = 0.0
    if pdd_norm_denominator > 0: 
        pdd_score_norm = (pdd - config.PDD_THRESHOLD) / pdd_norm_denominator
    elif pdd >= config.PDD_THRESHOLD: 
        pdd_score_norm = 1.0
    pdd_score_norm = min(max(pdd_score_norm, 0.0), 1.0) 
    
    # ADg Score Normalization
    adg_norm_denominator = config.TARGET_ADG_FOR_MAX_REDUCTION - config.MIN_AVG_DESCENT_GRADIENT_THRESHOLD
    adg_score_norm = 0.0
    if adg_norm_denominator > 0: 
        adg_score_norm = (abs(adg) - config.MIN_AVG_DESCENT_GRADIENT_THRESHOLD) / adg_norm_denominator
    elif abs(adg) >= config.TARGET_ADG_FOR_MAX_REDUCTION: 
         adg_score_norm = 1.0
    adg_score_norm = min(max(adg_score_norm, 0.0), 1.0) 
    
    # Combine for Downhill Score (DS)
    downhill_score = (config.WEIGHT_PDD_SCORE * pdd_score_norm) + \
                     (config.WEIGHT_ADG_SCORE * adg_score_norm)
    downhill_score = min(max(downhill_score, 0.0), 1.0) 
    
    # Calculate Downhill Reduction Factor (DRF)
    downhill_reduction_factor = pow(config.MAX_DOWNHILL_REDUCTION_FACTOR, downhill_score)
    return downhill_reduction_factor

def calculate_elevation_factor(tega: float, acg: float, mcg_val: float, pdd: float, adg: float) -> float: 
    """
    Calculates the overall Elevation Factor (EF) by combining UF and DRF.
    mcg_val is the calculated MCg from the GPX/TCX file.
    """
    uf = calculate_uphill_factor(tega, acg, mcg_val) 
    drf = calculate_downhill_reduction_factor(pdd, tega, adg)
    ef = uf * drf
    return ef

def calculate_total_difficulty(
        distance_km: float, 
        tega: float, 
        acg: float, 
        mcg_val: float, 
        pdd: float, 
        adg: float
    ) -> float: 
    """
    Calculates the final UN CAPPED total difficulty score for a ride.
    Uses MIN_DIFFICULTY_SCORE from config.
    """
    if distance_km <= 0: 
        return config.MIN_DIFFICULTY_SCORE
    
    dist_difficulty = calculate_distance_difficulty(distance_km)
    elevation_factor = calculate_elevation_factor(tega, acg, mcg_val, pdd, adg) 
    
    raw_total_difficulty = dist_difficulty * elevation_factor
    final_difficulty = max(config.MIN_DIFFICULTY_SCORE, raw_total_difficulty)
    
    return final_difficulty

if __name__ == '__main__':
    # Example Usage (optional - for testing difficulty_calculator.py directly)
    # This requires 'config.py' to be in the same directory or accessible in PYTHONPATH
    
    print("--- Testing difficulty_calculator.py with example metrics ---")
    
    # Create a dummy config.py for standalone testing if it doesn't exist
    # This is only for when running this file directly.
    import os
    if not os.path.exists("config.py"):
        print("Creating dummy config.py for testing difficulty_calculator.py")
        with open("config.py", "w") as f_config:
            f_config.write("DISTANCE_BASE_ADDITION = 5.0\n")
            f_config.write("DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.003\n")
            f_config.write("MAX_EXPECTED_TEGA = 3500.0\n")
            f_config.write("MAX_EXPECTED_ACG = 12.0\n")
            f_config.write("MAX_EXPECTED_MCG = 45.0\n")
            f_config.write("WEIGHT_TEGA = 0.50\n")
            f_config.write("WEIGHT_ACG = 0.40\n")
            f_config.write("WEIGHT_MCG = 0.10\n")
            f_config.write("LINEAR_UF_SLOPE = 1.2\n")
            f_config.write("PDD_THRESHOLD = 0.65\n")
            f_config.write("MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0\n")
            f_config.write("MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0\n")
            f_config.write("TARGET_ADG_FOR_MAX_REDUCTION = 7.0\n")
            f_config.write("WEIGHT_PDD_SCORE = 0.7\n")
            f_config.write("WEIGHT_ADG_SCORE = 0.3\n")
            f_config.write("MAX_DOWNHILL_REDUCTION_FACTOR = 0.8\n")
            f_config.write("MIN_DIFFICULTY_SCORE = 0.0\n")
        import config # Re-import if just created
    else:
        # If config.py exists, ensure it's reloaded in case of changes for testing
        import importlib
        importlib.reload(config)


    print(f"Using DISTANCE_BASE_ADDITION: {config.DISTANCE_BASE_ADDITION}")
    print(f"Using DISTANCE_DIFFICULTY_COEFFICIENT_A: {config.DISTANCE_DIFFICULTY_COEFFICIENT_A}")
    print(f"Using LINEAR_UF_SLOPE: {config.LINEAR_UF_SLOPE}")
    print(f"Using MAX_EXPECTED_MCG (for normalization): {config.MAX_EXPECTED_MCG}")

    example_metrics = {
        "distance_km": 100.0, "TEGa": 2000.0, "ACg": 7.0, 
        "MCg": 15.0, "PDD": 0.45, "ADg": 4.0      
    }
    score = calculate_total_difficulty(
        distance_km=example_metrics["distance_km"],
        tega=example_metrics["TEGa"],
        acg=example_metrics["ACg"],
        mcg_val=example_metrics["MCg"],
        pdd=example_metrics["PDD"],
        adg=example_metrics["ADg"]
    )
    print(f"\nExample Metrics: {example_metrics}")
    print(f"Calculated Total Difficulty: {score:.2f}")

    flat_ride_metrics = {
        "distance_km": 50.0, "TEGa": 0, "ACg": 0, "MCg": 0, "PDD": 0, "ADg": 0
    }
    flat_score = calculate_total_difficulty(**flat_ride_metrics) # Using dictionary unpacking
    print(f"\nFlat 50km Ride Metrics: {flat_ride_metrics}")
    print(f"Flat 50km Ride Difficulty: {flat_score:.2f}")
