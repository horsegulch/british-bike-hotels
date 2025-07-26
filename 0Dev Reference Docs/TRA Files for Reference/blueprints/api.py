# blueprints/api.py

import datetime
import hashlib
import os
import requests
import uuid
from flask import (Blueprint, request, jsonify, redirect, url_for, g, current_app)
from flask_login import login_required, current_user
from bson import ObjectId, errors
from difficulty_calculator import calculate_total_difficulty
from common.utils import haversine_distance, get_start_location_name
from metric_extractor import get_route_metrics
from difficulty_calculator import calculate_total_difficulty
from common.utils import get_start_location_name # We need this for the new logic


# Define the blueprint. The 'url_prefix' will add '/api' to every route in this file.
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/list_saved_routes', methods=['GET'])
def list_saved_routes():
    try:
        routes_collection = g.mongo.db.routes
        all_routes_cursor = routes_collection.find({}, {"track_points": 0}) 
        routes_list = []
        for route in all_routes_cursor:
            # The app.json_encoder handles BSON types, but being explicit can prevent issues
            if '_id' in route: route['_id'] = str(route['_id'])
            if 'creator_id' in route and route['creator_id']: route['creator_id'] = str(route['creator_id'])
            routes_list.append(route)
        return jsonify(routes_list)
    except Exception as e:
        current_app.logger.error(f"Error listing routes: {e}", exc_info=True)
        return jsonify({"error": "Error listing routes."}), 500


@api_bp.route('/routes/<route_id>', methods=['GET'])
def get_single_route(route_id):
    try:
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        
        route_document = g.mongo.db.routes.find_one({"_id": route_obj_id})
        
        if not route_document: return jsonify({"error": "Route not found"}), 404

        creator_id = route_document.get('creator_id')
        if creator_id:
            creator = g.mongo.db.users.find_one({"_id": ObjectId(creator_id)})
            if creator:
                if 'avatar_filename' in creator and creator['avatar_filename']:
                    # Use url_for with the function name from app.py
                    route_document['creator_avatar_url'] = url_for('files.serve_avatar', filename=creator['avatar_filename'], _external=True)
                else:
                    email_hash = hashlib.md5(creator.get('email', '').lower().encode('utf-8')).hexdigest()
                    route_document['creator_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"

        return jsonify(route_document) 
    except Exception as e:
        current_app.logger.error(f"Error getting route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error getting route."}), 500


@api_bp.route('/routes/<route_id>/access_file', methods=['GET'])
def access_route_file(route_id):
    try:
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        route_doc = g.mongo.db.routes.find_one({"_id": route_obj_id})
        if not route_doc: return jsonify({"error": "Route not found"}), 404
        # ... this function might need access to 'send_from_directory' from the main app
        # For now, this logic remains, but might require slight adjustment if moved fully
        # This is more advanced and can be revisited.
        return redirect(url_for('.access_route_file', route_id=route_id, _external=True)) # Simpler to redirect for now
    except Exception as e:
        current_app.logger.error(f"Error accessing file for {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error accessing file."}), 500


@api_bp.route('/routes/<route_id>/comments', methods=['POST'])
@login_required
def add_comment_to_route(route_id):
    if not request.is_json: return jsonify({"error": "Request must be JSON."}), 415
    data = request.get_json()
    comment_text = data.get('text')
    if not comment_text: return jsonify({"error": "Missing comment text."}), 400
    try:
        try: route_obj_id = ObjectId(route_id)
        except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
        new_comment = {
            "_id": ObjectId(), "text": comment_text,
            "author_id": ObjectId(current_user.get_id()),
            "author_username": current_user.username,
            "timestamp": datetime.datetime.now(datetime.UTC)
        }
        result = g.mongo.db.routes.update_one({"_id": route_obj_id}, {"$push": {"comments": new_comment}})
        if result.matched_count == 0: return jsonify({"error": "Route not found"}), 404
        return jsonify({"message": "Comment added.", "comment": new_comment}), 201
    except Exception as e:
        current_app.logger.error(f"Error adding comment to {route_id}: {e}", exc_info=True)
        return jsonify({"error": "Error adding comment."}), 500


@api_bp.route('/routes/<route_id>/reviews', methods=['POST'])
@login_required
def submit_review(route_id):
    from ..app import allowed_image_file # Example of importing a helper if needed
    try:
        review_document = {
            "route_id": ObjectId(route_id), 
            "user_id": ObjectId(current_user.get_id()),
            "creator_username": current_user.username, 
            "created_at": datetime.datetime.now(datetime.UTC),
            "ride_report": request.form.get('ride_report', ''), "image_ids": [],
            "ratings": {
                "scenery": int(request.form.get('rating_scenery')) if request.form.get('rating_scenery') else None,
                "traffic": int(request.form.get('rating_traffic')) if request.form.get('rating_traffic') else None,
                "pit_stops": int(request.form.get('rating_pit_stops')) if request.form.get('rating_pit_stops') else None,
                "points_of_interest": int(request.form.get('rating_interest_points')) if request.form.get('rating_interest_points') else None,
                "perceived_difficulty": int(request.form.get('rating_perceived_difficulty')) if request.form.get('rating_perceived_difficulty') else None
            },
            "upvotes": [], "downvotes": [],
        }
        review_insert_result = g.mongo.db.reviews.insert_one(review_document)
        new_review_id = review_insert_result.inserted_id

        uploaded_image_ids = []
        if 'ride_images' in request.files:
            files = request.files.getlist('ride_images')
            for file in files:
                if file and allowed_image_file(file.filename):
                    # Save logic would go here
                    pass
        if uploaded_image_ids:
            g.mongo.db.reviews.update_one({"_id": new_review_id}, {"$set": {"image_ids": uploaded_image_ids}})
        return jsonify({"success": True, "message": "Review submitted successfully!"}), 201
    except Exception as e:
        current_app.logger.error(f"Error submitting review: {e}", exc_info=True)
        return jsonify({"success": False, "error": "An internal error occurred."}), 500


@api_bp.route('/routes/<route_id>/reviews', methods=['GET'])
def get_reviews_for_route(route_id):
    sort_by = request.args.get('sort', 'latest')
    try:
        pipeline = [{"$match": {"route_id": ObjectId(route_id)}}]
        if sort_by == 'top':
            pipeline.append({"$addFields": {"score": {"$subtract": [{"$size": {"$ifNull": ["$upvotes", []]}}, {"$size": {"$ifNull": ["$downvotes", []]}}]}}})
            pipeline.append({"$sort": {"score": -1, "created_at": -1}})
        else:
            pipeline.append({"$sort": {"created_at": -1}})
        pipeline.append({"$lookup": {"from": "images", "localField": "_id", "foreignField": "review_id", "as": "images_data"}})
        pipeline.extend([
            {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            {"$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}}
        ])
        reviews = list(g.mongo.db.reviews.aggregate(pipeline))
        for review in reviews:
            if review.get("author_details"):
                email = review.get("author_details", {}).get("email", "")
                review["author_details"]["gravatar_hash"] = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        return jsonify(reviews)
    except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching reviews: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500


@api_bp.route('/routes/<route_id>/images', methods=['GET'])
def get_images_for_route(route_id):
    try:
        images = list(g.mongo.db.images.find({"route_id": ObjectId(route_id)}, {"filename": 1, "_id": 1}).sort("uploaded_at", -1))
        return jsonify(images)
    except errors.InvalidId: return jsonify({"error": "Invalid route ID format."}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching images for route {route_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500


@api_bp.route('/reviews/<review_id>/vote', methods=['POST'])
@login_required
def vote_on_review(review_id):
    data = request.get_json()
    direction = data.get('direction')
    if direction not in ['up', 'down']: return jsonify({"error": "Invalid vote direction."}), 400
    try:
        review_obj_id, user_obj_id = ObjectId(review_id), ObjectId(current_user.get_id())
    except errors.InvalidId: return jsonify({"error": "Invalid ID format."}), 400
    add_to_field, pull_from_field = ('upvotes', 'downvotes') if direction == 'up' else ('downvotes', 'upvotes')
    update_result = g.mongo.db.reviews.update_one({"_id": review_obj_id}, {"$addToSet": {add_to_field: user_obj_id}, "$pull": {pull_from_field: user_obj_id}})
    if update_result.matched_count == 0: return jsonify({"error": "Review not found."}), 404
    updated_review = g.mongo.db.reviews.find_one({"_id": review_obj_id}, {"upvotes": 1, "downvotes": 1})
    upvote_count = len(updated_review.get('upvotes', []))
    downvote_count = len(updated_review.get('downvotes', []))
    return jsonify({"success": True, "upvotes": upvote_count, "downvotes": downvote_count, "new_score": upvote_count - downvote_count}), 200


@api_bp.route('/images/<image_id>/vote', methods=['POST'])
@login_required
def vote_on_image(image_id):
    data = request.get_json()
    direction = data.get('direction')
    if direction not in ['up', 'down']: return jsonify({"error": "Invalid vote direction."}), 400
    try:
        image_obj_id, user_obj_id = ObjectId(image_id), ObjectId(current_user.get_id())
    except errors.InvalidId: return jsonify({"error": "Invalid ID format."}), 400
    add_to_field, pull_from_field = ('upvotes', 'downvotes') if direction == 'up' else ('downvotes', 'upvotes')
    g.mongo.db.images.update_one({"_id": image_obj_id}, {"$addToSet": {add_to_field: user_obj_id}, "$pull": {pull_from_field: user_obj_id}})
    updated_image = g.mongo.db.images.find_one({"_id": image_obj_id}, {"upvotes": 1, "downvotes": 1})
    upvote_count = len(updated_image.get('upvotes', []))
    downvote_count = len(updated_image.get('downvotes', []))
    return jsonify({"success": True, "new_score": upvote_count - downvote_count}), 200


@api_bp.route('/trending_images', methods=['GET'])
def get_trending_images():
    try:
        thirty_days_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)
        pipeline = [
            {"$match": {"uploaded_at": {"$gte": thirty_days_ago}}},
            {"$addFields": {"score": {"$subtract": [{"$size": {"$ifNull": ["$upvotes", []]}}, {"$size": {"$ifNull": ["$downvotes", []]}}]}}},
            {"$sort": {"score": -1, "uploaded_at": -1}},
            {"$limit": 6},
            {"$lookup": {"from": "routes", "localField": "route_id", "foreignField": "_id", "as": "route_details"}},
            {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "uploader_details"}},
            {"$unwind": {"path": "$route_details", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$uploader_details", "preserveNullAndEmptyArrays": True}}
        ]
        trending_images = list(g.mongo.db.images.aggregate(pipeline))
        for image in trending_images:
            if image.get("uploader_details"):
                if image["uploader_details"].get('avatar_filename'):
                    image['uploader_avatar_url'] = url_for('files.serve_avatar', filename=image["uploader_details"]['avatar_filename'])
                else:
                    email_hash = hashlib.md5(image["uploader_details"].get('email', '').lower().encode('utf-8')).hexdigest()
                    image['uploader_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=30&d=identicon"
        return jsonify(trending_images)
    except Exception as e:
        current_app.logger.error(f"Error fetching trending images: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500


@api_bp.route('/routes/<route_id>/favorite', methods=['POST'])
@login_required
def favorite_route(route_id):
    try:
        g.mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$addToSet': {'favorites': ObjectId(route_id)}})
        return jsonify({"success": True}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500


@api_bp.route('/routes/<route_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_route(route_id):
    try:
        g.mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$pull': {'favorites': ObjectId(route_id)}})
        return jsonify({"success": True}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500


@api_bp.route('/compare_data')
def compare_data_api():
    route_ids_str = request.args.get('ids', '')
    if not route_ids_str: return jsonify({"error": "No route IDs provided"}), 400
    id_strings = route_ids_str.split(',')
    object_ids = [ObjectId(id_str) for id_str in id_strings if ObjectId.is_valid(id_str)]
    if not object_ids: return jsonify({"error": "No valid route IDs provided"}), 400
    routes_from_db = list(g.mongo.db.routes.find({"_id": {"$in": object_ids}}))
    return jsonify(routes_from_db)


@api_bp.route('/get_top_reviews')
def get_top_reviews_api():
    route_ids_str = request.args.get('ids', '')
    if not route_ids_str: return jsonify({"error": "No route IDs provided"}), 400
    id_strings = route_ids_str.split(',')
    top_reviews_map = {}
    for id_str in id_strings:
        if not ObjectId.is_valid(id_str): continue
        route_id_obj = ObjectId(id_str)
        pipeline = [
            {"$match": {"route_id": route_id_obj}},
            {"$addFields": {"score": {"$subtract": [{"$size": {"$ifNull": ["$upvotes", []]}}, {"$size": {"$ifNull": ["$downvotes", []]}}]}}},
            {"$sort": {"score": -1, "created_at": -1}},
            {"$limit": 1},
            {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            {"$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}}
        ]
        top_review_list = list(g.mongo.db.reviews.aggregate(pipeline))
        if top_review_list:
            top_review = top_review_list[0]
            if top_review.get("author_details"):
                if top_review["author_details"].get('avatar_filename'):
                    top_review['author_avatar_url'] = url_for('files.serve_avatar', filename=top_review["author_details"]['avatar_filename'])
                else:
                    email_hash = hashlib.md5(top_review["author_details"].get('email', '').lower().encode('utf-8')).hexdigest()
                    top_review['author_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"
            top_reviews_map[id_str] = top_review
    return jsonify(top_reviews_map)


# Replace your existing save_planned_route function with this one
@api_bp.route('/planner/save', methods=['POST'])
@login_required
def save_planned_route():
    """
    Receives GPX data, processes it immediately, saves it as a draft,
    and returns the new draft's ID.
    """
    if 'gpx_data' not in request.form:
        return jsonify({"success": False, "error": "Missing GPX data."}), 400

    gpx_string = request.form['gpx_data']
    title = request.form.get('title', 'Planned Route')
    temp_filepath = None # Initialize variable

    try:
        # 1. Save the GPX string to a temporary file for processing
        temp_filename = f"{uuid.uuid4().hex}.gpx"
        temp_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(gpx_string)

        # 2. Process the file immediately (no Celery)
        metrics_data = get_route_metrics(temp_filepath, 'gpx', apply_smoothing=True)
        if not metrics_data:
            raise ValueError("Failed to extract metrics from generated GPX.")

        start_lat, start_lon = metrics_data.get("start_lat"), metrics_data.get("start_lon")
        start_location_name = get_start_location_name(start_lat, start_lon)
        
        total_difficulty = calculate_total_difficulty(
            metrics_data['distance_km'], metrics_data['TEGa'], metrics_data['ACg'],
            metrics_data['MCg'], metrics_data['PDD'], metrics_data['ADg']
        )
        
        # 3. Prepare the document for the 'drafts' collection
        db_save_data = {
            "original_identifier": title,
            "route_name": metrics_data.get("route_name", title),
            "description": request.form.get('description', ''), # Get description from form
            "metrics_summary": {k: v for k,v in metrics_data.items() if k not in ["track_points", "start_lat", "start_lon"]},
            "start_location_name": start_location_name,
            "start_coordinates": {"lat": start_lat, "lon": start_lon},
            "track_points": metrics_data.get("track_points", []),
            "difficulty_score": round(total_difficulty, 2),
            "file_type": "gpx", # It's now a GPX file
            "source_type": 'planner',
            "created_at": datetime.datetime.now(datetime.UTC),
            "creator_id": ObjectId(current_user.get_id()),
            "creator_username": current_user.username
        }
        
        # 4. Save to the drafts collection
        insert_result = g.mongo.db.drafts.insert_one(db_save_data)
        new_draft_id = str(insert_result.inserted_id)
        
        # 5. Return the success response WITH the new draft_id
        return jsonify({"success": True, "draft_id": new_draft_id}), 201

    except Exception as e:
        current_app.logger.error(f"Error in synchronous planner save: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Could not process route."}), 500
    finally:
        # 6. Clean up the temporary file
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)

# In blueprints/api.py

# Add this entire function to the end of the file
@api_bp.route('/elevation', methods=['POST'])
@login_required
def elevation_proxy():
    """
    Receives coordinates, splits them into batches to avoid URL length limits,
    calls the Jawg API with multiple small GET requests, and returns the combined result.
    """
    data = request.get_json()
    if not data or 'locations' not in data:
        return jsonify({"error": "Missing 'locations' in request body"}), 400

    locations_list = data['locations'].split('|')
    access_token = os.getenv("JAWG_ACCESS_TOKEN")

    if not access_token:
        current_app.logger.error("JAWG_ACCESS_TOKEN not configured on the server.")
        return jsonify({"error": "API token not configured on server"}), 500

    chunk_size = 150
    all_elevation_data = []

    try:
        for i in range(0, len(locations_list), chunk_size):
            chunk = locations_list[i:i + chunk_size]
            chunk_string = '|'.join(chunk)
            
            # Use the correct 'locations' endpoint with GET
            jawg_url = f"https://api.jawg.io/elevations?locations={chunk_string}&access-token={access_token}"
            
            response = requests.get(jawg_url)
            response.raise_for_status()
            all_elevation_data.extend(response.json())
        
        return jsonify(all_elevation_data)

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch data from Jawg API during batching: {e}")
        return jsonify({"error": "Failed to fetch data from elevation provider."}), 502