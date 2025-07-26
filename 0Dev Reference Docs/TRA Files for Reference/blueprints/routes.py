# blueprints/routes.py

import os
import hashlib
import uuid
import datetime
from flask import (Blueprint, render_template, request, redirect, url_for, 
                   g, send_from_directory, jsonify, current_app)
from flask_login import login_required, current_user
from bson import ObjectId, errors
from PIL import Image

# Use a relative import to get the User model from the sibling 'models.py'
from .models import User

# Define the blueprint
routes_bp = Blueprint('routes', __name__)


# --- Helper function moved from app.py ---
# This is used in edit_profile, so it belongs here now.
def allowed_image_file(filename):
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# --- Main Page Rendering Routes ---

@routes_bp.route('/')
def serve_index():
    # This route uses 'g.mongo' which is set up in the main app.py before_request
    try:
        routes_collection = g.mongo.db.routes
        reviews_collection = g.mongo.db.reviews
        users_collection = g.mongo.db.users
        
        raw_latest_routes = list(routes_collection.find().sort("published_at", -1).limit(9))
        raw_top_routes = list(routes_collection.find().sort("likes_count", -1).limit(9))

        trending_pipeline = [
            {"$addFields": {"score": {"$subtract": [{"$size": {"$ifNull": ["$upvotes", []]}}, {"$size": {"$ifNull": ["$downvotes", []]}}]}}},
            {"$sort": {"score": -1, "created_at": -1}},
            {"$limit": 3},
            {"$lookup": {"from": "routes", "localField": "route_id", "foreignField": "_id", "as": "route_details"}},
            {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            {"$unwind": "$route_details"},
            {"$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}}
        ]
        trending_reviews = list(reviews_collection.aggregate(trending_pipeline))

        for review in trending_reviews:
            if review.get("author_details"):
                if 'avatar_filename' in review["author_details"] and review["author_details"]['avatar_filename']:
                    review['author_avatar_url'] = url_for('files.serve_avatar', filename=review["author_details"]['avatar_filename'])
                else:
                    email_hash = hashlib.md5(review["author_details"].get('email', '').lower().encode('utf-8')).hexdigest()
                    review['author_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"
            else:
                review["creator_username"] = "An unknown user"
                review['author_avatar_url'] = url_for('static', filename='images/default_avatar.png')

        def process_route_list_for_index(route_list):
            processed_list = []
            for route in route_list:
                if '_id' in route and isinstance(route['_id'], ObjectId): route['_id'] = str(route['_id'])
                route['creator_avatar_url'] = None
                if 'creator_id' in route and route['creator_id']:
                    try:
                        creator_id_obj = ObjectId(route['creator_id'])
                        creator = users_collection.find_one({"_id": creator_id_obj}) 
                        if creator:
                            if 'avatar_filename' in creator and creator['avatar_filename']:
                                route['creator_avatar_url'] = url_for('files.serve_avatar', filename=creator['avatar_filename'])
                            else:
                                email_hash = hashlib.md5(creator.get('email', '').lower().encode('utf-8')).hexdigest()
                                route['creator_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"
                    except Exception as e_avatar: current_app.logger.error(f"Error fetching avatar for {route.get('creator_id')}: {e_avatar}")
                
                if route.get('static_map_thumbnail_filename'):
                    route['static_map_thumbnail_url'] = url_for('static', filename=f"map_thumbnails/{route['static_map_thumbnail_filename']}")
                elif route.get('actual_thumbnail_url'): 
                    route['static_map_thumbnail_url'] = route['actual_thumbnail_url']
                else:
                    route['static_map_thumbnail_url'] = url_for('static', filename='images/map_placeholder.png')
                processed_list.append(route)
            return processed_list

        latest_routes = process_route_list_for_index(raw_latest_routes)
        top_routes = process_route_list_for_index(raw_top_routes)
        
        return render_template('index.html', 
                               latest_routes=latest_routes, 
                               top_routes=top_routes,
                               trending_reviews=trending_reviews)
    except Exception as e:
        current_app.logger.error(f"Error in serve_index: {e}", exc_info=True)
        return render_template('index.html', latest_routes=[], top_routes=[], trending_reviews=[])

@routes_bp.route('/route/<route_id>')
def route_profile_page(route_id):
    is_favorited = False
    if current_user.is_authenticated:
        user = g.mongo.db.users.find_one({"_id": ObjectId(current_user.get_id())})
        if user and route_id in [str(fav) for fav in user.get('favorites', [])]: 
            is_favorited = True
    return render_template('route_profile.html', route_id=route_id, is_favorited=is_favorited)

@routes_bp.route('/browse')
def browse_routes_page():
    return render_template('browse_routes.html')

@routes_bp.route('/planner')
@login_required # Add this decorator if only logged-in users can create routes
def planner_page():
    """Renders the route planner page."""
    # Note: You must add JAWG_ACCESS_TOKEN to your .env and load it in app.py
    # For now, we are assuming it's loaded into the app's config.
    # If not, you might need to add `app.config['JAWG_ACCESS_TOKEN'] = os.getenv('JAWG_ACCESS_TOKEN')`
    # in your main app.py
    jawg_token = os.getenv("JAWG_ACCESS_TOKEN")
    return render_template('planner.html', jawg_token=jawg_token)

@routes_bp.route('/profile')

@routes_bp.route('/profile')
@login_required
def profile():
    try:
        user_id_obj = ObjectId(current_user.get_id())
        user_data = g.mongo.db.users.find_one({"_id": user_id_obj})
        if not user_data:
            return redirect(url_for('auth.logout'))

        avatar_url = url_for('files.serve_avatar', filename=user_data['avatar_filename']) if 'avatar_filename' in user_data and user_data['avatar_filename'] \
            else f"https://www.gravatar.com/avatar/{hashlib.md5(user_data.get('email','').lower().encode('utf-8')).hexdigest()}?s=150&d=identicon"

        uploaded_routes = list(g.mongo.db.routes.find({"creator_id": user_id_obj}).sort("published_at", -1))
        
        liked_route_ids = user_data.get('favorites', [])
        liked_routes = []
        if liked_route_ids:
            liked_route_object_ids = [ObjectId(rid) for rid in liked_route_ids if ObjectId.is_valid(rid)]
            liked_routes = list(g.mongo.db.routes.find({"_id": {"$in": liked_route_object_ids}}))
        
        user_reviews_pipeline = [
            {"$match": {"user_id": user_id_obj}},
            {"$sort": {"created_at": -1}},
            {"$lookup": {"from": "routes", "localField": "route_id", "foreignField": "_id", "as": "route_details"}},
            {"$unwind": {"path": "$route_details", "preserveNullAndEmptyArrays": True}}
        ]
        user_reviews = list(g.mongo.db.reviews.aggregate(user_reviews_pipeline))

        def process_route_list_for_template(route_list):
            processed_list = []
            for route in route_list:
                creator_id = route.get('creator_id')
                if creator_id and ObjectId.is_valid(str(creator_id)):
                    creator_info = g.mongo.db.users.find_one({"_id": ObjectId(creator_id)})
                    if creator_info:
                        if 'avatar_filename' in creator_info and creator_info['avatar_filename']:
                            route['creator_avatar_url'] = url_for('files.serve_avatar', filename=creator_info['avatar_filename'])
                        else:
                            email_hash = hashlib.md5(creator_info.get('email', '').lower().encode('utf-8')).hexdigest()
                            route['creator_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=30&d=identicon"
                
                # Check for the real thumbnail URL first, then fall back to the placeholder.
                if route.get('static_map_thumbnail_filename'):
                    route['static_map_thumbnail_url'] = url_for('static', filename=f"map_thumbnails/{route['static_map_thumbnail_filename']}")
                elif route.get('actual_thumbnail_url'):
                    route['static_map_thumbnail_url'] = route['actual_thumbnail_url']
                else:
                    route['static_map_thumbnail_url'] = url_for('static', filename='images/map_placeholder.png')

                processed_list.append(route)
            return processed_list

        # --- THIS IS THE CORRECTED LOGIC ---
        # Ensure BOTH lists are processed by the helper function.
        final_uploaded_routes = process_route_list_for_template(uploaded_routes)
        final_liked_routes = process_route_list_for_template(liked_routes)
        
        return render_template('profile.html', 
                               user=user_data, 
                               avatar_url=avatar_url,
                               uploaded_routes=final_uploaded_routes, 
                               liked_routes=final_liked_routes,
                               user_reviews=user_reviews)
    except Exception as e:
        current_app.logger.error(f"Error loading profile page: {e}", exc_info=True)
        return render_template('profile.html', user=current_user, avatar_url="", uploaded_routes=[], liked_routes=[], user_reviews=[])

@routes_bp.route('/publish/<draft_id>', methods=['GET', 'POST'])
@login_required
def publish_page(draft_id):
    try:
        draft_obj_id = ObjectId(draft_id)
    except errors.InvalidId:
        current_app.logger.error(f"Publish page accessed with invalid draft_id: {draft_id}")
        return "Error: Invalid draft ID.", 400

    if request.method == 'POST':
        draft_doc = g.mongo.db.drafts.find_one_and_delete({"_id": draft_obj_id, "creator_id": ObjectId(current_user.get_id())})
        
        if not draft_doc:
            return "Error: Draft not found or you do not have permission to publish it.", 404

        final_route_data = draft_doc
        final_route_data['route_name'] = request.form.get('route_name', draft_doc.get('route_name', 'Unnamed Route'))
        final_route_data['description'] = request.form.get('description', '')
        final_route_data['surface_type'] = request.form.get('surface_type', '')
        tags_string = request.form.get('tags', '')
        final_route_data['tags'] = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        final_route_data['published_at'] = datetime.datetime.now(datetime.UTC)
        final_route_data.pop('_id', None)

        insert_result = g.mongo.db.routes.insert_one(final_route_data)
        
        return redirect(url_for('.route_profile_page', route_id=insert_result.inserted_id))

    draft = g.mongo.db.drafts.find_one({"_id": draft_obj_id, "creator_id": ObjectId(current_user.get_id())})
    if not draft:
        return "Unauthorized: You did not create this draft or it does not exist.", 403

    return render_template('publish_route.html', draft=draft)

@routes_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = ObjectId(current_user.get_id())
    user_data = g.mongo.db.users.find_one({"_id": user_id})

    if request.method == 'POST':
        g.mongo.db.users.update_one({"_id": user_id}, {"$set": {
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
                g.mongo.db.users.update_one({"_id": user_id}, {"$set": {"avatar_filename": new_filename}})
        
        return redirect(url_for('.profile'))
    
    return render_template('edit_profile.html', user=user_data)

@routes_bp.route('/add-routes')
@login_required
def add_routes_page():
    return render_template('add_routes.html')

@routes_bp.route('/compare')
def compare_page():
    ids_str = request.args.get('ids', '')
    if not ids_str:
        return "No routes for comparison.", 400

    obj_ids = [ObjectId(id_str) for id_str in ids_str.split(',') if ObjectId.is_valid(id_str)]
    routes_from_db = list(g.mongo.db.routes.find({"_id": {"$in": obj_ids}}))

    for route in routes_from_db:
        # This logic can be simplified later by calling the API endpoint internally
        pipeline = [
            {"$match": {"route_id": route['_id']}},
            {"$addFields": {"score": {"$subtract": [{"$size": {"$ifNull": ["$upvotes", []]}}, {"$size": {"$ifNull": ["$downvotes", []]}}]}}},
            {"$sort": {"score": -1, "created_at": -1}},
            {"$limit": 1},
            {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "author_details"}},
            {"$unwind": {"path": "$author_details", "preserveNullAndEmptyArrays": True}}
        ]
        top_reviews = list(g.mongo.db.reviews.aggregate(pipeline))
        
        if top_reviews:
            top_review = top_reviews[0]
            if top_review.get("author_details"):
                if 'avatar_filename' in top_review["author_details"] and top_review["author_details"]['avatar_filename']:
                    top_review['author_avatar_url'] = url_for('files.serve_avatar', filename=top_review["author_details"]['avatar_filename'])
                else:
                    email_hash = hashlib.md5(top_review["author_details"].get('email', '').lower().encode('utf-8')).hexdigest()
                    top_review['author_avatar_url'] = f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon"
            route['top_review'] = top_review
        else:
            route['top_review'] = None
    
    return render_template('compare.html', routes=routes_from_db)

