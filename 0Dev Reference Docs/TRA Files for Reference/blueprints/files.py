# blueprints/files.py

from flask import Blueprint, send_from_directory, current_app

files_bp = Blueprint('files', __name__)

@files_bp.route('/avatars/<filename>')
def serve_avatar(filename):
    # 'avatars_store' is a static directory name, not from config
    return send_from_directory('avatars_store', filename)

@files_bp.route('/reviews/images/<path:filename>')
def uploaded_review_image(filename):
    # This directory IS from the app config
    return send_from_directory(current_app.config['REVIEWS_IMAGES_FOLDER'], filename)