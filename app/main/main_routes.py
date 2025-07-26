# app/main/main_routes.py

import os
import json
from flask import render_template, abort, current_app
from . import main
from .. import mongo
from ..utils.gpx_utils import parse_gpx_file
from bson.objectid import ObjectId

@main.route('/')
def index():
    """
    Renders the main homepage.
    Passes the Jawg Access Token and latest blog posts to the template.
    """
    jawg_token = os.getenv('JAWG_ACCESS_TOKEN')
    # Fetch the 3 most recent 'published' posts
    latest_posts_cursor = mongo.db.blog_posts.find({'status': 'published'}).sort("created_at", -1).limit(3)
    latest_posts = list(latest_posts_cursor)
    
    # This is the corrected line, now passing the posts to the template
    return render_template('index.html', jawg_token=jawg_token, latest_posts=latest_posts)


@main.route('/hotel/<hotel_id>')
def hotel_profile(hotel_id):
    """
    Renders the profile page for a specific hotel.
    """
    hotel = mongo.db.hotels.find_one_or_404({'_id': hotel_id})
    # Fetch only active routes for this hotel
    routes_cursor = mongo.db.routes.find({'hotel_id': hotel_id, 'status': 'active'})
    routes = list(routes_cursor)
    return render_template('hotel_profile.html', hotel=hotel, routes=routes)


@main.route('/route/<route_id>')
def route_profile(route_id):
    """
    Renders the profile page for a specific cycling route.
    """
    route = mongo.db.routes.find_one_or_404({'_id': route_id})
    
    # We need the hotel's name for a breadcrumb link
    hotel = mongo.db.hotels.find_one({'_id': route['hotel_id']})

    # Read the GPX file to get the track points for the map and chart
    track_points = []
    try:
        # Construct the full path to the GPX file
        gpx_file_path = os.path.join(current_app.static_folder, route['gpx_file_path'])
        with open(gpx_file_path, 'r') as f:
            # We re-parse here to get the detailed points for the chart
            gpx_data = parse_gpx_file(f)
            track_points = gpx_data['track_points']
    except Exception as e:
        print(f"Could not read or parse GPX file for route {route_id}: {e}")

    jawg_token = os.getenv('JAWG_ACCESS_TOKEN')
    
    # Pass track_points as a JSON string to the template
    return render_template('route_profile.html', 
                           route=route, 
                           hotel=hotel, 
                           jawg_token=jawg_token,
                           track_points_json=json.dumps(track_points))
