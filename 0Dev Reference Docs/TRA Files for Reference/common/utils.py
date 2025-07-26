# blueprints/utils.py

import os
from urllib.parse import urlparse
from math import radians, sin, cos, sqrt, atan2

# These are the same functions you had in app.py

ALLOWED_EXTENSIONS = {'gpx', 'tcx'}

def allowed_file(filename):
    """Checks if a filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension_from_url(url):
    """Parses a URL to find a file extension."""
    try:
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return ext[1:] # Return the extension without the dot
    except Exception:
        # It's better to log this in the calling function, but for now, we return None
        pass
    return None

import json
import datetime
from bson import ObjectId
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError

# This needs to be initialized once
geolocator = Nominatim(user_agent="route_scorer_app_v1_unique_id/1.0")

class JSONEncoder(json.JSONEncoder):
    """ Custom JSON encoder to handle MongoDB's ObjectId and datetime objects. """
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, dict) and "$date" in o:
            try:
                date_val = o["$date"]
                if isinstance(date_val, (int, float)):
                    return datetime.datetime.fromtimestamp(date_val / 1000, tz=datetime.timezone.utc).isoformat()
                elif isinstance(date_val, str):
                    return datetime.datetime.fromisoformat(date_val.replace("Z", "+00:00")).isoformat()
            except (ValueError, TypeError):
                # Best to log this error in the app context if possible
                pass
        return json.JSONEncoder.default(self, o)

def get_start_location_name(lat, lon):
    """ Reverse geocodes coordinates to get a human-readable location name. """
    if lat is None or lon is None:
        return "N/A (No Coords)"
    try:
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10, language='en')
        if location and location.address:
            address_parts = location.raw.get('address', {})
            city = address_parts.get('city')
            town = address_parts.get('town')
            village = address_parts.get('village')
            country = address_parts.get('country', '')
            if city: return f"{city}, {country}"
            if town: return f"{town}, {country}"
            if village: return f"{village}, {country}"
            # Fallback for less common address formats
            parts = location.address.split(',')
            return f"{parts[-2].strip()}, {parts[-1].strip()}" if len(parts) >= 2 else location.address
        else:
            return "N/A (Geocode No Result)"
    except GeocoderTimedOut: return "N/A (Geocode Timeout)"
    except (GeocoderUnavailable, GeocoderServiceError): return "N/A (Geocode Service Error)"
    except Exception: return "N/A (Geocode Error)"

# Add this new function to blueprints/utils.py
import re # Make sure 'import re' is at the top of utils.py
from urllib.parse import urlparse, parse_qs

# In blueprints/utils.py

def transform_to_download_url(url):
    """
    Checks a URL and transforms it into a direct GPX download link if it's from a known provider.
    """
    # Ride with GPS
    if "ridewithgps.com/routes/" in url:
        match = re.search(r'/routes/(\d+)', url)
        if match:
            route_id = match.group(1)
            base_download_url = f"https://ridewithgps.com/routes/{route_id}.gpx"
            
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            privacy_code = query_params.get('privacy_code', [None])[0]

            if privacy_code:
                return f"{base_download_url}?privacy_code={privacy_code}"
            else:
                return base_download_url

    # Strava (returns a message for manual download)
    elif "strava.com/routes/" in url:
        return "strava_manual_download"

    # --- NEW: Add this block for Plotaroute ---
    elif "plotaroute.com/route/" in url:
        match = re.search(r'/route/(\d+)', url)
        if match:
            route_id = match.group(1)
            # Plotaroute uses a simple /download/ path
            return f"https://www.plotaroute.com/download/{route_id}"
    
    # If no match, return the original URL
    return url

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees).
    """
    # Radius of earth in kilometers
    R = 6371.0

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

def get_smoothed_elevations(original_elevations: list, window_size: int) -> list:
    """
    Applies a simple moving average to a list of elevation values.
    `window_size` should be an odd integer.
    """
    if not original_elevations or window_size < 2 or len(original_elevations) < window_size:
        return list(original_elevations) 

    smoothed_elevations = list(original_elevations)
    half_window = window_size // 2

    for i in range(half_window, len(original_elevations) - half_window):
        window_values = original_elevations[i - half_window : i + half_window + 1]
        
        valid_window_values = [v for v in window_values if isinstance(v, (int, float))]
        
        if len(valid_window_values) == window_size: 
            smoothed_elevations[i] = sum(valid_window_values) / len(valid_window_values)
            
    return smoothed_elevations