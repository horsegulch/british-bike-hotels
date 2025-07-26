import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2

# --- Configuration (you might make these configurable later) ---
SMOOTHING_WINDOW_SIZE = 3 # For a simple moving average on elevation (optional)

# --- Helper Functions ---

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers.
    """
    R = 6371  # Radius of earth in kilometers.
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance

def smooth_elevation(points, window_size=3):
    """
    Apply a simple moving average to elevation data.
    Returns a new list of points with smoothed elevation.
    This is a basic smoother; more advanced techniques exist.
    """
    if not points or window_size < 2:
        return points # No smoothing if not enough points or window too small

    smoothed_points = []
    elevation_values = [p.elevation for p in points if p.elevation is not None]
    
    if not elevation_values: # No elevation data to smooth
        return points

    # Pad the start and end to handle edges for the moving average
    # For simplicity, we'll just not smooth the very start/end points that don't have a full window
    # A more robust implementation might use different padding or edge handling.
    
    new_elevations = list(elevation_values) # Start with original elevations

    for i in range(len(elevation_values)):
        window = []
        # Define the window for averaging
        # Example: for window_size 3, current point i, window is [i-1, i, i+1]
        # For window_size 5, current point i, window is [i-2, i-1, i, i+1, i+2]
        half_window = window_size // 2
        
        start_index = max(0, i - half_window)
        end_index = min(len(elevation_values), i + half_window + 1)
        
        current_window_values = elevation_values[start_index:end_index]
        
        if current_window_values:
            new_elevations[i] = sum(current_window_values) / len(current_window_values)

    # Create new point objects with smoothed elevation
    # This assumes point objects are simple (e.g. gpxpy.gpx.GPXTrackPoint)
    # and we can create new ones or modify copies.
    # For gpxpy, it's better to modify elevation of existing points if possible,
    # or handle this carefully.
    
    idx_ele = 0
    for i, p_orig in enumerate(points):
        # Create a new point to avoid modifying the original gpxpy object directly in this example
        # In a real scenario, you might choose to modify p_orig.elevation
        p_new = gpxpy.gpx.GPXTrackPoint(latitude=p_orig.latitude, longitude=p_orig.longitude, elevation=p_orig.elevation, time=p_orig.time)
        if p_new.elevation is not None and idx_ele < len(new_elevations):
            p_new.elevation = new_elevations[idx_ele]
            idx_ele += 1
        smoothed_points.append(p_new)
        
    return smoothed_points


def extract_basic_metrics_from_gpx(gpx_file_path: str):
    """
    Parses a GPX file and extracts basic metrics:
    distance_km, total_elevation_gain (TEGa).
    
    This is a simplified example. Error handling and more complex metric
    calculations would be needed for a production system.
    """
    distance_km = 0.0
    total_elevation_gain = 0.0
    
    all_points = [] # To store all track points from the GPX file

    try:
        with open(gpx_file_path, 'r') as gpx_file_content:
            gpx = gpxpy.parse(gpx_file_content)

            for track in gpx.tracks:
                for segment in track.segments:
                    all_points.extend(segment.points)
            
            # For routes (less common for recorded activities, but good to check)
            for route in gpx.routes:
                all_points.extend(route.points)

            if not all_points:
                print(f"No points found in GPX file: {gpx_file_path}")
                return None # Or raise an error

            # --- Optional: Smooth elevation data ---
            # This can help reduce noise before calculating gradients or TEGa
            # Note: Smoothing can slightly alter TEGa. Decide if you want TEGa from raw or smoothed.
            # For this example, we'll calculate TEGa from smoothed points.
            print(f"Original points: {len(all_points)}")
            # smoothed_points = smooth_elevation(all_points, window_size=SMOOTHING_WINDOW_SIZE)
            # Using all_points directly for now, smoothing can be added as a refinement step
            # as the simple smoother above needs careful integration with gpxpy point objects
            # or a more generic point structure.
            # Let's assume for now we work with original points for TEGa and distance.
            # The `smooth_elevation` function provided is a template.
            
            points_to_process = all_points # Use original points for now

            # --- Calculate Distance and TEGa ---
            if len(points_to_process) < 2:
                print("Not enough points to calculate distance or elevation gain.")
                # Return 0 for distance and TEGa, or handle as an error
                return {
                    "distance_km": 0.0,
                    "TEGa": 0.0,
                    # ... other metrics will be None or 0 initially
                }

            for i in range(len(points_to_process) - 1):
                p1 = points_to_process[i]
                p2 = points_to_process[i+1]

                # Calculate distance between p1 and p2
                if p1.latitude is not None and p1.longitude is not None and \
                   p2.latitude is not None and p2.longitude is not None:
                    segment_distance = haversine_distance(p1.latitude, p1.longitude, 
                                                          p2.latitude, p2.longitude)
                    distance_km += segment_distance

                # Calculate elevation gain
                if p1.elevation is not None and p2.elevation is not None:
                    elevation_diff = p2.elevation - p1.elevation
                    if elevation_diff > 0:
                        total_elevation_gain += elevation_diff
            
            print(f"Processed GPX file: {gpx_file_path}")
            print(f"Total Distance: {distance_km:.2f} km")
            print(f"Total Elevation Gain (TEGa): {total_elevation_gain:.2f} m")

            # Here, you would then proceed to calculate PDD, ACg, MCg, ADg
            # using the 'points_to_process' list.

            return {
                "distance_km": distance_km,
                "TEGa": total_elevation_gain,
                # Placeholder for other metrics
                "PDD": None, 
                "ACg": None,
                "MCg": None,
                "ADg": None,
                "raw_points_count": len(all_points) # For debugging
            }

    except FileNotFoundError:
        print(f"Error: GPX file not found at {gpx_file_path}")
        return None
    except gpxpy.gpx.GPXXMLSyntaxException:
        print(f"Error: Could not parse GPX file (XML syntax error) at {gpx_file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Example of how you might call this ---
if __name__ == "__main__":
    # You would replace 'your_route.gpx' with an actual GPX file path
    # To run this example, you need to:
    # 1. Install gpxpy: pip install gpxpy
    # 2. Have a GPX file named 'your_route.gpx' in the same directory,
    #    or provide the correct path to an existing GPX file.
    
    # Create a dummy GPX file for testing if you don't have one
    #gpx_test_content = """
    #<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Gemini">
    #  <trk>
    #    <name>Test Track</name>
     #   <trkseg>
      #    <trkpt lat="50.8225" lon="-0.1372"><ele>10</ele><time>2025-05-08T10:00:00Z</time></trkpt>
       #   <trkpt lat="50.8235" lon="-0.1382"><ele>15</ele><time>2025-05-08T10:01:00Z</time></trkpt>
        #  <trkpt lat="50.8245" lon="-0.1392"><ele>12</ele><time>2025-05-08T10:02:00Z</time></trkpt>
         # <trkpt lat="50.8255" lon="-0.1402"><ele>25</ele><time>2025-05-08T10:03:00Z</time></trkpt>
        #</trkseg>
      #</trk>
    #</gpx>
    ""
    dummy_gpx_file = r"C:\Users\unwan\Downloads\Dales_Climbers_Classic.gpx"
    #with open(dummy_gpx_file, 'w') as f:
     #   f.write(gpx_test_content)

    print(f"Attempting to process GPX file: {dummy_gpx_file}")
    metrics = extract_basic_metrics_from_gpx(r"C:\Users\unwan\Downloads\Dales_Climbers_Classic.gpx")

    if metrics:
        print("\nExtracted Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # Now you could feed these into your difficulty algorithm (if all metrics were calculated)
        # For example:
        # if all(m is not None for m in [metrics['distance_km'], metrics['TEGa'], metrics['ACg'], ...]):
        #    total_difficulty = calculate_total_difficulty(
        #        distance_km=metrics['distance_km'],
        #        tega=metrics['TEGa'],
        #        # ... and so on for ACg, MCg, PDD, ADg
        #    )
        #    print(f"Calculated Total Difficulty: {total_difficulty:.2f}")
        # else:
        #    print("Could not calculate total difficulty as some metrics are missing.")
    else:
        print("Failed to extract metrics from GPX file.")

