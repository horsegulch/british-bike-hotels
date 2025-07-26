import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2
import copy # For deep copying points if necessary

# --- Configuration ---
SMOOTHING_WINDOW_SIZE = 7 # Defaulting to 7 as per user's successful test for TEGa
MCG_SEGMENT_TARGET_DISTANCE_M = 100.0 # Target distance in meters for MCg segments
MIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0 # Minimum distance for a segment to be considered for gradient calculation (to avoid division by tiny numbers)

# --- Helper Functions ---

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in kilometers."""
    R = 6371  # Radius of Earth in kilometers
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_smoothed_elevations(original_elevations, window_size):
    """
    Applies a simple moving average to a list of elevation values.
    Returns a new list of smoothed elevation values.
    """
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
    Includes elevation smoothing, PDD, and MCg calculation with debugging including start distance.
    """
    distance_km = 0.0
    total_elevation_gain_raw = 0.0
    total_elevation_gain_smoothed = 0.0
    total_downhill_distance_km = 0.0 
    pdd = 0.0 
    mcg = 0.0 
    
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
                print("Not enough points to calculate metrics.")
                return {"distance_km": 0.0, "TEGa": 0.0, "TEGa_raw": 0.0, "TEGa_smoothed": 0.0, 
                        "PDD": 0.0, "MCg": 0.0, "ACg": None, "ADg": None}

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
                        else:
                            new_p.elevation = p_orig.elevation
                        temp_smoothed_points_list.append(new_p)
                    points_for_elevation_metrics = temp_smoothed_points_list
                    print(f"Elevation smoothing applied with window size: {SMOOTHING_WINDOW_SIZE}")
                else:
                    print("Not enough elevation points to apply smoothing, using raw elevation.")
            elif apply_smoothing:
                 print("Not enough points overall to apply smoothing, using raw elevation.")

            # --- Calculate Total Distance (using original points for accuracy) ---
            # This loop calculates the overall distance_km
            for i in range(len(points_for_distance_calculation) - 1):
                p1 = points_for_distance_calculation[i]
                p2 = points_for_distance_calculation[i+1]
                if p1.latitude is not None and p1.longitude is not None and \
                   p2.latitude is not None and p2.longitude is not None:
                    distance_km += haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)

            # --- Calculate TEGa (Raw, using original points) ---
            for i in range(len(all_points_original) - 1):
                p1 = all_points_original[i]
                p2 = all_points_original[i+1]
                if p1.elevation is not None and p2.elevation is not None:
                    elevation_diff = p2.elevation - p1.elevation
                    if elevation_diff > 0:
                        total_elevation_gain_raw += elevation_diff
            
            # --- Calculate TEGa (Smoothed), PDD, and Cumulative Distances (using points_for_elevation_metrics) ---
            cumulative_distances_km_at_points = [0.0] * len(points_for_elevation_metrics) # Initialize with zeros

            if len(points_for_elevation_metrics) >= 1: # Ensure there's at least one point
                current_cumulative_dist_km = 0.0
                # cumulative_distances_km_at_points[0] is already 0.0

                for i in range(len(points_for_elevation_metrics) - 1):
                    p1 = points_for_elevation_metrics[i]
                    p2 = points_for_elevation_metrics[i+1]
                    segment_dist_km = 0.0
                    if p1.latitude is not None and p1.longitude is not None and \
                       p2.latitude is not None and p2.longitude is not None:
                        segment_dist_km = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)

                    current_cumulative_dist_km += segment_dist_km
                    if i + 1 < len(cumulative_distances_km_at_points): # Check index bounds
                         cumulative_distances_km_at_points[i+1] = current_cumulative_dist_km

                    if p1.elevation is not None and p2.elevation is not None:
                        elevation_diff = p2.elevation - p1.elevation
                        if elevation_diff > 0:
                            total_elevation_gain_smoothed += elevation_diff
                        elif elevation_diff < 0: 
                            total_downhill_distance_km += segment_dist_km
            
            if distance_km > 0: # Use the accurately calculated total distance_km
                pdd = total_downhill_distance_km / distance_km
            else:
                pdd = 0.0
            
            final_tega = total_elevation_gain_smoothed

            # --- Calculate MCg (Max Climb Gradient over ~MCG_SEGMENT_TARGET_DISTANCE_M segments) ---
            if len(points_for_elevation_metrics) >= 2:
                print("\n--- Debugging MCg Calculation ---") 
                for i in range(len(points_for_elevation_metrics) -1): # Iterate up to the second to last point
                    start_point_mcg_segment = points_for_elevation_metrics[i]
                    current_segment_dist_m = 0.0
                    end_point_idx = i 

                    # Try to build a segment of approx MCG_SEGMENT_TARGET_DISTANCE_M
                    for j in range(i + 1, len(points_for_elevation_metrics)):
                        p1_seg = points_for_elevation_metrics[j-1]
                        p2_seg = points_for_elevation_metrics[j]
                        dist_between_m = 0.0
                        if p1_seg.latitude is not None and p1_seg.longitude is not None and \
                           p2_seg.latitude is not None and p2_seg.longitude is not None:
                            dist_between_m = haversine_distance(p1_seg.latitude, p1_seg.longitude, 
                                                                p2_seg.latitude, p2_seg.longitude) * 1000 # convert km to m
                        
                        if current_segment_dist_m + dist_between_m <= MCG_SEGMENT_TARGET_DISTANCE_M:
                            current_segment_dist_m += dist_between_m
                            end_point_idx = j
                        else:
                            # If adding the next point exceeds target, this segment (up to j-1) is formed.
                            # If current_segment_dist_m is 0 and this first dist_between_m itself exceeds target,
                            # then this first segment becomes our segment to check.
                            if dist_between_m > 0 and current_segment_dist_m == 0 : 
                                current_segment_dist_m = dist_between_m
                                end_point_idx = j # The segment is just from i to j
                            break # Segment formed or next point too far

                    # Ensure we have a valid segment
                    if end_point_idx > i and current_segment_dist_m >= MIN_DIST_FOR_MCG_GRADIENT_CALC_M:
                        actual_end_point_mcg_segment = points_for_elevation_metrics[end_point_idx]
                        
                        if start_point_mcg_segment.elevation is not None and actual_end_point_mcg_segment.elevation is not None:
                            elevation_change_m = actual_end_point_mcg_segment.elevation - start_point_mcg_segment.elevation
                            if elevation_change_m > 0: # Only consider climbs
                                gradient_percent = (elevation_change_m / current_segment_dist_m) * 100.0
                                if gradient_percent > mcg:
                                    segment_start_km = cumulative_distances_km_at_points[i] # Get cumulative distance at start of segment
                                    print(f"  New MCg Candidate: {gradient_percent:.2f}% (Old MCg: {mcg:.2f}%) at approx {segment_start_km:.2f} km into route")
                                    print(f"    - Elev Change: {elevation_change_m:.2f}m over {current_segment_dist_m:.2f}m")
                                    print(f"    - Start Ele: {start_point_mcg_segment.elevation:.2f} (idx {i}), End Ele: {actual_end_point_mcg_segment.elevation:.2f} (idx {end_point_idx})")
                                    mcg = gradient_percent
                print("--- End MCg Debugging ---\n")
            
            print(f"Processed GPX file: {gpx_file_path}")
            print(f"Total Distance: {distance_km:.2f} km")
            print(f"Total Elevation Gain (TEGa - Raw): {total_elevation_gain_raw:.2f} m")
            print(f"Total Elevation Gain (TEGa - Smoothed, window {SMOOTHING_WINDOW_SIZE if apply_smoothing else 'N/A'}): {total_elevation_gain_smoothed:.2f} m")
            print(f"TEGa value to be used by algorithm: {final_tega:.2f} m")
            print(f"Total Downhill Distance: {total_downhill_distance_km:.2f} km")
            print(f"PDD (Proportion of Distance Downhill): {pdd:.3f}")
            print(f"MCg (Max Climb Gradient over ~{MCG_SEGMENT_TARGET_DISTANCE_M}m segments, min dist {MIN_DIST_FOR_MCG_GRADIENT_CALC_M}m): {mcg:.2f}%")

            return {
                "distance_km": distance_km,
                "TEGa": final_tega,
                "TEGa_raw": total_elevation_gain_raw,
                "TEGa_smoothed": total_elevation_gain_smoothed,
                "PDD": pdd, 
                "MCg": mcg,
                "ACg": None, 
                "ADg": None, 
                "raw_points_count": len(all_points_original)
            }

    except FileNotFoundError:
        print(f"Error: GPX file not found at {gpx_file_path}")
    except gpxpy.gpx.GPXXMLSyntaxException:
        print(f"Error: Could not parse GPX file (XML syntax error) at {gpx_file_path}")
    except UnicodeDecodeError:
        print(f"Error: Unicode decoding error. Ensure the GPX file is UTF-8 encoded or try a different encoding.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

if __name__ == "__main__":
    your_actual_gpx_file = r"C:\Users\unwan\Downloads\Dales_Climbers_Classic.gpx"

    if your_actual_gpx_file:
        print(f"Attempting to process GPX file: {your_actual_gpx_file}")
        metrics = extract_metrics_from_gpx(your_actual_gpx_file, apply_smoothing=True) 

        if metrics:
            print("\nExtracted Metrics:")
            for key, value in metrics.items():
                if isinstance(value, (float, int)):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("Failed to extract metrics from GPX file.")
    else:
        print("GPX file path is not set. Please edit the script to provide a valid path.")

