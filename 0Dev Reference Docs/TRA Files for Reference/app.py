# app.py

import os
from dotenv import load_dotenv
from flask import Flask, g

# --- Import from our new extensions file ---
from extensions import bcrypt, login_manager, mongo, limiter

# --- Import our custom modules ---
try:
    from metric_extractor import get_route_metrics
    from difficulty_calculator import calculate_total_difficulty
except ImportError as e:
    print(f"Error importing modules: {e}. Make sure they are accessible.")
    raise

# --- Path Constants ---
UPLOAD_FOLDER = 'uploads'
PERMANENT_STORAGE_FOLDER = 'route_files_store'
STATIC_MAP_THUMBNAILS_FOLDER = os.path.join('static', 'map_thumbnails')
REVIEWS_IMAGES_FOLDER = 'reviews_images_store'

# --- Flask App Initialization & Configuration ---
load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_STORAGE_FOLDER'] = PERMANENT_STORAGE_FOLDER
app.config['STATIC_MAP_THUMBNAILS_FOLDER'] = STATIC_MAP_THUMBNAILS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['REVIEWS_IMAGES_FOLDER'] = REVIEWS_IMAGES_FOLDER
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# --- Initialize Flask Extensions with the App ---
bcrypt.init_app(app)
login_manager.init_app(app)
mongo.init_app(app)
limiter.init_app(app)

# --- User Loader ---
from blueprints.models import User
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- Create Static Directories if they don't exist ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# ... (add other os.makedirs checks here if needed)

# --- Request Setup ---
@app.before_request
def before_request():
    # Note: We now import mongo from extensions, not the global scope of this file
    from extensions import mongo, bcrypt
    g.mongo = mongo
    g.bcrypt = bcrypt

# --- Import and Register Blueprints ---
# Imports are now here, after app and extensions are configured
from blueprints.auth import auth_bp
from blueprints.routes import routes_bp
from blueprints.api import api_bp
from blueprints.tasks import tasks_bp
from blueprints.files import files_bp

app.register_blueprint(auth_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(api_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(files_bp)

# --- Main Execution ---
if __name__ == '__main__':
    app.logger.info("Starting Flask application.")
    app.run(debug=True, host='0.0.0.0', port=5000)