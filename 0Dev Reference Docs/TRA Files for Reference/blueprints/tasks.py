# blueprints/tasks.py

import os
import uuid
import requests
import shutil
import re # <-- Import the regular expression module
from flask import (Blueprint, request, jsonify, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from common.utils import allowed_file, get_file_extension_from_url, transform_to_download_url

# Define the blueprint
tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/process_route_file', methods=['POST'])
@login_required
def process_route_file_endpoint():
    # Use an absolute import from the project root.
    from celery_worker import process_route_task

    if 'gpx_file' not in request.files:
        return jsonify({"error": "No file part."}), 400
    file = request.files['gpx_file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or no file selected."}), 400

    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower()
    
    temp_name = f"{uuid.uuid4().hex}_{original_filename}"
    temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_name)
    file.save(temp_path)

    task = process_route_task.delay(
        filepath=temp_path,
        file_extension=file_ext,
        original_identifier=original_filename,
        is_upload=True,
        temp_upload_path=temp_path,
        creator_id=str(current_user.get_id()),
        creator_username=current_user.username
    )

    return jsonify({"task_id": task.id}), 202


@tasks_bp.route('/process_route_url', methods=['POST'])
def process_route_url_endpoint():
    # Use an absolute import.
    from celery_worker import process_route_task

    if not request.is_json: return jsonify({"error": "Request must be JSON."}), 415
    data = request.get_json()
    route_url = data.get('route_url')
    if not route_url: return jsonify({"error": "Missing 'route_url'."}), 400
    
    temp_filepath = None
    try:

        download_url = transform_to_download_url(route_url)

        if download_url == "strava_manual_download":
            return jsonify({"error": "Strava links are not supported for automatic import. Please download the GPX file from Strava and use the 'Upload File' tab."}), 400

        # Use the (potentially modified) download_url from now on
        file_ext = get_file_extension_from_url(download_url)
        if not file_ext or not allowed_file(f"file.{file_ext}"):
            return jsonify({"error": "Invalid URL or file type."}), 400
            
        headers = {'User-Agent': 'RouteDifficultyScorer/1.0'}
        url_res = requests.get(download_url, stream=True, timeout=30, headers=headers)
        url_res.raise_for_status()
        
        base_name = os.path.basename(urlparse(download_url).path)
        safe_base = secure_filename(base_name) if base_name and allowed_file(base_name) else f"url_dl_{uuid.uuid4().hex[:4]}"
        temp_filename = f"{safe_base}.{file_ext}"
        temp_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        
        with open(temp_filepath, 'wb') as f:
            shutil.copyfileobj(url_res.raw, f)

        task = process_route_task.delay(
            filepath=temp_filepath,
            file_extension=file_ext,
            original_identifier=route_url, # Keep the original URL for the database
            is_upload=False,
            temp_upload_path=temp_filepath,
            creator_id=str(current_user.get_id()) if current_user.is_authenticated else None,
            creator_username=current_user.username if current_user.is_authenticated else "Anonymous"
        )
        
        return jsonify({"task_id": task.id}), 202

    except requests.exceptions.RequestException as e_req:
        if temp_filepath and os.path.exists(temp_filepath): os.remove(temp_filepath)
        return jsonify({"error": f"URL fetch error: {e_req}"}), 400
    except Exception as e:
        if temp_filepath and os.path.exists(temp_filepath): os.remove(temp_filepath)
        current_app.logger.error(f"Error processing route URL: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500


@tasks_bp.route('/task_status/<task_id>')
def task_status(task_id):
    # Use an absolute import.
    from celery_worker import celery

    task = celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    else: # Covers 'FAILURE', 'REVOKED', etc.
        response = {'state': task.state, 'status': str(task.info)}
        
    return jsonify(response)
