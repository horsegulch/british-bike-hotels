# metric_extractor.py - Extracts key metrics and detailed track points from GPX and TCX files

import gpxpy
import gpxpy.gpx
from tcxparser import TCXParser 
from lxml import objectify # For fallback TCX parsing
import copy 
import traceback 
from datetime import datetime 
import os 

# Assuming config.py and utils.py are in the same directory or accessible in PYTHONPATH
import config 
from common.utils import haversine_distance, get_smoothed_elevations

class TrackPoint:
    """Represents a single point in a track with latitude, longitude, elevation, and time."""
    def __init__(self, latitude, longitude, elevation=None, time=None):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.time = time 

    def __repr__(self):
        return f"TrackPoint(lat={self.latitude}, lon={self.longitude}, ele={self.elevation}, time={self.time})"

def _extract_trackpoints_from_gpx(gpx_file_path: str) -> tuple[str, list[TrackPoint]]:
    all_points_list = []
    route_name_from_gpx = "N/A" 
    try:
        with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file_content_stream:
            gpx = gpxpy.parse(gpx_file_content_stream)
        
        if gpx.name: route_name_from_gpx = gpx.name
        elif gpx.tracks and len(gpx.tracks) > 0 and gpx.tracks[0].name: 
            route_name_from_gpx = gpx.tracks[0].name
        elif gpx.routes and len(gpx.routes) > 0 and gpx.routes[0].name: 
            route_name_from_gpx = gpx.routes[0].name
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    all_points_list.append(TrackPoint(point.latitude, point.longitude, point.elevation, point.time))
        for route in gpx.routes: 
            for point in route.points: 
                all_points_list.append(TrackPoint(point.latitude, point.longitude, point.elevation, point.time))
    except Exception as e:
        print(f"Error during GPX parsing for {gpx_file_path}: {e}")
        traceback.print_exc()
        return "N/A (GPX Parse Error)", []
    return route_name_from_gpx, all_points_list

def _parse_tcx_course_manually(tcx_file_path: str) -> tuple[str, list[TrackPoint]]:
    all_points_list = []
    route_name_from_tcx = "N/A (TCX Course - Manual)"
    try:
        with open(tcx_file_path, 'rb') as f: 
            tree = objectify.parse(f)
        root = tree.getroot()
        if hasattr(root, 'Courses') and hasattr(root.Courses, 'Course'):
            course_elements = root.Courses.Course
            if not hasattr(course_elements, '__iter__') or isinstance(course_elements, str):
                course_elements = [course_elements] if hasattr(course_elements, 'Name') else []
            if course_elements:
                course = course_elements[0] 
                if hasattr(course, 'Name') and course.Name is not None:
                    route_name_from_tcx = str(course.Name.text if hasattr(course.Name, 'text') else course.Name)
                if hasattr(course, 'Track') and hasattr(course.Track, 'Trackpoint'):
                    trackpoints_nodes = course.Track.Trackpoint
                    if not hasattr(trackpoints_nodes, '__iter__') or isinstance(trackpoints_nodes, str):
                        trackpoints_nodes = [trackpoints_nodes] if hasattr(trackpoints_nodes, 'Position') else []
                    for tp_node in trackpoints_nodes:
                        lat, lon, ele, time_obj = None, None, None, None
                        if hasattr(tp_node, 'Position'):
                            if hasattr(tp_node.Position, 'LatitudeDegrees'): lat = float(tp_node.Position.LatitudeDegrees.text)
                            if hasattr(tp_node.Position, 'LongitudeDegrees'): lon = float(tp_node.Position.LongitudeDegrees.text)
                        if hasattr(tp_node, 'AltitudeMeters') and tp_node.AltitudeMeters is not None:
                            ele_text = tp_node.AltitudeMeters.text
                            if ele_text is not None: ele = float(ele_text)
                        if hasattr(tp_node, 'Time') and tp_node.Time is not None:
                            time_str = tp_node.Time.text
                            if time_str:
                                try: time_obj = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
                                except ValueError: print(f"Warning: Could not parse time '{time_str}' in TCX course (manual parse).")
                        if lat is not None and lon is not None:
                            all_points_list.append(TrackPoint(lat, lon, ele, time_obj))
        if all_points_list: print(f"Info: Successfully parsed TCX as Course (manual lxml): {tcx_file_path}")
        else:
            print(f"Warning: No trackpoints found in TCX (manual lxml Course parse) for: {tcx_file_path}")
            if route_name_from_tcx == "N/A (TCX Course - Manual)": route_name_from_tcx = "N/A (TCX Manual Parse Failed)"
    except Exception as e_lxml:
        print(f"Error during manual lxml TCX Course parsing for {tcx_file_path}: {e_lxml}")
        traceback.print_exc()
        return "N/A (TCX Manual Parse Error)", []
    return route_name_from_tcx, all_points_list

def _extract_trackpoints_from_tcx(tcx_file_path: str) -> tuple[str, list[TrackPoint]]:
    all_points_list = []
    route_name_from_tcx = "N/A (TCX Data)"
    parser = None
    try:
        parser = TCXParser(tcx_file_path)
    except AttributeError as e_attr_init:
        if "Activities" in str(e_attr_init).lower() or "'NoneType' object has no attribute 'Activities'" in str(e_attr_init):
            print(f"Info: TCXParser init failed for {tcx_file_path} (likely missing <Activities>). Attempting manual lxml parse for Course structure.")
            return _parse_tcx_course_manually(tcx_file_path)
        else:
            print(f"Error initializing TCXParser for {tcx_file_path}: {e_attr_init}.")
            traceback.print_exc()
            return "N/A (TCX Init Error)", []
    except Exception as e_init_other:
        print(f"An unexpected error occurred while initializing TCXParser for {tcx_file_path}: {e_init_other}")
        traceback.print_exc()
        return "N/A (TCX Init Error)", []
    try:
        activity_name_candidate = "TCX Activity"
        if hasattr(parser, 'activity_type') and parser.activity_type:
            activity_name_candidate = f"TCX Activity: {parser.activity_type}"
        lat_lon_tuples = parser.position_values()
        if lat_lon_tuples:
            elevations = parser.altitude_points()
            times_from_parser = parser.time_values()
            num_points = len(lat_lon_tuples)
            for i in range(num_points):
                lat, lon = lat_lon_tuples[i]
                ele = elevations[i] if i < len(elevations) and elevations[i] is not None else None
                time_val = times_from_parser[i] if i < len(times_from_parser) and times_from_parser[i] is not None else None
                all_points_list.append(TrackPoint(lat, lon, ele, time_val))
            if all_points_list:
                route_name_from_tcx = activity_name_candidate
                print(f"Info: Successfully parsed TCX as Activity: {tcx_file_path}")
                return route_name_from_tcx, all_points_list
        if hasattr(parser, 'courses') and parser.courses and len(parser.courses) > 0:
            course = parser.courses[0]
            if hasattr(course, 'name') and course.name: route_name_from_tcx = course.name
            elif route_name_from_tcx == "N/A (TCX Data)" or "Activity" in route_name_from_tcx: route_name_from_tcx = "TCX Course"
            if hasattr(course, 'laps') and course.laps:
                for lap in course.laps:
                    if hasattr(lap, 'track') and lap.track:
                        for trackpoint_data in lap.track: 
                            lat = trackpoint_data.get('latitude')
                            lon = trackpoint_data.get('longitude')
                            ele = trackpoint_data.get('altitude_meters')
                            time_val_str = trackpoint_data.get('time') 
                            time_obj = None
                            if time_val_str:
                                try:
                                    if isinstance(time_val_str, datetime): time_obj = time_val_str
                                    else: time_obj = datetime.fromisoformat(str(time_val_str).replace('Z', '+00:00'))
                                except ValueError: print(f"Warning: Could not parse time '{time_val_str}' in TCX course trackpoint (parser.courses).")
                            if lat is not None and lon is not None:
                                all_points_list.append(TrackPoint(float(lat), float(lon), float(ele) if ele is not None else None, time_obj))
            if all_points_list:
                print(f"Info: Successfully parsed TCX as Course (via parser.courses): {tcx_file_path}")
                return route_name_from_tcx, all_points_list
        print(f"Warning: TCX file {tcx_file_path} did not yield points from TCXParser standard attributes.")
        return "N/A (Unknown TCX Structure via TCXParser)", []
    except Exception as e_gen:
        print(f"An unexpected error after TCXParser init for {tcx_file_path}: {e_gen}")
        traceback.print_exc()
        return "N/A (TCX General Parse Error)", []

def _calculate_distances_and_pdd(
    points: list[TrackPoint], 
    total_distance_km_ref: list[float], 
    total_downhill_distance_km_ref: list[float], 
    cumulative_distances_km_at_points_ref: list[float] 
):
    if len(points) < 1: return 
    current_cumulative_dist_km = 0.0 
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        segment_dist_km = 0.0
        if p1.latitude is not None and p1.longitude is not None and \
           p2.latitude is not None and p2.longitude is not None:
            segment_dist_km = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
        total_distance_km_ref[0] += segment_dist_km
        current_cumulative_dist_km += segment_dist_km
        if i + 1 < len(cumulative_distances_km_at_points_ref):
            cumulative_distances_km_at_points_ref[i+1] = current_cumulative_dist_km
        if p1.elevation is not None and p2.elevation is not None:
            elevation_diff = p2.elevation - p1.elevation
            if elevation_diff < 0: 
                total_downhill_distance_km_ref[0] += segment_dist_km

def _calculate_tega(points: list[TrackPoint]) -> float:
    tega = 0.0
    if len(points) < 2: return tega
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        if p1.elevation is not None and p2.elevation is not None:
            if p2.elevation > p1.elevation:
                tega += (p2.elevation - p1.elevation)
    return tega

def _calculate_mcg(points: list[TrackPoint], cumulative_distances_km: list[float]) -> float:
    mcg_metric = 0.0
    if len(points) < 2: return mcg_metric
    for i in range(len(points) -1): 
        start_point_mcg_segment = points[i]
        current_segment_dist_m = 0.0
        end_point_idx = i 
        for j in range(i + 1, len(points)): 
            p1_seg, p2_seg = points[j-1], points[j]
            dist_between_m = 0.0
            if p1_seg.latitude is not None and p1_seg.longitude is not None and \
               p2_seg.latitude is not None and p2_seg.longitude is not None:
                dist_between_m = haversine_distance(p1_seg.latitude, p1_seg.longitude, 
                                                    p2_seg.latitude, p2_seg.longitude) * 1000 
            if current_segment_dist_m + dist_between_m <= config.MCG_SEGMENT_TARGET_DISTANCE_M:
                current_segment_dist_m += dist_between_m
                end_point_idx = j
            else: 
                if dist_between_m > 0 and current_segment_dist_m == 0 : 
                    current_segment_dist_m = dist_between_m
                    end_point_idx = j
                break 
        if end_point_idx > i and current_segment_dist_m >= config.MIN_DIST_FOR_MCG_GRADIENT_CALC_M:
            actual_end_point_mcg_segment = points[end_point_idx]
            if start_point_mcg_segment.elevation is not None and actual_end_point_mcg_segment.elevation is not None:
                elevation_change_m = actual_end_point_mcg_segment.elevation - start_point_mcg_segment.elevation
                if elevation_change_m > 0: 
                    gradient_percent = (elevation_change_m / current_segment_dist_m) * 100.0
                    if gradient_percent > mcg_metric:
                        mcg_metric = gradient_percent
    return mcg_metric

def _calculate_acg_or_adg(points: list[TrackPoint], cumulative_distances_km: list[float], is_climb: bool) -> float:
    significant_segment_gradients = []
    current_segment_points = [] 
    potential_start_threshold = config.POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD if is_climb else config.POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD
    min_segment_dist_m = config.SIG_CLIMB_MIN_DISTANCE_M if is_climb else config.SIG_DESCENT_MIN_DISTANCE_M
    min_segment_grad_percent = config.SIG_CLIMB_MIN_GRADIENT_PERCENT if is_climb else config.SIG_DESCENT_MIN_GRADIENT_PERCENT
    factor_threshold = config.SIG_CLIMB_FACTOR_THRESHOLD if is_climb else None 
    if len(points) < 2: return 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        segment_dist_m = 0.0
        if p1.latitude is not None and p1.longitude is not None and \
           p2.latitude is not None and p2.longitude is not None:
            segment_dist_m = haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude) * 1000
        elevation_change_m = 0.0
        if p1.elevation is not None and p2.elevation is not None:
            elevation_change_m = p2.elevation - p1.elevation
        current_segment_gradient = (elevation_change_m / segment_dist_m * 100.0) if segment_dist_m > 0 else 0
        condition_met = (is_climb and elevation_change_m > 0 and current_segment_gradient >= potential_start_threshold) or \
                        (not is_climb and elevation_change_m < 0 and current_segment_gradient <= potential_start_threshold)
        if condition_met:
            if not current_segment_points: 
                current_segment_points.append(p1)
            current_segment_points.append(p2)
        else: 
            if len(current_segment_points) >= 2: 
                seg_start_point = current_segment_points[0]
                seg_end_point = current_segment_points[-1]
                seg_total_dist_m = 0
                seg_total_ele_change_for_grad_calc = 0 
                if is_climb: 
                    current_gain_in_segment = 0
                    for k in range(len(current_segment_points) - 1):
                        cp1, cp2 = current_segment_points[k], current_segment_points[k+1]
                        d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000 if (cp1.latitude and cp2.latitude) else 0
                        seg_total_dist_m += d
                        if cp1.elevation is not None and cp2.elevation is not None:
                            current_gain_in_segment += max(0, cp2.elevation - cp1.elevation)
                    seg_total_ele_change_for_grad_calc = current_gain_in_segment
                else: 
                    if seg_start_point.elevation is not None and seg_end_point.elevation is not None:
                         seg_total_ele_change_for_grad_calc = seg_end_point.elevation - seg_start_point.elevation 
                    for k in range(len(current_segment_points) - 1):
                        cp1, cp2 = current_segment_points[k], current_segment_points[k+1]
                        d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000 if (cp1.latitude and cp2.latitude) else 0
                        seg_total_dist_m += d
                if seg_total_dist_m > 0:
                    avg_grad_of_segment = (seg_total_ele_change_for_grad_calc / seg_total_dist_m) * 100.0
                    qualified = False
                    if is_climb:
                        climb_factor = seg_total_dist_m * avg_grad_of_segment 
                        if seg_total_dist_m >= min_segment_dist_m and \
                           avg_grad_of_segment >= min_segment_grad_percent and \
                           (factor_threshold is None or climb_factor >= factor_threshold):
                            qualified = True
                    else: 
                        if seg_total_dist_m >= min_segment_dist_m and \
                           avg_grad_of_segment <= min_segment_grad_percent: 
                            qualified = True
                    if qualified:
                        significant_segment_gradients.append(abs(avg_grad_of_segment))
            current_segment_points = [] 
    if len(current_segment_points) >= 2:
        seg_start_point = current_segment_points[0]
        seg_end_point = current_segment_points[-1]
        seg_total_dist_m = 0
        seg_total_ele_change_for_grad_calc = 0
        if is_climb:
            current_gain_in_segment = 0
            for k in range(len(current_segment_points) - 1):
                cp1, cp2 = current_segment_points[k], current_segment_points[k+1]
                d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000 if (cp1.latitude and cp2.latitude) else 0
                seg_total_dist_m += d
                if cp1.elevation is not None and cp2.elevation is not None: current_gain_in_segment += max(0, cp2.elevation - cp1.elevation)
            seg_total_ele_change_for_grad_calc = current_gain_in_segment
        else: 
            if seg_start_point.elevation is not None and seg_end_point.elevation is not None:
                 seg_total_ele_change_for_grad_calc = seg_end_point.elevation - seg_start_point.elevation
            for k in range(len(current_segment_points) - 1):
                cp1, cp2 = current_segment_points[k], current_segment_points[k+1]
                d = haversine_distance(cp1.latitude, cp1.longitude, cp2.latitude, cp2.longitude) * 1000 if (cp1.latitude and cp2.latitude) else 0
                seg_total_dist_m += d
        if seg_total_dist_m > 0:
            avg_grad_of_segment = (seg_total_ele_change_for_grad_calc / seg_total_dist_m) * 100.0
            qualified = False
            if is_climb:
                climb_factor = seg_total_dist_m * avg_grad_of_segment
                if seg_total_dist_m >= min_segment_dist_m and avg_grad_of_segment >= min_segment_grad_percent and (factor_threshold is None or climb_factor >= factor_threshold): qualified = True
            else: 
                if seg_total_dist_m >= min_segment_dist_m and avg_grad_of_segment <= min_segment_grad_percent: qualified = True
            if qualified: significant_segment_gradients.append(abs(avg_grad_of_segment))
    return sum(significant_segment_gradients) / len(significant_segment_gradients) if significant_segment_gradients else 0.0

def get_route_metrics(file_path: str, file_extension: str, apply_smoothing: bool = True):
    route_name_from_file = "N/A"
    all_points_original_parsed: list[TrackPoint] = [] 
    metrics_result = { 
        "route_name": route_name_from_file, "distance_km": 0.0, "TEGa": 0.0, 
        "TEGa_raw": 0.0, "TEGa_smoothed": 0.0, "PDD": 0.0, 
        "MCg": 0.0, "ACg": 0.0, "ADg": 0.0, 
        "raw_points_count": 0,
        "track_points": [],
        "start_lat": None, 
        "start_lon": None  
    }
    try:
        if file_extension == 'gpx':
            route_name_from_file, all_points_original_parsed = _extract_trackpoints_from_gpx(file_path)
        elif file_extension == 'tcx':
            route_name_from_file, all_points_original_parsed = _extract_trackpoints_from_tcx(file_path)
            if "Error)" in route_name_from_file and not all_points_original_parsed: 
                 metrics_result["route_name"] = route_name_from_file 
                 return metrics_result 
        else:
            print(f"Error: Unsupported file extension: {file_extension}")
            metrics_result["route_name"] = f"Unsupported File Type ({file_extension})"
            return metrics_result 
        
        metrics_result["route_name"] = route_name_from_file
        metrics_result["raw_points_count"] = len(all_points_original_parsed)

        if not all_points_original_parsed or len(all_points_original_parsed) < 2:
            print(f"Warning: No usable points after parsing {file_extension.upper()} file: {file_path}")
            if not ("Error)" in metrics_result["route_name"] or "Unsupported" in metrics_result["route_name"]): 
                metrics_result["route_name"] = f"N/A (No Points in {file_extension.upper()})"
            return metrics_result 

        if all_points_original_parsed:
            metrics_result["start_lat"] = all_points_original_parsed[0].latitude
            metrics_result["start_lon"] = all_points_original_parsed[0].longitude

        points_for_elevation_metrics = [copy.deepcopy(p) for p in all_points_original_parsed]
        if apply_smoothing and len(points_for_elevation_metrics) >= config.SMOOTHING_WINDOW_SIZE:
            original_elevations = [p.elevation for p in points_for_elevation_metrics if p.elevation is not None]
            if len(original_elevations) >= config.SMOOTHING_WINDOW_SIZE: 
                smoothed_elevation_values = get_smoothed_elevations(original_elevations, config.SMOOTHING_WINDOW_SIZE)
                ele_idx = 0 
                for p_obj in points_for_elevation_metrics:
                    if p_obj.elevation is not None: 
                        if ele_idx < len(smoothed_elevation_values):
                            p_obj.elevation = smoothed_elevation_values[ele_idx]
                        ele_idx +=1 
        try: metrics_result["TEGa_raw"] = _calculate_tega(all_points_original_parsed)
        except Exception as e: print(f"Error calculating TEGa_raw: {e}\n{traceback.format_exc()}")
        try:
            tega_smoothed = _calculate_tega(points_for_elevation_metrics)
            metrics_result["TEGa_smoothed"] = tega_smoothed
            metrics_result["TEGa"] = tega_smoothed 
        except Exception as e: print(f"Error calculating TEGa_smoothed: {e}\n{traceback.format_exc()}")
        total_dist_km_list = [0.0] 
        total_downhill_distance_km_list = [0.0] 
        cumulative_distances_km = [0.0] * len(points_for_elevation_metrics) 
        try:
            _calculate_distances_and_pdd(points_for_elevation_metrics, 
                                         total_dist_km_list, 
                                         total_downhill_distance_km_list, 
                                         cumulative_distances_km)
            metrics_result["distance_km"] = total_dist_km_list[0]
            if metrics_result["distance_km"] > 0:
                metrics_result["PDD"] = total_downhill_distance_km_list[0] / metrics_result["distance_km"]
            else:
                metrics_result["PDD"] = 0.0
        except Exception as e: 
            print(f"Error calculating total distance or PDD: {e}\n{traceback.format_exc()}")
            if "distance_km" not in metrics_result or metrics_result["distance_km"] == 0.0:
                 metrics_result["distance_km"] = sum(haversine_distance(points_for_elevation_metrics[i].latitude, points_for_elevation_metrics[i].longitude, 
                                                                        points_for_elevation_metrics[i+1].latitude, points_for_elevation_metrics[i+1].longitude)
                                                     for i in range(len(points_for_elevation_metrics)-1) 
                                                     if points_for_elevation_metrics[i].latitude is not None and points_for_elevation_metrics[i+1].latitude is not None)
        try: metrics_result["MCg"] = _calculate_mcg(points_for_elevation_metrics, cumulative_distances_km)
        except Exception as e: print(f"Error calculating MCg: {e}\n{traceback.format_exc()}")
        try: metrics_result["ACg"] = _calculate_acg_or_adg(points_for_elevation_metrics, cumulative_distances_km, is_climb=True)
        except Exception as e: print(f"Error calculating ACg: {e}\n{traceback.format_exc()}")
        try: metrics_result["ADg"] = _calculate_acg_or_adg(points_for_elevation_metrics, cumulative_distances_km, is_climb=False)
        except Exception as e: print(f"Error calculating ADg: {e}\n{traceback.format_exc()}")
        detailed_track_points = []
        for i, point_obj in enumerate(points_for_elevation_metrics):
            detailed_track_points.append({
                "lat": point_obj.latitude,
                "lon": point_obj.longitude,
                "ele": point_obj.elevation, 
                "dist": cumulative_distances_km[i] 
            })
        metrics_result["track_points"] = detailed_track_points
        return metrics_result
    except FileNotFoundError: 
        print(f"Error: File not found: {file_path}")
        metrics_result["route_name"] = "N/A (File Not Found)"
    except gpxpy.gpx.GPXXMLSyntaxException: 
        print(f"Error: GPX XML Syntax Error for: {file_path}")
        metrics_result["route_name"] = "N/A (GPX Syntax Error)"
    except ImportError as e_imp: 
        if 'tcxparser' in str(e_imp).lower():
            print(f"Error: python-tcxparser library not found. Please install it to process .tcx files ('pip install python-tcxparser').")
            metrics_result["route_name"] = "N/A (TCX Parser Missing)"
        else:
            print(f"Error: Missing import for {file_path}: {e_imp}")
            metrics_result["route_name"] = "N/A (Import Error)"
    except Exception as e_main: 
        print(f"Error: Unexpected error during metric extraction for {file_path}: {e_main}")
        print(traceback.format_exc()) 
        if metrics_result["route_name"] == "N/A": 
            metrics_result["route_name"] = "N/A (Extraction Error)"
    return metrics_result if metrics_result.get("distance_km") is not None else None

if __name__ == '__main__':
    if not os.path.exists("config.py"):
        print("Creating dummy config.py for testing metric_extractor.py")
        with open("config.py", "w") as f:
            f.write("SMOOTHING_WINDOW_SIZE = 7\nMCG_SEGMENT_TARGET_DISTANCE_M = 100.0\nMIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0\n"
                    "SIG_CLIMB_FACTOR_THRESHOLD = 3500.0\nSIG_CLIMB_MIN_DISTANCE_M = 250.0\nSIG_CLIMB_MIN_GRADIENT_PERCENT = 3.0\n"
                    "POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD = 1.0\nSIG_DESCENT_MIN_DISTANCE_M = 500.0\n"
                    "SIG_DESCENT_MIN_GRADIENT_PERCENT = -3.0\nPOTENTIAL_DESCENT_START_GRADIENT_THRESHOLD = -1.0\n")
    if not os.path.exists("utils.py"):
        print("Creating dummy utils.py for testing metric_extractor.py")
        with open("utils.py", "w") as f:
            f.write("from math import radians, sin, cos, sqrt, atan2\n\n"
                    "def haversine_distance(lat1, lon1, lat2, lon2):\n"
                    "    R = 6371 \n"
                    "    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])\n"
                    "    dlon = lon2_rad - lon1_rad; dlat = lat2_rad - lat1_rad\n"
                    "    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2\n"
                    "    c = 2 * atan2(sqrt(a), sqrt(1 - a)); return R * c\n\n"
                    "def get_smoothed_elevations(original_elevations, window_size):\n"
                    "    if not original_elevations or window_size < 2 or len(original_elevations) < window_size: return list(original_elevations)\n"
                    "    smoothed_elevations = list(original_elevations); half_window = window_size // 2\n"
                    "    for i in range(half_window, len(original_elevations) - half_window):\n"
                    "        window_values = original_elevations[i - half_window : i + half_window + 1]\n"
                    "        valid_window_values = [v for v in window_values if isinstance(v, (int, float))]\n"
                    "        if len(valid_window_values) == window_size : smoothed_elevations[i] = sum(valid_window_values) / len(valid_window_values)\n"
                    "    return smoothed_elevations\n")
    test_gpx_file = "metric_extractor_test_route.gpx"
    if not os.path.exists(test_gpx_file):
        print(f"Creating dummy GPX file: {test_gpx_file}")
        gpx_content = """<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Dummy">
<metadata><name>GPX Test Route</name></metadata>
<trk><name>GPX Test Track</name><trkseg>
<trkpt lat="50.0" lon="0.0"><ele>10</ele><time>2023-01-01T10:00:00Z</time></trkpt>
<trkpt lat="50.001" lon="0.001"><ele>20</ele><time>2023-01-01T10:01:00Z</time></trkpt>
<trkpt lat="50.002" lon="0.002"><ele>15</ele><time>2023-01-01T10:02:00Z</time></trkpt>
<trkpt lat="50.003" lon="0.003"><ele>30</ele><time>2023-01-01T10:03:00Z</time></trkpt>
</trkseg></trk></gpx>"""
        with open(test_gpx_file, 'w') as f: f.write(gpx_content)
    print(f"\n--- Testing metric_extractor.py with GPX: {test_gpx_file} ---")
    gpx_metrics = get_route_metrics(test_gpx_file, 'gpx')
    if gpx_metrics:
        print("GPX Metrics:")
        for k, v_val in gpx_metrics.items():
            if k == "track_points":
                print(f"  {k}: (list of {len(v_val)} points)")
            else:
                print(f"  {k}: {v_val:.3f}" if isinstance(v_val, float) else f"  {k}: {v_val}")
    else:
        print("  Failed to get GPX metrics.")
    test_tcx_activity_file = "metric_extractor_test_activity.tcx" 
    if not os.path.exists(test_tcx_activity_file):
        print(f"Creating dummy TCX file (Activity): {test_tcx_activity_file}")
        tcx_content_activity = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
<Activities><Activity Sport="Biking"><Id>2025-05-14T12:00:00Z</Id><Lap StartTime="2025-05-14T12:00:00Z">
<Track>
  <Trackpoint><Time>2025-05-14T12:00:00Z</Time><Position><LatitudeDegrees>50.0</LatitudeDegrees><LongitudeDegrees>0.0</LongitudeDegrees></Position><AltitudeMeters>10.0</AltitudeMeters></Trackpoint>
  <Trackpoint><Time>2025-05-14T12:01:00Z</Time><Position><LatitudeDegrees>50.001</LatitudeDegrees><LongitudeDegrees>0.001</LongitudeDegrees></Position><AltitudeMeters>20.0</AltitudeMeters></Trackpoint>
</Track></Lap></Activity></Activities></TrainingCenterDatabase>"""
        with open(test_tcx_activity_file, 'w') as f: f.write(tcx_content_activity)
    print(f"\n--- Testing metric_extractor.py with TCX (Activity type): {test_tcx_activity_file} ---")
    try:
        tcx_metrics_activity = get_route_metrics(test_tcx_activity_file, 'tcx')
        if tcx_metrics_activity:
            print("TCX Metrics (Activity):")
            for k, v_val in tcx_metrics_activity.items():
                if k == "track_points":
                    print(f"  {k}: (list of {len(v_val)} points)")
                else:
                    print(f"  {k}: {v_val:.3f}" if isinstance(v_val, float) else f"  {k}: {v_val}")
        else:
            print("  Failed to get TCX Activity metrics.")
    except ImportError:
        print("  Skipping TCX Activity test: tcxparser library not found. Install with 'pip install python-tcxparser'")
    except Exception as e_tcx_act:
        print(f"  Error during TCX Activity test: {e_tcx_act}")
    test_tcx_course_file = "metric_extractor_test_course.tcx" 
    if not os.path.exists(test_tcx_course_file):
        print(f"Creating dummy TCX Course file: {test_tcx_course_file}")
        tcx_content_course = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd">
<Courses><Course><Name>TCX Course Test (No Activities Tag)</Name><Lap><Track>
  <Trackpoint><Time>2025-05-14T13:00:00Z</Time><Position><LatitudeDegrees>51.0</LatitudeDegrees><LongitudeDegrees>0.1</LongitudeDegrees></Position><AltitudeMeters>100.0</AltitudeMeters></Trackpoint>
  <Trackpoint><Time>2025-05-14T13:01:00Z</Time><Position><LatitudeDegrees>51.001</LatitudeDegrees><LongitudeDegrees>0.101</LongitudeDegrees></Position><AltitudeMeters>120.0</AltitudeMeters></Trackpoint>
</Track></Lap></Course></Courses></TrainingCenterDatabase>"""
        with open(test_tcx_course_file, 'w') as f: f.write(tcx_content_course)
    print(f"\n--- Testing metric_extractor.py with TCX (Course type, no Activities tag): {test_tcx_course_file} ---") # Corrected this line
    try:
        tcx_metrics_course = get_route_metrics(test_tcx_course_file, 'tcx')
        if tcx_metrics_course:
            print("TCX Metrics (Course):")
            for k, v_val in tcx_metrics_course.items():
                if k == "track_points":
                    print(f"  {k}: (list of {len(v_val)} points)")
                else:
                    print(f"  {k}: {v_val:.3f}" if isinstance(v_val, float) else f"  {k}: {v_val}")
        else:
            print("  Failed to get TCX Course metrics.")
    except ImportError:
        print("  Skipping TCX Course test: tcxparser library not found.")
    except Exception as e_tcx_crs:
        print(f"  Error during TCX Course test: {e_tcx_crs}")