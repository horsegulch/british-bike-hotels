# app.py - Main Flask web application with Start Location Geocoding

import os
import traceback
import uuid
import requests
import datetime
import json
import shutil
import hashlib
from PIL import Image
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

# --- Configuration for Flask App ---
UPLOAD_FOLDER = 'uploads'
PERMANENT_STORAGE_FOLDER = 'route_files_store'
ALLOWED_EXTENSIONS = {'gpx', 'tcx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_STORAGE_FOLDER'] = PERMANENT_STORAGE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config["MONGO_URI"] = "mongodb://localhost:27017/route_scorer_db"

# +++ Add a secret key and initialise new extensions +++
app.config['SECRET_KEY'] = 'Riptide0-Stage0-Figment2-Cone7' # IMPORTANT: Change this to a random string
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to the 'login' route if a user tries to access a protected page
login_manager.login_message_category = 'info'

# +++ Add User class and user_loader function +++
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password')
        self.favorites = user_data.get('favorites', []) # For favorites feature
        self.ridden = user_data.get('ridden', [])     # For ridden feature

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
# +++ End of User class and loader +++

# --- Initialize Geocoder and PyMongo ---
# IMPORTANT: Provide a unique user_agent string for Nominatim as per their usage policy.
# Replace 'route_scorer_app_v1_unique_id' with something specific to your app/email.
geolocator = Nominatim(user_agent="route_scorer_app_v1_unique_id/1.0")

try:
    mongo = PyMongo(app)
    app.logger.info("PyMongo initialized with local MongoDB.")
except Exception as e_mongo_init:
    app.logger.error(f"Error initializing PyMongo with local MongoDB: {e_mongo_init}")
    app.logger.error("Please ensure your local MongoDB server is running and accessible.")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PERMANENT_STORAGE_FOLDER):
    os.makedirs(PERMANENT_STORAGE_FOLDER)
if not os.path.exists('avatars_store'):
    os.makedirs('avatars_store')

# --- Helper Functions ---
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
                if isinstance(o["$date"], (int, float)):
                    return datetime.datetime.fromtimestamp(o["$date"] / 1000, tz=datetime.timezone.utc).isoformat()
                elif isinstance(o["$date"], str):
                    return datetime.datetime.fromisoformat(o["$date"].replace("Z", "+00:00")).isoformat()
            except (ValueError, TypeError):
                pass
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

def get_start_location_name(lat, lon):
    """Helper function to get location name from lat/lon using Nominatim."""
    if lat is None or lon is None:
        return "N/A (No Coords)"
    try:
        # Nominatim requires coordinates as a "lat, lon" string
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10, language='en')
        if location and location.address:
            # Attempt to get a concise location name. This can be customized.
            # For example, city, town, or just a part of the address.
            # location.raw often contains address components like 'city', 'town', 'village', 'country'
            address_parts = location.raw.get('address', {})
            city = address_parts.get('city')
            town = address_parts.get('town')
            village = address_parts.get('village')
            country = address_parts.get('country', '')

            if city: return f"{city}, {country}"
            if town: return f"{town}, {country}"
            if village: return f"{village}, {country}"
            # Fallback to a more general part of the address or the full address
            return location.address.split(',')[-2].strip() + ", " + location.address.split(',')[-1].strip() if len(location.address.split(',')) >=2 else location.address

        else:
            return "N/A (Geocode No Result)"
    except GeocoderTimedOut:
        app.logger.warning("Nominatim reverse geocoding timed out.")
        return "N/A (Geocode Timeout)"
    except (GeocoderUnavailable, GeocoderServiceError) as e:
        app.logger.warning(f"Nominatim reverse geocoding service error: {e}")
        return "N/A (Geocode Service Error)"
    except Exception as e:
        app.logger.error(f"Unexpected error during reverse geocoding: {e}", exc_info=True)
        return "N/A (Geocode Error)"


def process_route_data(filepath, file_extension, original_identifier, is_upload=False, temp_upload_path=None):
    try:
        app.logger.info(f"Processing data for: {original_identifier}, type: {file_extension}")
        metrics_data = get_route_metrics(filepath, file_extension, apply_smoothing=True)

        if not metrics_data:
             app.logger.error(f"Failed to extract metrics from data: {original_identifier}")
             return {"error": f"Failed to extract metrics from {file_extension.upper()} data. Check server logs."}, 500

        track_points = metrics_data.get("track_points", [])
        start_lat = metrics_data.get("start_lat") # From metric_extractor
        start_lon = metrics_data.get("start_lon") # From metric_extractor

        required_keys_for_calc = ["distance_km", "TEGa", "ACg", "MCg", "PDD", "ADg"]
        if any(metrics_data.get(key) is None for key in required_keys_for_calc):
            missing_calc_keys = [key for key in required_keys_for_calc if metrics_data.get(key) is None]
            app.logger.error(f"Metric extraction incomplete for calculation for {original_identifier}. None values for: {missing_calc_keys}")
            return {"error": "Metric extraction incomplete for core calculation.", "details": f"Missing values for: {missing_calc_keys}"}, 500

        if metrics_data.get("route_name") == "N/A":
             app.logger.warning(f"Route name not found for {original_identifier}, using 'N/A'.")

        # --- Get Start Location Name ---
        start_location_name = get_start_location_name(start_lat, start_lon)
        app.logger.info(f"Start location for {original_identifier}: {start_location_name} (from {start_lat}, {start_lon})")
        # --- End Get Start Location Name ---

        total_difficulty = calculate_total_difficulty(
            distance_km = metrics_data['distance_km'],
            tega = metrics_data['TEGa'],
            acg = metrics_data['ACg'],
            mcg_val = metrics_data['MCg'],
            pdd = metrics_data['PDD'],
            adg = metrics_data['ADg']
        )
        app.logger.info(f"Calculated difficulty for {original_identifier}: {total_difficulty:.2f}")

        db_save_data = {
            "original_identifier": original_identifier,
            "route_name": metrics_data.get("route_name", "N/A"),
            "metrics_summary": {k: v for k, v in metrics_data.items() if k not in ["track_points", "start_lat", "start_lon"]}, # Exclude these from summary
            "start_location_name": start_location_name, # Add start location name
            "start_coordinates": {"lat": start_lat, "lon": start_lon} if start_lat and start_lon else None, # Store original coords too
            "track_points": track_points,
            "difficulty_score": round(total_difficulty, 2),
            "file_type": file_extension,
            "source_type": 'url' if not is_upload else 'upload',
            "processed_at": datetime.datetime.utcnow(),
            "stored_file_name": None,
            "likes_count": 0,
            "comments": [],
            # +++ Add creator information +++
            "creator_id": ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
            "creator_username": current_user.username if current_user.is_authenticated else "Anonymous"
        }

        if is_upload and temp_upload_path:
            permanent_filename = f"{uuid.uuid4().hex}.{file_extension}"
            permanent_file_full_path = os.path.join(app.config['PERMANENT_STORAGE_FOLDER'], permanent_filename)
            try:
                shutil.copy2(temp_upload_path, permanent_file_full_path)
                app.logger.info(f"Uploaded file '{original_identifier}' copied to permanent storage: '{permanent_file_full_path}'")
                db_save_data["stored_file_name"] = permanent_filename
            except Exception as e_copy:
                app.logger.error(f"Error copying uploaded file to permanent storage: {e_copy}", exc_info=True)
                db_save_data["stored_file_name"] = "COPY_ERROR"

        try:
            routes_collection = mongo.db.routes
            insert_result = routes_collection.insert_one(db_save_data)
            app.logger.info(f"Data for '{original_identifier}' saved to MongoDB with id: {insert_result.inserted_id}")
        except AttributeError as e_mongo_attr:
            app.logger.error(f"MongoDB client not available (AttributeError): {e_mongo_attr}", exc_info=True)
            app.logger.error(f"Data for {original_identifier} was NOT saved to MongoDB.")
        except Exception as e_mongo_save:
            app.logger.error(f"Error saving data to MongoDB for {original_identifier}: {e_mongo_save}", exc_info=True)

        frontend_response_data = {
            "filename": original_identifier,
            "metrics": {k: v for k, v in metrics_data.items() if k not in ["track_points", "start_lat", "start_lon"]},
            "difficulty_score": round(total_difficulty, 2)
        }
        return frontend_response_data, 200

    except Exception as e:
        app.logger.error(f"An error occurred processing data from {original_identifier}: {e}")
        app.logger.error(traceback.format_exc())
        return {"error": "An internal server error occurred while processing the data."}, 500

# --- Flask Routes ---
@app.route('/')
def serve_index():
    # Fetch the 8 most recently added routes
    latest_routes = list(mongo.db.routes.find().sort("processed_at", -1).limit(8))

    # Fetch the 8 most liked routes
    top_routes = list(mongo.db.routes.find().sort("likes_count", -1).limit(8))

    return render_template(
        'index.html', 
        latest_routes=latest_routes, 
        top_routes=top_routes
    )

@app.route('/process_route_file', methods=['POST'])
def process_route_file_endpoint():
    if 'gpx_file' not in request.files:
        return jsonify({"error": "No file part in the request. Expected 'gpx_file'."}), 400
    file = request.files['gpx_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        temp_unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_unique_filename)
        try:
            file.save(temp_filepath)
            app.logger.info(f"File '{original_filename}' saved temporarily to '{temp_filepath}'")
            response_dict, status_code = process_route_data(
                filepath=temp_filepath,
                file_extension=file_extension,
                original_identifier=original_filename,
                is_upload=True,
                temp_upload_path=temp_filepath
            )
            return jsonify(response_dict), status_code
        except Exception as e:
            app.logger.error(f"Error processing uploaded file {original_filename}: {e}", exc_info=True)
            return jsonify({"error": "Error processing uploaded file."}), 500
        finally:
            if os.path.exists(temp_filepath):
                try: os.remove(temp_filepath)
                except Exception as e_remove: app.logger.error(f"Error removing temp file: {e_remove}", exc_info=True)
    else:
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

@app.route('/process_route_url', methods=['POST'])
def process_route_url_endpoint():
    if not request.is_json:
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415
    data = request.get_json()
    route_url = data.get('route_url')
    if not route_url:
        return jsonify({"error": "Missing 'route_url' in JSON payload"}), 400
    app.logger.info(f"Received request to process URL: {route_url}")
    temp_filepath = None
    try:
        file_extension = get_file_extension_from_url(route_url)
        if not file_extension or file_extension not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"URL must end with valid extension ({', '.join(ALLOWED_EXTENSIONS)})"}), 400
        headers = {'User-Agent': 'RouteDifficultyScorer/1.0'}
        response = requests.get(route_url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()
        parsed_url = urlparse(route_url)
        original_url_filename = os.path.basename(parsed_url.path)
        if original_url_filename and allowed_file(original_url_filename):
             safe_url_filename = secure_filename(original_url_filename)
             temp_filename = f"url_{safe_url_filename}_{uuid.uuid4().hex[:8]}.{file_extension}"
        else: temp_filename = f"url_download_{uuid.uuid4().hex}.{file_extension}"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        app.logger.info(f"File from URL '{route_url}' saved temporarily to '{temp_filepath}'")
        response_dict, status_code = process_route_data(
            filepath=temp_filepath, file_extension=file_extension, original_identifier=route_url
        )
        return jsonify(response_dict), status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error downloading file from URL {route_url}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to download or access URL: {e}"}), 400
    except Exception as e:
        app.logger.error(f"An error occurred processing URL {route_url}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while processing the URL."}), 500
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            try: os.remove(temp_filepath)
            except Exception as e_remove: app.logger.error(f"Error removing temp URL file: {e_remove}", exc_info=True)


@app.route('/api/list_saved_routes', methods=['GET'])
def list_saved_routes():
    try:
        routes_collection = mongo.db.routes
        all_routes_cursor = routes_collection.find({})
        routes_list = []
        for route_doc in all_routes_cursor:
            if '_id' in route_doc and isinstance(route_doc['_id'], ObjectId):
                route_doc['_id'] = str(route_doc['_id'])
            if 'processed_at' in route_doc and isinstance(route_doc['processed_at'], datetime.datetime):
                route_doc['processed_at'] = route_doc['processed_at'].isoformat()
            if 'comments' not in route_doc: route_doc['comments'] = []
            elif isinstance(route_doc['comments'], list):
                 for comment in route_doc['comments']:
                    if 'timestamp' in comment:
                        if isinstance(comment['timestamp'], datetime.datetime): comment['timestamp'] = comment['timestamp'].isoformat()
                        elif isinstance(comment['timestamp'], dict) and "$date" in comment['timestamp']:
                            date_val = comment['timestamp']['$date']
                            if isinstance(date_val, (int, float)): comment['timestamp'] = datetime.datetime.fromtimestamp(date_val / 1000, tz=datetime.timezone.utc).isoformat()
                            elif isinstance(date_val, str): comment['timestamp'] = datetime.datetime.fromisoformat(date_val.replace("Z", "+00:00")).isoformat()
            routes_list.append(route_doc)
        app.logger.info(f"Retrieved and processed {len(routes_list)} routes from MongoDB for listing.")
        return jsonify(routes_list), 200
    except AttributeError:
        app.logger.error("MongoDB client not available (AttributeError) when listing routes.", exc_info=True)
        return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error retrieving routes from MongoDB: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving routes."}), 500

@app.route('/api/routes/<route_id>', methods=['GET'])
def get_single_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_object_id = ObjectId(route_id)
        except errors.InvalidId:
            return jsonify({"error": "Invalid route ID format."}), 400
        route_document = routes_collection.find_one({"_id": route_object_id})
        if route_document:
            if "likes_count" not in route_document: route_document["likes_count"] = 0
            if "comments" not in route_document: route_document["comments"] = []
            elif isinstance(route_document['comments'], list):
                 for comment in route_document['comments']:
                    if 'timestamp' in comment and isinstance(comment['timestamp'], datetime.datetime): comment['timestamp'] = comment['timestamp'].isoformat()
                    elif 'timestamp' in comment and isinstance(comment['timestamp'], dict) and "$date" in comment['timestamp']:
                        date_val = comment['timestamp']['$date']
                        if isinstance(date_val, (int, float)): comment['timestamp'] = datetime.datetime.fromtimestamp(date_val / 1000, tz=datetime.timezone.utc).isoformat()
                        elif isinstance(date_val, str): comment['timestamp'] = datetime.datetime.fromisoformat(date_val.replace("Z", "+00:00")).isoformat()
            return jsonify(route_document), 200
        else:
            return jsonify({"error": "Route not found"}), 404
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error retrieving route {route_id} from MongoDB: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving the route."}), 500

@app.route('/api/routes/<route_id>/access_file', methods=['GET'])
def access_route_file(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_object_id = ObjectId(route_id)
        except errors.InvalidId:
            app.logger.warning(f"Access file: Invalid ObjectId format for route_id: {route_id}")
            return jsonify({"error": "Invalid route ID format."}), 400
        route_document = routes_collection.find_one({"_id": route_object_id})
        if not route_document:
            app.logger.warning(f"Access file: Route with id {route_id} not found.")
            return jsonify({"error": "Route not found"}), 404
        source_type = route_document.get("source_type")
        if source_type == 'upload':
            stored_filename = route_document.get("stored_file_name")
            original_filename_for_download = route_document.get("original_identifier", stored_filename)
            if not stored_filename:
                app.logger.error(f"Access file: Route {route_id} is type 'upload' but has no stored_file_name.")
                return jsonify({"error": "Stored file path not found for this route."}), 500
            directory = os.path.join(os.getcwd(), app.config['PERMANENT_STORAGE_FOLDER'])
            app.logger.info(f"Attempting to send file: {stored_filename} from directory: {directory}. Original name: {original_filename_for_download}")
            if not os.path.exists(os.path.join(directory, stored_filename)):
                app.logger.error(f"Access file: File {stored_filename} not found in {directory} for route {route_id}.")
                return jsonify({"error": "Stored file not found on server."}), 404
            return send_from_directory(
                directory=directory, path=stored_filename, as_attachment=True, download_name=original_filename_for_download
            )
        elif source_type == 'url':
            external_url = route_document.get("original_identifier")
            if not external_url:
                app.logger.error(f"Access file: Route {route_id} is type 'url' but has no original_identifier (URL).")
                return jsonify({"error": "External URL not found for this route."}), 500
            app.logger.info(f"Access file: Redirecting to external URL for route {route_id}: {external_url}")
            return redirect(external_url)
        else:
            app.logger.error(f"Access file: Unknown source_type '{source_type}' for route {route_id}.")
            return jsonify({"error": "Unknown route source type."}), 500
    except AttributeError: return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error accessing file for route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while accessing the route file."}), 500

@app.route('/api/routes/<route_id>/like', methods=['POST'])
def like_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_object_id = ObjectId(route_id)
        except errors.InvalidId:
            app.logger.warning(f"Like route: Invalid ObjectId format for route_id: {route_id}")
            return jsonify({"error": "Invalid route ID format."}), 400
        update_result = routes_collection.update_one(
            {"_id": route_object_id},
            {"$inc": {"likes_count": 1}}
        )
        if update_result.matched_count == 0:
            app.logger.warning(f"Like route: Route with id {route_id} not found for liking.")
            return jsonify({"error": "Route not found"}), 404
        updated_route_document = routes_collection.find_one({"_id": route_object_id})
        new_likes_count = updated_route_document.get("likes_count", 0)
        app.logger.info(f"Route {route_id} liked. New likes_count: {new_likes_count}")
        return jsonify({"message": "Route liked successfully!", "likes_count": new_likes_count}), 200
    except AttributeError:
        app.logger.error(f"MongoDB client not available (AttributeError) when liking route {route_id}.", exc_info=True)
        return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error liking route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while liking the route."}), 500

@app.route('/api/routes/<route_id>/unlike', methods=['POST'])
def unlike_route(route_id):
    try:
        routes_collection = mongo.db.routes
        try: route_object_id = ObjectId(route_id)
        except errors.InvalidId:
            app.logger.warning(f"Unlike route: Invalid ObjectId format for route_id: {route_id}")
            return jsonify({"error": "Invalid route ID format."}), 400
        route_document = routes_collection.find_one({"_id": route_object_id})
        if not route_document:
            app.logger.warning(f"Unlike route: Route with id {route_id} not found.")
            return jsonify({"error": "Route not found"}), 404
        current_likes = route_document.get("likes_count", 0)
        if current_likes > 0:
            update_result = routes_collection.update_one(
                {"_id": route_object_id},
                {"$inc": {"likes_count": -1}}
            )
            if update_result.modified_count == 0:
                 app.logger.warning(f"Unlike route: Route {route_id} found but not modified (likes_count might not have decremented).")
        else:
            app.logger.info(f"Unlike route: Route {route_id} already has 0 likes. No change made.")
        updated_route_document = routes_collection.find_one({"_id": route_object_id})
        new_likes_count = updated_route_document.get("likes_count", 0)
        app.logger.info(f"Route {route_id} unliked (or like count confirmed). New likes_count: {new_likes_count}")
        return jsonify({"message": "Route unlike processed!", "likes_count": new_likes_count}), 200
    except AttributeError:
        app.logger.error(f"MongoDB client not available (AttributeError) when unliking route {route_id}.", exc_info=True)
        return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error unliking route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while unliking the route."}), 500

@app.route('/api/routes/<route_id>/comments', methods=['POST'])
def add_comment_to_route(route_id):
    if not request.is_json:
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415
    data = request.get_json()
    comment_text = data.get('text')
    if not comment_text:
        return jsonify({"error": "Missing 'text' for comment in JSON payload"}), 400
    try:
        routes_collection = mongo.db.routes
        try: route_object_id = ObjectId(route_id)
        except errors.InvalidId:
            app.logger.warning(f"Add comment: Invalid ObjectId format for route_id: {route_id}")
            return jsonify({"error": "Invalid route ID format."}), 400
        new_comment = {
            "_id": ObjectId(),
            "text": comment_text,
            # +++ Update author details +++
            "author_id": ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
            "author_username": current_user.username if current_user.is_authenticated else "Anonymous",
            "timestamp": datetime.datetime.utcnow()
        }
        update_result = routes_collection.update_one(
            {"_id": route_object_id},
            {"$push": {"comments": new_comment}}
        )
        if update_result.matched_count == 0:
            app.logger.warning(f"Add comment: Route with id {route_id} not found.")
            return jsonify({"error": "Route not found"}), 404
        if update_result.modified_count == 0:
            app.logger.warning(f"Add comment: Route {route_id} found but comments not modified.")
        app.logger.info(f"Comment added to route {route_id} by {new_comment['author_username']}")
        response_comment = {
            **new_comment,
            "_id": str(new_comment["_id"]),
            "author_id": str(new_comment["author_id"]) if new_comment["author_id"] else None,
            "timestamp": new_comment["timestamp"].isoformat()
        }
        return jsonify({"message": "Comment added successfully!", "comment": response_comment}), 201
    except AttributeError:
        app.logger.error(f"MongoDB client not available (AttributeError) when adding comment to route {route_id}.", exc_info=True)
        return jsonify({"error": "Database client not available."}), 500
    except Exception as e:
        app.logger.error(f"Error adding comment to route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while adding the comment."}), 500

@app.route('/route/<route_id>')
def route_profile_page(route_id):
    # +++ Pass user's favorite status to the template +++
    is_favorited = False
    if current_user.is_authenticated:
        # We need to fetch the full user document to check the 'favorites' list
        user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.get_id())})
        if user_data and 'favorites' in user_data:
            # Check if the route_id (as an ObjectId) is in the list of favorite ObjectIds
            if any(str(fav_id) == route_id for fav_id in user_data['favorites']):
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
        return redirect('/logout')

    # --- Updated Avatar Logic ---
    # Check for a custom uploaded avatar first
    if 'avatar_filename' in user_data and user_data['avatar_filename']:
        avatar_url = url_for('serve_avatar', filename=user_data['avatar_filename'])
    else:
        # Fallback to Gravatar if no custom avatar is set
        email_hash = hashlib.md5(user_data.get('email', '').lower().encode('utf-8')).hexdigest()
        avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s=150&d=identicon"

    uploaded_routes = list(mongo.db.routes.find({"creator_id": user_id}).sort("processed_at", -1))

    favourited_routes = []
    if 'favorites' in user_data and user_data['favorites']:
        favorite_ids = user_data['favorites']
        favourited_routes = list(mongo.db.routes.find({"_id": {"$in": favorite_ids}}))

    return render_template(
        'profile.html', 
        user=user_data, 
        avatar_url=avatar_url,
        uploaded_routes=uploaded_routes,
        favourited_routes=favourited_routes
    )

# +++ Add Edit Profile and Avatar Serving Routes +++
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = ObjectId(current_user.get_id())
    user_data = mongo.db.users.find_one({"_id": user_id})

    if request.method == 'POST':
        # This block runs when the user submits the form
        location = request.form.get('location')
        bio = request.form.get('bio')
        mongo.db.users.update_one({"_id": user_id}, {"$set": {"location": location, "bio": bio}})

        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_image_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                new_filename = f"{current_user.get_id()}_{uuid.uuid4().hex[:8]}.{ext}"
                
                if 'avatar_filename' in user_data and user_data['avatar_filename']:
                    old_path = os.path.join('avatars_store', user_data['avatar_filename'])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                img = Image.open(file.stream)
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(os.path.join('avatars_store', new_filename))
                mongo.db.users.update_one({"_id": user_id}, {"$set": {"avatar_filename": new_filename}})

        # This redirect should be aligned with the "if 'avatar'..." block,
        # so it runs after all the POST logic is complete.
        return redirect('/profile')

    # This return is for the GET request (when the page first loads).
    # It should be aligned with the "if request.method == 'POST':" block.
    return render_template('edit_profile.html', user=user_data)

@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory('avatars_store', filename)

# +++ Add Route for the new "Add Your Routes" page +++
@app.route('/add-routes')
@login_required
def add_routes_page():
    return render_template('add_routes.html')

# +++ Add Authentication Routes +++
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            # In a real app, you'd provide a more specific message
            return render_template('register.html', error="Username or email already exists.")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        mongo.db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'favorites': [],
            'ridden': []
        })
        # Add a success message (optional)
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = mongo.db.users.find_one({'username': username})

        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user_obj = User(user_data)
            login_user(user_obj, remember=True)
            # Redirect to the page they were trying to access, or home
            next_page = request.args.get('next')
            return redirect(next_page or '/')
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')
# +++ End of Authentication Routes +++

# +++ Add Favourites API Routes +++
@app.route('/api/routes/<route_id>/favorite', methods=['POST'])
@login_required
def favorite_route(route_id):
    try:
        route_object_id = ObjectId(route_id)
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$addToSet': {'favorites': route_object_id}}
        )
        return jsonify({"success": True, "message": "Route added to favorites."}), 200
    except Exception as e:
        app.logger.error(f"Error favoriting route {route_id} for user {current_user.id}: {e}")
        return jsonify({"success": False, "error": "Could not save favorite."}), 500

@app.route('/api/routes/<route_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_route(route_id):
    try:
        route_object_id = ObjectId(route_id)
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$pull': {'favorites': route_object_id}}
        )
        return jsonify({"success": True, "message": "Route removed from favorites."}), 200
    except Exception as e:
        app.logger.error(f"Error unfavoriting route {route_id} for user {current_user.id}: {e}")
        return jsonify({"success": False, "error": "Could not remove favorite."}), 500
# +++ End of Favourites API Routes +++

@app.route('/compare')
def compare_page():
    # Get the comma-separated string of IDs from the URL query parameter
    route_ids_str = request.args.get('ids', '')
    if not route_ids_str:
        return "No routes selected for comparison.", 400

    # Convert the string of IDs into a list of ObjectId objects
    id_strings = route_ids_str.split(',')
    object_ids = []
    for id_str in id_strings:
        try:
            object_ids.append(ObjectId(id_str))
        except errors.InvalidId:
            # Skip any invalid IDs
            app.logger.warning(f"Invalid ObjectId format in compare URL: {id_str}")
            continue

    # Fetch all routes whose _id is in our list of ObjectIds
    # We use $in to match multiple values
    routes = list(mongo.db.routes.find({"_id": {"$in": object_ids}}))

    # Pass the fetched routes to the new compare template
    return render_template('compare.html', routes=routes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)