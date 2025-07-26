# app/utils/gpx_utils.py

import gpxpy
import gpxpy.gpx
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees).
    """
    R = 6371  # Radius of earth in kilometers
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def calculate_difficulty(distance, elevation):
    """
    Calculates a simple difficulty rating for a route.
    """
    if distance > 80 or elevation > 1500:
        return 'Hard'
    elif distance > 40 or elevation > 750:
        return 'Moderate'
    else:
        return 'Easy'

def parse_gpx_file(file_stream):
    """
    Parses a GPX file stream to extract key metrics and detailed track points.
    """
    gpx = gpxpy.parse(file_stream)
    
    total_distance_km = 0.0
    total_elevation_gain = 0.0
    track_points = []
    
    last_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if last_point:
                    # Calculate distance
                    segment_distance = haversine_distance(last_point.latitude, last_point.longitude, point.latitude, point.longitude)
                    total_distance_km += segment_distance
                    
                    # Calculate elevation gain
                    elevation_diff = point.elevation - last_point.elevation
                    if elevation_diff > 0:
                        total_elevation_gain += elevation_diff
                
                track_points.append({
                    'lat': point.latitude,
                    'lon': point.longitude,
                    'ele': point.elevation,
                    'dist': total_distance_km  # Cumulative distance
                })
                
                last_point = point

    difficulty = calculate_difficulty(total_distance_km, total_elevation_gain)

    return {
        'distance_km': round(total_distance_km, 1),
        'elevation_m': round(total_elevation_gain, 1),
        'difficulty': difficulty,
        'track_points': track_points
    }
