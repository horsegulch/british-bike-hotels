# app.py - Corrected Version

import os
import traceback
import uuid
import requests
import datetime
import json
import shutil
import hashlib
from PIL import Image
from staticmap import StaticMap, Line # Existing import for thumbnails
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from flask_pymongo import PyMongo
from bson import ObjectId, errors
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# --- For Reverse Geocoding ---
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError

# --- Import from our new modules ---
try:
    from metric_extractor import get_route_metrics
    from difficulty_calculator import calculate_total_difficulty
except ImportError as e:
    print(f"Error importing modules: {e}. Make sure metric_extractor.py and difficulty_calculator.py are in the same directory or accessible in PYTHONPATH.")
    raise

# --- Path Constants (defined before app initialization) ---
UPLOAD_FOLDER = 'uploads'
PERMANENT_STORAGE_FOLDER = 'route_files_store'
ALLOWED_EXTENSIONS = {'gpx', 'tcx'}
STATIC_MAP_THUMBNAILS_FOLDER = os.path.join('static', 'map_thumbnails') # Path string for thumbnails

# --- Flask App Initialization ---
app = Flask(__name__) # Initialize Flask app

# --- Flask App Configuration (now 'app' object exists) ---
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_STORAGE_FOLDER'] = PERMANENT_STORAGE_FOLDER
app.config['STATIC_MAP_THUMBNAILS_FOLDER'] = STATIC_MAP_THUMBNAILS_FOLDER # Assign to app.config
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["MONGO_URI"] = "mongodb://localhost:27017/route_scorer_db"
app.config['SECRET_KEY'] = 'Riptide0-Stage0-Figment2-Cone7' 

# --- Initialize Flask Extensions ---
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'

# --- User Class and Loader ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password')
        self.favorites = user_data.get('favorites', []) 
        self.ridden = user_data.get('ridden', [])     

    @staticmethod
    def get(user_id):
        try:
            user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(user_data)
            return None
        except (errors.InvalidId, TypeError):
            return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- Geocoding Setup ---
geolocator = Nominatim(user_agent="route_scorer_app_v1_unique_id/1.0")

# --- Database Setup (PyMongo) ---
try:
    mongo = PyMongo(app)
    app.logger.info("PyMongo initialized with local MongoDB.")
except Exception as e_mongo_init:
    app.logger.error(f"Error initializing PyMongo with local MongoDB: {e_mongo_init}")
    app.logger.error("Please ensure your local MongoDB server is running and accessible.")

# --- Create Static Directories if they don't exist (after app.config is set) ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['PERMANENT_STORAGE_FOLDER']):
    os.makedirs(app.config['PERMANENT_STORAGE_FOLDER'])
if not os.path.exists('avatars_store'): # This one doesn't use app.config directly
    os.makedirs('avatars_store')
if not os.path.exists(app.config['STATIC_MAP_THUMBNAILS_FOLDER']): # Create thumbnail folder
    os.makedirs(app.config['STATIC_MAP_THUMBNAILS_FOLDER'])


# --- Helper Functions (allowed_file, get_file_extension_from_url, JSONEncoder, get_start_location_name) ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension_from_url(url):
    try:
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return ext[1:]
    except Exception:
        app.logger.warning(f"Could not parse URL to get extension: {url}", exc_info=True)
    return None

class JSONEncoder(json.JSONEncoder):
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
            except (ValueError, TypeError) as e:
                app.logger.warning(f"JSONEncoder: Could not parse $date object: {o}, error: {e}")
                pass
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

def get_start_location_name(lat, lon):
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
            return location.address.split(',')[-2].strip() + ", " + location.address.split(',')[-1].strip() if len(location.address.split(',')) >=2 else location.address
        else:
            return "N/A (Geocode No Result)"
    except GeocoderTimedOut: return "N/A (Geocode Timeout)"
    except (GeocoderUnavailable, GeocoderServiceError): return "N/A (Geocode Service Error)"
    except Exception: return "N/A (Geocode Error)"

# --- Core Route Processing Logic ---
def process_route_data(filepath, file_extension, original_identifier, is_upload=False, temp_upload_path=None):
    try:
        metrics_data = get_route_metrics(filepath, file_extension, apply_smoothing=True)
        if not metrics_data: return {"error": "Failed to extract metrics."}, 500
        
        track_points = metrics_data.get("track_points", [])
        line_coordinates = []
        if track_points:
            # Assuming track_points is a list of [lon, lat] or (lon, lat)
            # If it's [lat, lon], you need to swap:
            line_coordinates = [(point[1], point[0]) for point in track_points if len(point) == 2]
            #line_coordinates = [tuple(point) for point in track_points if len(point) == 2]


        start_lat, start_lon = metrics_data.get("start_lat"), metrics_data.get("start_lon")
        required_keys = ["distance_km", "TEGa", "ACg", "MCg", "PDD", "ADg"]
        if any(metrics_data.get(key) is None for key in required_keys):
            return {"error": "Metric extraction incomplete for calculation."}, 500
        
        start_location_name = get_start_location_name(start_lat, start_lon)
        total_difficulty = calculate_total_difficulty(
            metrics_data['distance_km'], metrics_data['TEGa'], metrics_data['ACg'],
            metrics_data['MCg'], metrics_data['PDD'], metrics_data['ADg']
        )

        app.logger.info(f"--- Debugging Thumbnail Generation for: {original_identifier} ---")
        app.logger.info(f"Raw track_points from metrics_data (first 5): {track_points[:5] if track_points else 'Track_points is empty or None'}")
        app.logger.info(f"Processed line_coordinates for staticmap (first 5): {line_coordinates[:5] if line_coordinates else 'Line_coordinates is empty'}") # This will use the corrected line_coordinates
        app.logger.info(f"Number of line_coordinates: {len(line_coordinates)}")

        # This is your current line_coordinates logic (with the swap for (lon, lat))
        # Add a check for None inside the points themselves just in case.
        if track_points:
            line_coordinates = [(point[1], point[0]) for point in track_points if len(point) == 2 and point[0] is not None and point[1] is not None]
        else:
            line_coordinates = [] # Ensure it's an empty list if track_points is None or empty

        app.logger.info(f"Processed line_coordinates for staticmap (first 5): {line_coordinates[:5] if line_coordinates else 'Line_coordinates is empty'}")
        app.logger.info(f"Number of line_coordinates: {len(line_coordinates)}")

        # --- Thumbnail Generation Logic ---
        actual_thumbnail_url = None # Default to None
        if line_coordinates: 
            app.logger.info("Condition 'if line_coordinates:' is TRUE. Attempting thumbnail generation.") # ADD THIS
            try:
                thumbnail_filename = f"{uuid.uuid4().hex}.png"
                # (rest of your thumbnail generation code...)
                # ...
                m = StaticMap(300, 200) 
                line = Line(line_coordinates, color="blue", width=3)
                m.add_line(line)
                image = m.render(zoom_auto=True) 
                
                thumbnail_save_path = os.path.join(app.config['STATIC_MAP_THUMBNAILS_FOLDER'], thumbnail_filename) # Ensure path is defined before save
                image.save(thumbnail_save_path)
                
                actual_thumbnail_url = url_for('static', filename=f'map_thumbnails/{thumbnail_filename}')
                app.logger.info(f"Successfully generated thumbnail: {actual_thumbnail_url}")

            except Exception as e_thumb:
                app.logger.error(f"Error generating thumbnail for {original_identifier}: {e_thumb}", exc_info=True)
                # actual_thumbnail_url remains None
        else:
            app.logger.warning("Condition 'if line_coordinates:' is FALSE. Skipping thumbnail generation.") # ADD THIS
        # --- End Thumbnail Generation Logic ---

        db_save_data = {
            "original_identifier": original_identifier,
            "route_name": metrics_data.get("route_name", "N/A"),
            "metrics_summary": {k: v for k,v in metrics_data.items() if k not in ["track_points", "start_lat", "start_lon"]},
            "start_location_name": start_location_name,
            "start_coordinates": {"lat": start_lat, "lon": start_lon} if start_lat and start_lon else None,
            "track_points": track_points, 
            "difficulty_score": round(total_difficulty, 2), 
            "file_type": file_extension,
            "source_type": 'upload' if is_upload else 'url', 
            "processed_at": datetime.datetime.utcnow(),
            "stored_file_name": None, 
            "likes_count": 0, 
            "comments": [],
            "creator_id": ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
            "creator_username": current_user.username if current_user.is_authenticated else "Anonymous",
            "actual_thumbnail_url": actual_thumbnail_url 
        }
        
        if is_upload and temp_upload_path:
            permanent_filename = f"{uuid.uuid4().hex}.{file_extension}"
            permanent_path = os.path.join(app.config['PERMANENT_STORAGE_FOLDER'], permanent_filename)
            shutil.copy2(temp_upload_path, permanent_path)
            db_save_data["stored_file_name"] = permanent_filename
            
        mongo.db.routes.insert_one(db_save_data)
        return {"filename": original_identifier, "metrics": db_save_data["metrics_summary"], "difficulty_score": db_save_data["difficulty_score"]}, 200
    except Exception as e:
        app.logger.error(f"Error in process_route_data for {original_identifier}: {e}", exc_info=True)
        return {"error": "Internal server error processing data."}, 500

# --- Routes (Endpoints) ---
@app.route('/')
def serve_index():
    try:
        routes_collection = mongo.db.routes
        users_collection = mongo.db.users
        
        raw_latest_routes = list(routes_collection.find().sort("processed_at", -1).limit(8))
        raw_top_routes = list(routes_collection.find().sort("likes_count", -1).limit(8))

        def process_route_list_for_index(route_list):
            processed_list = []
            for route in route_list:
                if '_id' in route and isinstance(route['_id'], ObjectId): route['_id'] = str(route['_id'])
                route['creator_avatar_url'] = None
                if 'creator_id' in route and route['creator_id']:
                    try:
                        creator = users_collection.find_one({"_id": ObjectId(str(route['creator_id']))}) 
                        if creator:
                            if 'avatar_filename' in creator and creator['avatar_filename']:
                                route['creator_avatar_url'] = url_for('serve_avatar', filename=creator['avatar_filename'])
                            else:
                                email_hash = hashlib.md5(creator.get('email', '').lower().encode('utf-8')).hexdigest()
                                route['creator_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"
                    except Exception as e_avatar: app.logger.error(f"Error fetching avatar for {route.get('creator_id')}: {e_avatar}")
                
                # Use actual_thumbnail_url if present, else placeholder
                if route.get('actual_thumbnail_url'): 
                    route['static_map_thumbnail_url'] = route['actual_thumbnail_url']
                else:
                    route['static_map_thumbnail_url'] = url_for('static', filename='images/map_placeholder.png')
                processed_list.append(route)
            return processed_list

        latest_routes = process_route_list_for_index(raw_latest_routes)
        top_routes = process_route_list_for_index(raw_top_routes)
        
        return render_template('index.html', latest_routes=latest_routes, top_routes=top_routes)
    except Exception as e:
        app.logger.error(f"Error in serve_index: {e}", exc_info=True)
        return render_template('index.html', latest_routes=[], top_routes=[])

@app.route('/process_route_file', methods=['POST'])
def process_route_file_endpoint():
    if 'gpx_file' not in request.files: return jsonify({"error": "No file part."}), 400
    file = request.files['gpx_file']
    if file.filename == '': return jsonify({"error": "No selected file."}), 400
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        temp_name = f"{uuid.uuid4().hex}_{original_filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_name)
        try:
            file.save(temp_path)
            response, status = process_route_data(temp_path, file_ext, original_filename, True, temp_path)
            return jsonify(response), status
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
    return jsonify({"error": "Invalid file type."}), 400

@app.route('/process_route_url', methods=['POST'])
def process_route_url_endpoint():
    if not request.is_json: return jsonify({"error": "Request must be JSON."}), 415
    data = request.get_json()
    route_url = data.get('route_url')
    if not route_url: return jsonify({"error": "Missing 'route_url'."}), 400
    temp_filepath = None
    try:
        file_ext = get_file_extension_from_url(route_url)
        if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": "Invalid URL extension."}), 400
        headers = {'User-Agent': 'RouteDifficultyScorer/1.0'}
        url_res = requests.get(route_url, stream=True, timeout=30, headers=headers)
        url_res.raise_for_status()
        base_name = os.path.basename(urlparse(route_url).path)
        safe_base = secure_filename(base_name) if base_name and allowed_file(base_name) else f"url_dl_{uuid.uuid4().hex[:4]}"
        temp_filename = f"{safe_base}.{file_ext}"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        with open(temp_filepath, 'wb') as f: shutil.copyfileobj(url_res.raw, f)
        response, status = process_route_data(temp_filepath, file_ext, route_url)
        return jsonify(response), status
    except requests.exceptions.RequestException as e_req:
        return jsonify({"error": f"URL fetch error: {e_req}"}), 400
    finally:
        if temp_filepath and os.path.exists(temp_filepath): os.remove(temp_filepath)

@app.route('/api/list_saved_routes', methods=['GET'])
def list_saved_routes():
    try:
        routes_collection = mongo.db.routes
        all_routes_cursor = routes_collection.find({}, {"track_points": 0}) 
        routes_list = []
        for route in all_routes_cursor:
            if '_id' in route and isinstance(route['_id'], ObjectId):
                route['_id'] = str(route['_id'])
            if 'processed_at' in route and isinstance(route['processed_at'], datetime.datetime):
                route['processed_at'] = route['processed_at'].isoformat()
            if 'creator_id' in route and route['creator_id'] is not None and isinstance(route['creator_id'], ObjectId):
                route['creator_id'] = str(route['creator_id'])
            if 'metrics_summary' in route and isinstance(route['metrics_summary'], dict):
                for key, value in route['metrics_summary'].items():
                    if isinstance(value, datetime.datetime): route['metrics_summary'][key] = value.isoformat()
                    elif isinstance(value, ObjectId): route['metrics_summary'][key] = str(value)
            if 'comments' in route and isinstance(route['comments'], list):
                for comment in route['comments']:
                    if isinstance(comment, dict):
                        if '_id' in comment and isinstance(comment['_id'], ObjectId): comment['_id'] = str(comment['_id'])
                        if 'author_id' in comment and comment['author_id'] is not None and isinstance(comment['author_id'], ObjectId): comment['author_id'] = str(comment['author_id'])
                        if 'timestamp' in comment and isinstance(comment['timestamp'], datetime.datetime): comment['timestamp'] = comment['timestamp'].isoformat()
            routes_list.append(route)
        return jsonify(routes_list)
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error listing routes: {e}", exc_info=True)
        return jsonify({"error": "Error listing routes."}), 500

@app.route('/api/routes/<route_id>', methods=['GET'])
def get_single_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        route_document = routes_collection.find_one({"_id": route_obj_id})
        if route_document: return jsonify(route_document) 
        return jsonify({"error": "Route not found"}), 404
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error getting route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error getting route."}), 500

@app.route('/api/routes/<route_id>/access_file', methods=['GET'])
def access_route_file(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        route_doc = routes_collection.find_one({"_id": route_obj_id})
        if not route_doc: return jsonify({"error": "Route not found"}), 404
        source_type = route_doc.get("source_type")
        if source_type == 'upload':
            stored_name = route_doc.get("stored_file_name")
            original_name = route_doc.get("original_identifier", stored_name)
            if not stored_name: return jsonify({"error": "Stored file path missing."}), 500
            directory = os.path.join(os.getcwd(), app.config['PERMANENT_STORAGE_FOLDER'])
            if not os.path.exists(os.path.join(directory, stored_name)): return jsonify({"error": "Stored file not on server."}), 404
            return send_from_directory(directory, stored_name, as_attachment=True, download_name=original_name)
        elif source_type == 'url':
            external_url = route_doc.get("original_identifier")
            if not external_url: return jsonify({"error": "External URL missing."}), 500
            return redirect(external_url)
        return jsonify({"error": "Unknown route source type."}), 500
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error accessing file for {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error accessing file."}), 500

@app.route('/api/routes/<route_id>/like', methods=['POST'])
@login_required
def like_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        result = routes_collection.update_one({"_id": route_obj_id}, {"$inc": {"likes_count": 1}})
        if result.matched_count == 0: return jsonify({"error": "Route not found"}), 404
        updated_doc = routes_collection.find_one({"_id": route_obj_id})
        return jsonify({"likes_count": updated_doc.get("likes_count", 0)}), 200
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e: return jsonify({"error": f"Error liking route: {e}"}), 500

@app.route('/api/routes/<route_id>/unlike', methods=['POST'])
@login_required
def unlike_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        result = routes_collection.update_one({"_id": route_obj_id, "likes_count": {"$gt": 0}}, {"$inc": {"likes_count": -1}})
        updated_doc = routes_collection.find_one({"_id": route_obj_id})
        if not updated_doc: return jsonify({"error": "Route not found"}), 404 
        return jsonify({"likes_count": updated_doc.get("likes_count", 0)}), 200
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e: return jsonify({"error": f"Error unliking route: {e}"}), 500

@app.route('/api/routes/<route_id>/comments', methods=['POST'])
@login_required
def add_comment_to_route(route_id):
    if not request.is_json: return jsonify({"error": "Request must be JSON."}), 415
    data = request.get_json()
    comment_text = data.get('text')
    if not comment_text: return jsonify({"error": "Missing comment text."}), 400
    try:
        routes_collection = mongo.db.routes
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        new_comment = {
            "_id": ObjectId(), "text": comment_text,
            "author_id": ObjectId(current_user.get_id()),
            "author_username": current_user.username,
            "timestamp": datetime.datetime.utcnow()
        }
        result = routes_collection.update_one({"_id": route_obj_id}, {"$push": {"comments": new_comment}})
        if result.matched_count == 0: return jsonify({"error": "Route not found"}), 404
        response_comment = {k: (str(v) if isinstance(v, ObjectId) else (v.isoformat() if isinstance(v, datetime.datetime) else v)) for k,v in new_comment.items()}
        return jsonify({"message": "Comment added.", "comment": response_comment}), 201
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error adding comment to {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error adding comment."}), 500

# --- Standard Page Routes ---
@app.route('/route/<route_id>')
def route_profile_page(route_id):
    is_favorited = False
    if current_user.is_authenticated:
        user = mongo.db.users.find_one({"_id": ObjectId(current_user.get_id())})
        if user and route_id in [str(fav) for fav in user.get('favorites', [])]: 
            is_favorited = True
    return render_template('route_profile.html', route_id=route_id, is_favorited=is_favorited)

@app.route('/browse')
def browse_routes_page():
    return render_template('browse_routes.html')

@app.route('/profile')
@login_required
def profile():
    user_id = ObjectId(current_user.get_id())
    user_data = mongo.db.users.find_one({"_id": user_id})
    if not user_data:
        app.logger.warning(f"User data not found for ID: {user_id}. Logging out.")
        return redirect(url_for('logout'))

    avatar_url = url_for('serve_avatar', filename=user_data['avatar_filename']) if 'avatar_filename' in user_data and user_data['avatar_filename'] \
        else f"https://www.gravatar.com/avatar/{hashlib.md5(user_data.get('email','').lower().encode('utf-8')).hexdigest()}?s=150&d=identicon"

    raw_uploaded_routes = list(mongo.db.routes.find({"creator_id": user_id}).sort("processed_at", -1))
    
    raw_favourited_routes = []
    if 'favorites' in user_data and user_data['favorites']:
        favorite_object_ids = []
        for fid in user_data['favorites']:
            fid_str = str(fid) 
            if ObjectId.is_valid(fid_str): 
                favorite_object_ids.append(ObjectId(fid_str))
            else:
                app.logger.warning(f"Invalid ObjectId string found in user {user_id}'s favorites: {fid_str}")
        
        if favorite_object_ids:
            raw_favourited_routes = list(mongo.db.routes.find({"_id": {"$in": favorite_object_ids}}))

    def process_profile_route_list(route_list_raw):
        # (This function was already well-defined for JSON serialization)
        processed_list = []
        for route in route_list_raw:
            if '_id' in route and isinstance(route['_id'], ObjectId): route['_id'] = str(route['_id'])
            if 'processed_at' in route and isinstance(route['processed_at'], datetime.datetime): route['processed_at'] = route['processed_at'].isoformat()
            if 'creator_id' in route and route['creator_id'] is not None and isinstance(route['creator_id'], ObjectId): route['creator_id'] = str(route['creator_id'])
            if 'metrics_summary' in route and isinstance(route['metrics_summary'], dict):
                for key, value in route['metrics_summary'].items():
                    if isinstance(value, datetime.datetime): route['metrics_summary'][key] = value.isoformat()
                    elif isinstance(value, ObjectId): route['metrics_summary'][key] = str(value)
            if 'comments' in route and isinstance(route['comments'], list):
                for comment in route['comments']:
                    if isinstance(comment, dict):
                        if '_id' in comment and isinstance(comment['_id'], ObjectId): comment['_id'] = str(comment['_id'])
                        if 'author_id' in comment and comment['author_id'] is not None and isinstance(comment['author_id'], ObjectId): comment['author_id'] = str(comment['author_id'])
                        if 'timestamp' in comment and isinstance(comment['timestamp'], datetime.datetime): comment['timestamp'] = comment['timestamp'].isoformat()
            processed_list.append(route)
        return processed_list

    uploaded_routes = process_profile_route_list(raw_uploaded_routes)
    favourited_routes = process_profile_route_list(raw_favourited_routes)

    return render_template('profile.html', 
                           user=user_data, 
                           avatar_url=avatar_url,
                           uploaded_routes=uploaded_routes, 
                           favourited_routes=favourited_routes)
                           
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = ObjectId(current_user.get_id())
    user_data = mongo.db.users.find_one({"_id": user_id})
    if request.method == 'POST':
        mongo.db.users.update_one({"_id": user_id}, {"$set": {
            "location": request.form.get('location'), "bio": request.form.get('bio')}})
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_image_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
                if 'avatar_filename' in user_data and user_data['avatar_filename']:
                    old_path = os.path.join('avatars_store', user_data['avatar_filename'])
                    if os.path.exists(old_path): os.remove(old_path)
                img = Image.open(file.stream)
                img.thumbnail((300, 300))
                img.save(os.path.join('avatars_store', new_filename))
                mongo.db.users.update_one({"_id": user_id}, {"$set": {"avatar_filename": new_filename}})
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=user_data)

@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory('avatars_store', filename)

@app.route('/add-routes')
@login_required
def add_routes_page():
    return render_template('add_routes.html')

# --- Auth Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('serve_index'))
    if request.method == 'POST':
        username, email, password = request.form.get('username'), request.form.get('email'), request.form.get('password')
        if mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
            return render_template('register.html', error="Username or email already exists.")
        mongo.db.users.insert_one({'username': username, 'email': email, 
                                   'password': bcrypt.generate_password_hash(password).decode('utf-8'),
                                   'favorites': [], 'ridden': []})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('serve_index'))
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        user_doc = mongo.db.users.find_one({'username': username})
        if user_doc and bcrypt.check_password_hash(user_doc['password'], password):
            login_user(User(user_doc), remember=request.form.get('remember') == 'on')
            return redirect(request.args.get('next') or url_for('serve_index'))
        return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('serve_index'))

# --- Favorite/Unfavorite Routes ---
@app.route('/api/routes/<route_id>/favorite', methods=['POST'])
@login_required
def favorite_route(route_id):
    try:
        mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$addToSet': {'favorites': ObjectId(route_id)}})
        return jsonify({"success": True}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/routes/<route_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_route(route_id):
    try:
        mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$pull': {'favorites': ObjectId(route_id)}})
        return jsonify({"success": True}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- Compare Routes ---
@app.route('/compare')
def compare_page():
    ids_str = request.args.get('ids', '')
    if not ids_str: return "No routes for comparison.", 400
    obj_ids = [ObjectId(id_str) for id_str in ids_str.split(',') if errors.is_valid(id_str)] # Changed from ObjectId.is_valid to errors.is_valid
    routes = list(mongo.db.routes.find({"_id": {"$in": obj_ids}}))
    processed_routes = [] # This list will hold routes processed for Jinja
    for route in routes:
        # (This function was already well-defined for JSON serialization)
        if '_id' in route and isinstance(route['_id'], ObjectId): route['_id'] = str(route['_id'])
        if 'processed_at' in route and isinstance(route['processed_at'], datetime.datetime): route['processed_at'] = route['processed_at'].isoformat()
        if 'creator_id' in route and route['creator_id'] is not None and isinstance(route['creator_id'], ObjectId): route['creator_id'] = str(route['creator_id'])
        if 'metrics_summary' in route and isinstance(route['metrics_summary'], dict):
            for k, v in route['metrics_summary'].items():
                if isinstance(v, datetime.datetime): route['metrics_summary'][k] = v.isoformat()
                elif isinstance(v, ObjectId): route['metrics_summary'][k] = str(v)
        if 'comments' in route and isinstance(route['comments'], list):
            for cmt in route['comments']:
                if isinstance(cmt, dict):
                    if '_id' in cmt and isinstance(cmt['_id'], ObjectId): cmt['_id'] = str(cmt['_id'])
                    if 'author_id' in cmt and cmt['author_id'] is not None and isinstance(cmt['author_id'], ObjectId): cmt['author_id'] = str(cmt['author_id'])
                    if 'timestamp' in cmt and isinstance(cmt['timestamp'], datetime.datetime): cmt['timestamp'] = cmt['timestamp'].isoformat()
        processed_routes.append(route)
    return render_template('compare.html', routes=processed_routes)


@app.route('/api/compare_data')
def compare_data_api():
    route_ids_str = request.args.get('ids', '')
    if not route_ids_str:
        return jsonify({"error": "No route IDs provided"}), 400

    id_strings = route_ids_str.split(',')
    object_ids = []
    for id_str in id_strings:
        if ObjectId.is_valid(id_str): 
            object_ids.append(ObjectId(id_str))
        else:
            app.logger.warning(f"Invalid ObjectId string in compare_data API: {id_str}")

    if not object_ids: 
         return jsonify({"error": "No valid route IDs provided for comparison"}), 400

    routes_from_db = list(mongo.db.routes.find({"_id": {"$in": object_ids}}))

    if not routes_from_db and id_strings:
        app.logger.warning(f"No routes found in DB for valid comparison IDs: {object_ids}")

    return jsonify(routes_from_db)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
