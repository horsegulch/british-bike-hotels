import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2, pow
import copy 
import traceback # For printing detailed errors
import os # To get the filename from the path

# --- Configuration: Metric Extraction ---
SMOOTHING_WINDOW_SIZE = 7 
MCG_SEGMENT_TARGET_DISTANCE_M = 100.0 
MIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0 
SIG_CLIMB_FACTOR_THRESHOLD = 3500.0 
SIG_CLIMB_MIN_DISTANCE_M = 250.0     
SIG_CLIMB_MIN_GRADIENT_PERCENT = 3.0 
POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD = 1.0 
SIG_DESCENT_MIN_DISTANCE_M = 500.0     
SIG_DESCENT_MIN_GRADIENT_PERCENT = -3.0 
POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD = -1.0 

# --- Configuration: Difficulty Calculation ---
DISTANCE_BASE_ADDITION = 10.0
DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.003 
MAX_EXPECTED_TEGA = 3500.0
MAX_EXPECTED_ACG = 12.0
MAX_EXPECTED_MCG = 20.0 
WEIGHT_TEGA = 0.50
WEIGHT_ACG = 0.40
WEIGHT_MCG = 0.10
LINEAR_UF_SLOPE = 0.8  
PDD_THRESHOLD = 0.65
MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0 
TARGET_ADG_FOR_MAX_REDUCTION = 7.0
WEIGHT_PDD_SCORE = 0.7
WEIGHT_ADG_SCORE = 0.3
MAX_DOWNHILL_REDUCTION_FACTOR = 0.8 
MIN_DIFFICULTY_SCORE = 0.0

# --- Helper Functions ---

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in kilometers."""
    R = 6371
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_smoothed_elevations(original_elevations, window_size):
    """Applies a simple moving average to a list of elevation values."""
    if not original_elevations or window_size < 2 or len(original_elevations) < window_size:
        return list(original_elevations) 
    smoothed_elevations = list(original_elevations) 
    half_window = window_size // 2
    for i in range(half_window, len(original_elevations) - half_window):
        window_values = original_elevations[i - half_window : i + half_window + 1]
        valid_window_values = [v for v in window_values if isinstance(v, (int, float))]
        if len(valid_window_values) == window_size : 
            smoothed_elevations[i] = sum(valid_window_values) / len(valid_window_values)
    return smoothed_elevations

# --- Difficulty Calculation Functions ---

def calculate_distance_difficulty(distance_km: float) -> float:
    """Calculates the base difficulty score based purely on the distance."""
    if distance_km < 0: return 0.0 
    difficulty = DISTANCE_BASE_ADDITION + (DISTANCE_DIFFICULTY_COEFFICIENT_A * (distance_km**2))
    return difficulty

def calculate_uphill_factor(tega: float, acg: float, mcg: float) -> float:
    """Calculates the Uphill Factor (UF) using a LINEAR model."""
    tega_norm = min(max(0, tega) / (MAX_EXPECTED_TEGA if MAX_EXPECTED_TEGA > 0 else 1.0), 1.0)
    acg_norm = min(max(0, acg) / (MAX_EXPECTED_ACG if MAX_EXPECTED_ACG > 0 else 1.0), 1.0)
    mcg_norm = min(max(0, mcg) / (MAX_EXPECTED_MCG if MAX_EXPECTED_MCG > 0 else 1.0), 1.0)
    uphill_score = (WEIGHT_TEGA * tega_norm) + (WEIGHT_ACG * acg_norm) + (WEIGHT_MCG * mcg_norm)
    uphill_score = min(max(uphill_score, 0.0), 1.0)
    uphill_factor = 1 + (LINEAR_UF_SLOPE * uphill_score)
    return uphill_factor

def calculate_downhill_reduction_factor(pdd: float, tega_for_downhill_check: float, adg: float) -> float:
    """Calculates the Downhill Reduction Factor (DRF)."""
    condition_a_met = pdd > PDD_THRESHOLD
    condition_b_met = tega_for_downhill_check < MAX_ASCENT_FOR_DOWNHILL_REDUCTION
    condition_c_met = abs(adg) > MIN_AVG_DESCENT_GRADIENT_THRESHOLD
    if not (condition_a_met and condition_b_met and condition_c_met): return 1.0
    pdd_norm_denominator = 1.0 - PDD_THRESHOLD
    pdd_score_norm = 0.0
    if pdd_norm_denominator > 0: pdd_score_norm = (pdd - PDD_THRESHOLD) / pdd_norm_denominator
    elif pdd >= PDD_THRESHOLD: pdd_score_norm = 1.0
    pdd_score_norm = min(max(pdd_score_norm, 0.0), 1.0)
    adg_norm_denominator = TARGET_ADG_FOR_MAX_REDUCTION - MIN_AVG_DESCENT_GRADIENT_THRESHOLD
    adg_score_norm = 0.0
    if adg_norm_denominator > 0: adg_score_norm = (abs(adg) - MIN_AVG_DESCENT_GRADIENT_THRESHOLD) / adg_norm_denominator
    elif abs(adg) >= TARGET_ADG_FOR_MAX_REDUCTION: adg_score_norm = 1.0
    adg_score_norm = min(max(adg_score_norm, 0.0), 1.0)
    downhill_score = (WEIGHT_PDD_SCORE * pdd_score_norm) + (WEIGHT_ADG_SCORE * adg_score_norm)
    downhill_score = min(max(downhill_score, 0.0), 1.0)
    downhill_reduction_factor = pow(MAX_DOWNHILL_REDUCTION_FACTOR, downhill_score)
    return downhill_reduction_factor

def calculate_elevation_factor(tega: float, acg: float, mcg: float, pdd: float, adg: float) -> float:
    """Calculates the overall Elevation Factor (EF)."""
    uf = calculate_uphill_factor(tega, acg, mcg)
    drf = calculate_downhill_reduction_factor(pdd, tega, adg)
    ef = uf * drf
    return ef

def calculate_total_difficulty(distance_km: float, tega: float, acg: float, mcg: float, pdd: float, adg: float) -> float:
    """Calculates the final UN CAPPED total difficulty score for a ride."""
    if distance_km <= 0: return MIN_DIFFICULTY_SCORE
    dist_difficulty = calculate_distance_difficulty(distance_km)
    elevation_factor = calculate_elevation_factor(tega, acg, mcg, pdd, adg)
    raw_total_difficulty = dist_difficulty * elevation_factor
    final_difficulty = max(MIN_DIFFICULTY_SCORE, raw_total_difficulty)
    return final_difficulty

# --- Metric Extraction Function ---

def extract_metrics_from_gpx(gpx_file_path: str, apply_smoothing: bool = True):
    """
    Parses a GPX file and extracts all six metrics required for difficulty calculation.
    Returns a dictionary of metrics or None on error.
    """
    # Initialize metrics with default values
    metrics_result = {
        "distance_km": 0.0, "TEGa": 0.0, "TEGa_raw": 0.0, "TEGa_smoothed": 0.0, 
        "PDD": 0.0, "MCg": 0.0, "ACg": 0.0, "ADg": 0.0, "raw_points_count": 0
    }
    distance_km = 0.0
    total_elevation_gain_raw = 0.0
    total_elevation_gain_smoothed = 0.0
    total_downhill_distance_km = 0.0 
    pdd = 0.0 
    mcg = 0.0 
    acg = 0.0 
    adg = 0.0 
    all_points_original = []

    try:
        with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file_content:
            gpx = gpxpy.parse(gpx_file_content)

            for track in gpx.tracks:
                for segment in track.segments:
                    all_points_original.extend(segment.points)
            for route in gpx.routes:
                all_points_original.extend(route.points)
            
            metrics_result["raw_points_count"] = len(all_points_original) # Store raw count

            if not all_points_original:
                print(f"No points found in GPX file: {gpx_file_path}")
                return metrics_result # Return default metrics
            print(f"Original points found: {len(all_points_original)}")
            if len(all_points_original) < 2:
                print("Not enough points to calculate metrics.")
                return metrics_result # Return default metrics

            # --- Smoothing ---
            points_for_distance_calculation = all_points_original
            points_for_elevation_metrics = all_points_original 
            if apply_smoothing and len(all_points_original) >= SMOOTHING_WINDOW_SIZE:
                original_elevations = [p.elevation for p in all_points_original if p.elevation is not None]
                if len(original_elevations) >= SMOOTHING_WINDOW_SIZE:
                    smoothed_elevation_values = get_smoothed_elevations(original_elevations, SMOOTHING_WINDOW_SIZE)
                    temp_smoothed_points_list = []
                    ele_idx = 0
                    for p_orig in all_points_original:
                        new_p = gpxpy.gpx.GPXTrackPoint(latitude=p_orig.latitude, longitude=p_orig.longitude, time=p_orig.time)
                        if p_orig.elevation is not None and ele_idx < len(smoothed_elevation_values):
                            new_p.elevation = smoothed_elevation_values[ele_idx]; ele_idx +=1
                        else: new_p.elevation = p_orig.elevation
                        temp_smoothed_points_list.append(new_p)
                    points_for_elevation_metrics = temp_smoothed_points_list
                    print(f"Elevation smoothing applied with window size: {SMOOTHING_WINDOW_SIZE}")
                else: print("Not enough elevation points to apply smoothing, using raw elevation.")
            elif apply_smoothing: print("Not enough points overall to apply smoothing, using raw elevation.")

            # --- Calculations ---
            # Distance
            for i in range(len(points_for_distance_calculation) - 1):
                p1, p2 = points_for_distance_calculation[i], points_for_distance_calculation[i+1]
                if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                    distance_km += haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
            metrics_result["distance_km"] = distance_km

            # TEGa Raw
            for i in range(len(all_points_original) - 1):
                p1, p2 = all_points_original[i], all_points_original[i+1]
                if p1.elevation is not None and p2.elevation is not None:
                    if p2.elevation > p1.elevation: total_elevation_gain_raw += (p2.elevation - p1.elevation)
            metrics_result["TEGa_raw"] = total_elevation_gain_raw

            # TEGa Smoothed, PDD, Cumulative Distances
            cumulative_distances_km_at_points = [0.0] * len(points_for_elevation_metrics)
            current_cumulative_dist_km = 0.0
            if len(points_for_elevation_metrics) >= 1:
                for i in range(len(points_for_elevation_metrics) - 1):
                    p1, p2 = points_for_elevation_metrics[i], points_for_elevation_metrics[i+1]
                    segment_dist_km = 0.0
                    if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                        segment_dist_km = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
                    current_cumulative_dist_km += segment_dist_km
                    if i + 1 < len(cumulative_distances_km_at_points): cumulative_distances_km_at_points[i+1] = current_cumulative_dist_km
                    if p1.elevation is not None and p2.elevation is not None:
                        elevation_diff = p2.elevation - p1.elevation
                        if elevation_diff > 0: total_elevation_gain_smoothed += elevation_diff
                        elif elevation_diff < 0: total_downhill_distance_km += segment_dist_km
            pdd = (total_downhill_distance_km / distance_km) if distance_km > 0 else 0.0
            metrics_result["TEGa_smoothed"] = total_elevation_gain_smoothed
            metrics_result["TEGa"] = total_elevation_gain_smoothed # Use smoothed for algorithm
            metrics_result["PDD"] = pdd
            
            # MCg
            if len(points_for_elevation_metrics) >= 2:
                for i in range(len(points_for_elevation_metrics) -1):
                    start_point_mcg_segment = points_for_elevation_metrics[i]
                    current_segment_dist_m = 0.0
                    end_point_idx = i 
                    for j in range(i + 1, len(points_for_elevation_metrics)):
                        p1_seg, p2_seg = points_for_elevation_metrics[j-1], points_for_elevation_metrics[j]
                        dist_between_m = 0.0
                        if p1_seg.latitude is not None and p1_seg.longitude is not None and p2_seg.latitude is not None and p2_seg.longitude is not None:
                            dist_between_m = haversine_distance(p1_seg.latitude, p1_seg.longitude, p2_seg.latitude, p2_seg.longitude) * 1000
                        if current_segment_dist_m + dist_between_m <= MCG_SEGMENT_TARGET_DISTANCE_M:
                            current_segment_dist_m += dist_between_m; end_point_idx = j
                        else:
                            if dist_between_m > 0 and current_segment_dist_m == 0 : current_segment_dist_m = dist_between_m; end_point_idx = j
                            break 
                    if end_point_idx > i and current_segment_dist_m >= MIN_DIST_FOR_MCG_GRADIENT_CALC_M:
                        actual_end_point_mcg_segment = points_for_elevation_metrics[end_point_idx]
                        if start_point_mcg_segment.elevation is not None and actual_end_point_mcg_segment.elevation is not None:
                            elevation_change_m = actual_end_point_mcg_segment.elevation - start_point_mcg_segment.elevation
                            if elevation_change_m > 0: 
                                gradient_percent = (elevation_change_m / current_segment_dist_m) * 100.0
                                if gradient_percent > mcg: mcg = gradient_percent
            metrics_result["MCg"] = mcg

            # ACg
            significant_climb_gradients = []
            current_climb_points = [] 
            if len(points_for_elevation_metrics) >= 2:
                for i in range(len(points_for_elevation_metrics) - 1):
                    p1, p2 = points_for_elevation_metrics[i], points_for_elevation_metrics[i+1]
                    segment_dist_m = 0.0
                    if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                        segment_dist_m = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude) * 1000
                    elevation_change_m = 0.0
                    if p1.elevation is not None and p2.elevation is not None:
                        elevation_change_m = p2.elevation - p1.elevation
                    current_segment_gradient = (elevation_change_m / segment_dist_m * 100.0) if segment_dist_m > 0 else 0
                    if elevation_change_m > 0 and current_segment_gradient >= POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD : 
                        if not current_climb_points: current_climb_points.append(p1)
                        current_climb_points.append(p2)
                    else: 
                        if len(current_climb_points) >= 2: 
                            climb_start_point, climb_end_point = current_climb_points[0], current_climb_points[-1]
                            climb_segment_total_dist_m, climb_segment_total_gain_m = 0, 0
                            for k in range(len(current_climb_points) - 1):
                                cp1, cp2 = current_climb_points[k], current_climb_points[k+1]
                                seg_d = 0
                                if cp1.latitude is not None and cp1.longitude is not None and cp2.latitude is not None and cp2.longitude is not None:
                                     seg_d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000
                                climb_segment_total_dist_m += seg_d
                                if cp1.elevation is not None and cp2.elevation is not None:
                                    climb_segment_total_gain_m += max(0, cp2.elevation - cp1.elevation)
                            if climb_segment_total_dist_m > 0: 
                                avg_grad_of_segment = (climb_segment_total_gain_m / climb_segment_total_dist_m) * 100.0
                                climb_factor = climb_segment_total_dist_m * avg_grad_of_segment
                                if climb_segment_total_dist_m >= SIG_CLIMB_MIN_DISTANCE_M and \
                                   avg_grad_of_segment >= SIG_CLIMB_MIN_GRADIENT_PERCENT and \
                                   climb_factor >= SIG_CLIMB_FACTOR_THRESHOLD:
                                    significant_climb_gradients.append(avg_grad_of_segment)
                        current_climb_points = [] 
                if len(current_climb_points) >= 2: # Check last segment
                    climb_start_point, climb_end_point = current_climb_points[0], current_climb_points[-1]
                    climb_segment_total_dist_m, climb_segment_total_gain_m = 0, 0
                    for k in range(len(current_climb_points) - 1):
                        cp1, cp2 = current_climb_points[k], current_climb_points[k+1]
                        seg_d = 0
                        if cp1.latitude is not None and cp1.longitude is not None and cp2.latitude is not None and cp2.longitude is not None:
                             seg_d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000
                        climb_segment_total_dist_m += seg_d
                        if cp1.elevation is not None and cp2.elevation is not None:
                            climb_segment_total_gain_m += max(0, cp2.elevation - cp1.elevation)
                    if climb_segment_total_dist_m > 0:
                        avg_grad_of_segment = (climb_segment_total_gain_m / climb_segment_total_dist_m) * 100.0
                        climb_factor = climb_segment_total_dist_m * avg_grad_of_segment
                        if climb_segment_total_dist_m >= SIG_CLIMB_MIN_DISTANCE_M and \
                           avg_grad_of_segment >= SIG_CLIMB_MIN_GRADIENT_PERCENT and \
                           climb_factor >= SIG_CLIMB_FACTOR_THRESHOLD:
                            significant_climb_gradients.append(avg_grad_of_segment)
            acg = sum(significant_climb_gradients) / len(significant_climb_gradients) if significant_climb_gradients else 0.0
            metrics_result["ACg"] = acg

            # ADg
            significant_descent_gradients = []
            current_descent_points = []
            if len(points_for_elevation_metrics) >= 2:
                for i in range(len(points_for_elevation_metrics) - 1):
                    p1, p2 = points_for_elevation_metrics[i], points_for_elevation_metrics[i+1]
                    segment_dist_m = 0.0
                    if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                        segment_dist_m = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude) * 1000
                    elevation_change_m = 0.0
                    if p1.elevation is not None and p2.elevation is not None:
                        elevation_change_m = p2.elevation - p1.elevation
                    current_segment_gradient = (elevation_change_m / segment_dist_m * 100.0) if segment_dist_m > 0 else 0
                    if elevation_change_m < 0 and current_segment_gradient <= POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD: 
                        if not current_descent_points: current_descent_points.append(p1)
                        current_descent_points.append(p2)
                    else: 
                        if len(current_descent_points) >= 2:
                            descent_start_point, descent_end_point = current_descent_points[0], current_descent_points[-1]
                            descent_segment_total_dist_m, descent_segment_total_loss_m = 0, 0
                            for k in range(len(current_descent_points) - 1):
                                dp1, dp2 = current_descent_points[k], current_descent_points[k+1]
                                seg_d = 0
                                if dp1.latitude is not None and dp1.longitude is not None and dp2.latitude is not None and dp2.longitude is not None:
                                    seg_d = haversine_distance(dp1.latitude, dp1.longitude, dp2.latitude, dp2.longitude) * 1000
                                descent_segment_total_dist_m += seg_d
                                if dp1.elevation is not None and dp2.elevation is not None:
                                    descent_segment_total_loss_m += abs(min(0, dp2.elevation - dp1.elevation)) 
                            if descent_segment_total_dist_m > 0:
                                avg_grad_of_segment = (-descent_segment_total_loss_m / descent_segment_total_dist_m) * 100.0
                                if descent_segment_total_dist_m >= SIG_DESCENT_MIN_DISTANCE_M and \
                                   avg_grad_of_segment <= SIG_DESCENT_MIN_GRADIENT_PERCENT:
                                    significant_descent_gradients.append(abs(avg_grad_of_segment))
                        current_descent_points = []
                if len(current_descent_points) >= 2: # Check last segment for descent
                    descent_start_point, descent_end_point = current_descent_points[0], current_descent_points[-1]
                    descent_segment_total_dist_m, descent_segment_total_loss_m = 0, 0
                    for k in range(len(current_descent_points) - 1):
                        dp1, dp2 = current_descent_points[k], current_descent_points[k+1]
                        seg_d = 0
                        if dp1.latitude is not None and dp1.longitude is not None and dp2.latitude is not None and dp2.longitude is not None:
                            seg_d = haversine_distance(dp1.latitude, dp1.longitude, dp2.latitude, dp2.longitude) * 1000
                        descent_segment_total_dist_m += seg_d
                        if dp1.elevation is not None and dp2.elevation is not None:
                            descent_segment_total_loss_m += abs(min(0, dp2.elevation - dp1.elevation))
                    if descent_segment_total_dist_m > 0:
                        avg_grad_of_segment = (-descent_segment_total_loss_m / descent_segment_total_dist_m) * 100.0
                        if descent_segment_total_dist_m >= SIG_DESCENT_MIN_DISTANCE_M and \
                           avg_grad_of_segment <= SIG_DESCENT_MIN_GRADIENT_PERCENT:
                            significant_descent_gradients.append(abs(avg_grad_of_segment))
            adg = sum(significant_descent_gradients) / len(significant_descent_gradients) if significant_descent_gradients else 0.0
            metrics_result["ADg"] = adg

            # --- Print Summary ---
            print("\n--- Extracted Metrics Summary ---")
            for key, value in metrics_result.items():
                 if isinstance(value, (float, int)): print(f"  {key}: {value:.3f}")
                 else: print(f"  {key}: {value}")
            print("---------------------------------\n")

            return metrics_result

    except Exception as e: 
        print(f"An unexpected error occurred during metric extraction: {e}")
        traceback.print_exc() 
    return None

# --- Main Execution Block ---
if __name__ == "__main__":
    # --- Define LIST of GPX file paths ---
    # IMPORTANT: Add the full paths to all GPX files you want to process here
    gpx_file_paths = [
        r"C:\Users\unwan\Downloads\Dales_Climbers_Classic.gpx",
        r"C:\Users\unwan\Downloads\Easy Coastal.gpx",
        r"C:\Users\unwan\Downloads\Medium Hills.gpx",
        r"C:\Users\unwan\Downloads\Hard Surrey.gpx",
        r"C:\Users\unwan\Downloads\Easy Long.gpx",
        r"C:\Users\unwan\Downloads\The Rider.gpx",
        # Add more file paths here, e.g.:
        # r"C:\path\to\another\route.gpx",
        # r"C:\path\to\yet\another\route.gpx",
    ]
    
    print("Starting Batch GPX Processing...")
    print("================================\n")

    # --- Loop through each file path ---
    for gpx_file in gpx_file_paths:
        print(f"--- Processing File: {os.path.basename(gpx_file)} ---") # Use os.path.basename to show just filename
        
        if not os.path.exists(gpx_file):
            print(f"  ERROR: File not found at {gpx_file}")
            print("---------------------------------\n")
            continue # Skip to the next file

        # --- Step 1: Extract Metrics ---
        metrics = extract_metrics_from_gpx(gpx_file, apply_smoothing=True) 

        # --- Step 2: Calculate Difficulty Score ---
        if metrics:
            # Check if all required metrics were calculated successfully
            required_keys = ["distance_km", "TEGa", "ACg", "MCg", "PDD", "ADg"]
            # Check if keys exist and values are not None (0 is acceptable)
            if all(key in metrics and metrics[key] is not None for key in required_keys): 
                print("  All required metrics extracted. Calculating total difficulty...")
                
                # Call the difficulty calculation function with extracted metrics
                total_difficulty = calculate_total_difficulty(
                    distance_km = metrics['distance_km'],
                    tega = metrics['TEGa'], # Using the smoothed TEGa
                    acg = metrics['ACg'],
                    mcg = metrics['MCg'],
                    pdd = metrics['PDD'],
                    adg = metrics['ADg']
                )
                
                print(f"\n  >>> FINAL CALCULATED DIFFICULTY SCORE: {total_difficulty:.2f} <<<")
                
            else:
                print("\n  ERROR: Could not calculate total difficulty because some required metrics are missing or None.")
                print("  Missing keys or None values for:", 
                      [key for key in required_keys if key not in metrics or metrics[key] is None])

        else:
            print("\n  ERROR: Failed to extract metrics from GPX file. Cannot calculate difficulty.")
            
        print("---------------------------------\n") # Separator between files

    print("================================")
    print("Batch Processing Complete.")

