import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2
import copy # For deep copying points if necessary

# --- Configuration ---
SMOOTHING_WINDOW_SIZE = 7 
MCG_SEGMENT_TARGET_DISTANCE_M = 100.0 # User defined
MIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0 # User defined

# Constants for ACg (Significant Climb Identification)
SIG_CLIMB_FACTOR_THRESHOLD = 3500.0  # distance_m * avg_gradient_percent
SIG_CLIMB_MIN_DISTANCE_M = 250.0     # meters
SIG_CLIMB_MIN_GRADIENT_PERCENT = 3.0 # %
# Threshold to start considering a segment as part of a potential climb (can be lower than SIG_CLIMB_MIN_GRADIENT_PERCENT)
POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD = 1.0 # % 

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

def extract_metrics_from_gpx(gpx_file_path: str, apply_smoothing: bool = True):
    """
    Parses a GPX file and extracts metrics.
    Includes elevation smoothing, PDD, MCg, and ACg calculation.
    """
    distance_km = 0.0
    total_elevation_gain_raw = 0.0
    total_elevation_gain_smoothed = 0.0
    total_downhill_distance_km = 0.0 
    pdd = 0.0 
    mcg = 0.0 
    acg = 0.0 # Average Climb Gradient, initialized to 0
    
    all_points_original = []

    try:
        with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file_content:
            gpx = gpxpy.parse(gpx_file_content)

            for track in gpx.tracks:
                for segment in track.segments:
                    all_points_original.extend(segment.points)
            for route in gpx.routes:
                all_points_original.extend(route.points)

            if not all_points_original:
                print(f"No points found in GPX file: {gpx_file_path}")
                return None
            print(f"Original points found: {len(all_points_original)}")
            if len(all_points_original) < 2:
                # Handle case with insufficient points
                return {"distance_km": 0.0, "TEGa": 0.0, "TEGa_raw": 0.0, "TEGa_smoothed": 0.0, 
                        "PDD": 0.0, "MCg": 0.0, "ACg": 0.0, "ADg": None}


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
                            new_p.elevation = smoothed_elevation_values[ele_idx]
                            ele_idx +=1
                        else: new_p.elevation = p_orig.elevation
                        temp_smoothed_points_list.append(new_p)
                    points_for_elevation_metrics = temp_smoothed_points_list
                    print(f"Elevation smoothing applied with window size: {SMOOTHING_WINDOW_SIZE}")
                else: print("Not enough elevation points to apply smoothing, using raw elevation.")
            elif apply_smoothing: print("Not enough points overall to apply smoothing, using raw elevation.")

            for i in range(len(points_for_distance_calculation) - 1):
                p1, p2 = points_for_distance_calculation[i], points_for_distance_calculation[i+1]
                if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                    distance_km += haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)

            for i in range(len(all_points_original) - 1):
                p1, p2 = all_points_original[i], all_points_original[i+1]
                if p1.elevation is not None and p2.elevation is not None:
                    if p2.elevation > p1.elevation: total_elevation_gain_raw += (p2.elevation - p1.elevation)
            
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
            final_tega = total_elevation_gain_smoothed

            if len(points_for_elevation_metrics) >= 2:
                # MCg Calculation (unchanged from previous version, but ensure constants are used)
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
                            current_segment_dist_m += dist_between_m
                            end_point_idx = j
                        else:
                            if dist_between_m > 0 and current_segment_dist_m == 0 : 
                                current_segment_dist_m = dist_between_m
                                end_point_idx = j
                            break 
                    if end_point_idx > i and current_segment_dist_m >= MIN_DIST_FOR_MCG_GRADIENT_CALC_M:
                        actual_end_point_mcg_segment = points_for_elevation_metrics[end_point_idx]
                        if start_point_mcg_segment.elevation is not None and actual_end_point_mcg_segment.elevation is not None:
                            elevation_change_m = actual_end_point_mcg_segment.elevation - start_point_mcg_segment.elevation
                            if elevation_change_m > 0: 
                                gradient_percent = (elevation_change_m / current_segment_dist_m) * 100.0
                                if gradient_percent > mcg: mcg = gradient_percent
            
            # --- Calculate ACg (Average Climb Gradient of Significant Climbs) ---
            significant_climb_gradients = []
            current_climb_points = [] # List to store points of a potential climb segment
            
            if len(points_for_elevation_metrics) >= 2:
                print("\n--- Debugging ACg: Identifying Potential Climb Segments ---")
                for i in range(len(points_for_elevation_metrics) - 1):
                    p1 = points_for_elevation_metrics[i]
                    p2 = points_for_elevation_metrics[i+1]
                    
                    segment_dist_m = 0.0
                    if p1.latitude is not None and p1.longitude is not None and p2.latitude is not None and p2.longitude is not None:
                        segment_dist_m = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude) * 1000
                    
                    elevation_change_m = 0.0
                    if p1.elevation is not None and p2.elevation is not None:
                        elevation_change_m = p2.elevation - p1.elevation

                    current_segment_gradient = (elevation_change_m / segment_dist_m * 100.0) if segment_dist_m > 0 else 0

                    if elevation_change_m > 0 and current_segment_gradient >= POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD : # Start or continue a climb segment
                        if not current_climb_points: # Start of a new potential climb
                            current_climb_points.append(p1)
                        current_climb_points.append(p2)
                    else: # Segment is not uphill enough, or is downhill/flat; current potential climb ends
                        if len(current_climb_points) >= 2: # We have an accumulated climb segment to evaluate
                            climb_start_point = current_climb_points[0]
                            climb_end_point = current_climb_points[-1]
                            
                            climb_segment_total_dist_m = 0
                            climb_segment_total_gain_m = 0
                            
                            # Recalculate distance and gain for the accumulated segment
                            for k in range(len(current_climb_points) - 1):
                                cp1 = current_climb_points[k]
                                cp2 = current_climb_points[k+1]
                                seg_d = 0
                                if cp1.latitude is not None and cp1.longitude is not None and cp2.latitude is not None and cp2.longitude is not None:
                                     seg_d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000
                                climb_segment_total_dist_m += seg_d
                                if cp1.elevation is not None and cp2.elevation is not None:
                                    climb_segment_total_gain_m += max(0, cp2.elevation - cp1.elevation) # Sum only positive gains within the segment

                            if climb_segment_total_dist_m > 0: # Avoid division by zero
                                avg_grad_of_segment = (climb_segment_total_gain_m / climb_segment_total_dist_m) * 100.0
                                climb_factor = climb_segment_total_dist_m * avg_grad_of_segment
                                
                                print(f"  Potential climb ended. Dist: {climb_segment_total_dist_m:.0f}m, Gain: {climb_segment_total_gain_m:.0f}m, AvgGrad: {avg_grad_of_segment:.2f}%, Factor: {climb_factor:.0f}")

                                if climb_segment_total_dist_m >= SIG_CLIMB_MIN_DISTANCE_M and \
                                   avg_grad_of_segment >= SIG_CLIMB_MIN_GRADIENT_PERCENT and \
                                   climb_factor >= SIG_CLIMB_FACTOR_THRESHOLD:
                                    significant_climb_gradients.append(avg_grad_of_segment)
                                    start_idx = points_for_elevation_metrics.index(climb_start_point) # Find original index for debug
                                    print(f"    -> QUALIFIED as Significant Climb! Started near point index {start_idx} (approx {cumulative_distances_km_at_points[start_idx]:.2f} km)")
                            
                        current_climb_points = [] # Reset for next potential climb
                
                # Check if the very last segment was a climb
                if len(current_climb_points) >= 2:
                    climb_start_point = current_climb_points[0]
                    climb_end_point = current_climb_points[-1]
                    climb_segment_total_dist_m = 0
                    climb_segment_total_gain_m = 0
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
                        print(f"  Potential climb ended (end of route). Dist: {climb_segment_total_dist_m:.0f}m, Gain: {climb_segment_total_gain_m:.0f}m, AvgGrad: {avg_grad_of_segment:.2f}%, Factor: {climb_factor:.0f}")
                        if climb_segment_total_dist_m >= SIG_CLIMB_MIN_DISTANCE_M and \
                           avg_grad_of_segment >= SIG_CLIMB_MIN_GRADIENT_PERCENT and \
                           climb_factor >= SIG_CLIMB_FACTOR_THRESHOLD:
                            significant_climb_gradients.append(avg_grad_of_segment)
                            start_idx = points_for_elevation_metrics.index(climb_start_point)
                            print(f"    -> QUALIFIED as Significant Climb! Started near point index {start_idx} (approx {cumulative_distances_km_at_points[start_idx]:.2f} km)")
                print("--- End ACg Debugging ---\n")

            if significant_climb_gradients:
                acg = sum(significant_climb_gradients) / len(significant_climb_gradients)
            else:
                acg = 0.0
            
            print(f"Processed GPX file: {gpx_file_path}")
            print(f"Total Distance: {distance_km:.2f} km")
            print(f"Total Elevation Gain (TEGa - Raw): {total_elevation_gain_raw:.2f} m")
            print(f"Total Elevation Gain (TEGa - Smoothed, window {SMOOTHING_WINDOW_SIZE}): {total_elevation_gain_smoothed:.2f} m")
            print(f"TEGa value to be used by algorithm: {final_tega:.2f} m")
            print(f"Total Downhill Distance: {total_downhill_distance_km:.2f} km")
            print(f"PDD (Proportion of Distance Downhill): {pdd:.3f}")
            print(f"MCg (Max Climb Gradient over ~{MCG_SEGMENT_TARGET_DISTANCE_M}m segments, min dist {MIN_DIST_FOR_MCG_GRADIENT_CALC_M}m): {mcg:.2f}%")
            print(f"ACg (Average Gradient of Significant Climbs): {acg:.2f}%")

            return {
                "distance_km": distance_km, "TEGa": final_tega, "TEGa_raw": total_elevation_gain_raw,
                "TEGa_smoothed": total_elevation_gain_smoothed, "PDD": pdd, "MCg": mcg, "ACg": acg, 
                "ADg": None, "raw_points_count": len(all_points_original)
            }

    except Exception as e: # Catching generic Exception for broader error reporting
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
    return None

if __name__ == "__main__":
    your_actual_gpx_file = r"C:\Users\unwan\Downloads\Dales_Climbers_Classic.gpx"
    if your_actual_gpx_file:
        print(f"Attempting to process GPX file: {your_actual_gpx_file}")
        metrics = extract_metrics_from_gpx(your_actual_gpx_file, apply_smoothing=True) 
        if metrics:
            print("\nExtracted Metrics:")
            for key, value in metrics.items():
                if isinstance(value, (float, int)): print(f"  {key}: {value:.3f}")
                else: print(f"  {key}: {value}")
        else: print("Failed to extract metrics from GPX file.")
    else: print("GPX file path is not set. Please edit the script to provide a valid path.")
