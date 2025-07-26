# celery_worker.py (Corrected Version)

import os
import shutil
import uuid
import datetime
from dotenv import load_dotenv
from app import app, mongo
from celery import Celery
from bson import ObjectId

# Helper function imports
from metric_extractor import get_route_metrics
from difficulty_calculator import calculate_total_difficulty
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError
from staticmap import StaticMap, Line
from flask import url_for

# --- Celery Configuration ---
load_dotenv()

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'], include=['celery_worker'])
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# --- Helper Function (moved from app.py) ---
def get_start_location_name(lat, lon):
    if lat is None or lon is None: return "N/A (No Coords)"
    geolocator = Nominatim(user_agent="route_scorer_app_v1_unique_id/1.0")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10, language='en')
        if location and location.address:
            # ... (Full logic for get_start_location_name as it was in app.py) ...
            return location.address
        return "N/A (Geocode No Result)"
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError, Exception):
        return "N/A (Geocode Error)"

# In celery_worker.py, replace the entire function

@celery.task(name='celery_worker.process_route_task')
def process_route_task(filepath, file_extension, original_identifier, is_upload, temp_upload_path, creator_id, creator_username):
    """
    This background task contains the full logic for processing a route file.
    """
    try:
        metrics_data = get_route_metrics(filepath, file_extension, apply_smoothing=True)
        if not metrics_data: 
            raise ValueError("Failed to extract metrics from route file.")

        # --- Thumbnail Generation ---
        thumbnail_filename = None # Default to None
        if metrics_data.get("track_points"):
            try:
                line_coordinates = [(p['lon'], p['lat']) for p in metrics_data["track_points"]]
                if line_coordinates:
                    # Generate a unique filename for the thumbnail
                    temp_thumb_filename = f"map_{uuid.uuid4().hex[:10]}.png"
                    thumbnail_path = os.path.join(app.config['STATIC_MAP_THUMBNAILS_FOLDER'], temp_thumb_filename)
                    
                    # Create and save the map image
                    m = StaticMap(400, 250, url_template='https://tile.jawg.io/jawg-terrain/{z}/{x}/{y}.png?access-token=YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p')
                    line = Line(line_coordinates, '#f3ba19', 3)
                    m.add_line(line)
                    image = m.render(zoom=None)
                    image.save(thumbnail_path)
                    
                    # If save was successful, set the filename to be stored in the DB
                    thumbnail_filename = temp_thumb_filename
                    app.logger.info(f"Successfully generated thumbnail: {thumbnail_filename}")

            except Exception as e_thumb:
                app.logger.error(f"Error generating thumbnail for {original_identifier}: {e_thumb}", exc_info=True)
        # --- End of Thumbnail Logic ---
        
        start_lat, start_lon = metrics_data.get("start_lat"), metrics_data.get("start_lon")
        start_location_name = get_start_location_name(start_lat, start_lon)
        total_difficulty = calculate_total_difficulty(
            metrics_data['distance_km'], metrics_data['TEGa'], metrics_data['ACg'],
            metrics_data['MCg'], metrics_data['PDD'], metrics_data['ADg']
        )
        
        db_save_data = {
            "original_identifier": original_identifier,
            "route_name": metrics_data.get("route_name", "N/A"),
            "metrics_summary": {k: v for k,v in metrics_data.items() if k not in ["track_points", "start_lat", "start_lon"]},
            "start_location_name": start_location_name,
            "start_coordinates": {"lat": start_lat, "lon": start_lon},
            "track_points": metrics_data.get("track_points", []),
            "difficulty_score": round(total_difficulty, 2),
            "file_type": file_extension,
            "source_type": 'upload' if is_upload else 'url',
            "processed_at": datetime.datetime.now(datetime.UTC),
            "creator_id": ObjectId(creator_id) if creator_id else None,
            "creator_username": creator_username,
            "static_map_thumbnail_filename": thumbnail_filename # Save the FILENAME, not a URL
        }
        
        if is_upload and temp_upload_path:
            permanent_filename = f"{uuid.uuid4().hex}.{file_extension}"
            permanent_path = os.path.join(app.config['PERMANENT_STORAGE_FOLDER'], permanent_filename)
            shutil.copy2(filepath, permanent_path)
            db_save_data["stored_file_name"] = permanent_filename
            
        insert_result = mongo.db.drafts.insert_one(db_save_data)
        
        if temp_upload_path and os.path.exists(temp_upload_path):
            os.remove(temp_upload_path)
        
        return {"status": "success", "draft_id": str(insert_result.inserted_id)}

    except Exception as e:
        app.logger.error(f"CRITICAL Error in Celery task for {original_identifier}: {e}", exc_info=True)
        return {"status": "error", "message": "Internal server error during background processing."}