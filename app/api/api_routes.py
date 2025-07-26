# app/api/api_routes.py

from flask import jsonify, request, abort, current_app
from . import api
from .. import mongo

@api.route('/map-data')
def get_map_data():
    """
    Retrieves initial data for the main homepage map.
    Fetches all approved hotels.
    """
    try:
        hotels_cursor = mongo.db.hotels.find({'status': 'approved'})
        hotels_list = []
        for hotel in hotels_cursor:
            hotel['_id'] = str(hotel['_id'])
            hotels_list.append(hotel)
        return jsonify({'hotels': hotels_list})
    except Exception as e:
        print(f"Error fetching map data: {e}")
        return jsonify({'error': 'Could not fetch map data'}), 500

@api.route('/hotels-in-view')
def get_hotels_in_view():
    """
    Retrieves hotels that are within the current visible map area.
    Expects north, south, east, and west query parameters.
    """
    try:
        north = float(request.args.get('north'))
        south = float(request.args.get('south'))
        east = float(request.args.get('east'))
        west = float(request.args.get('west'))
    except (TypeError, ValueError):
        return abort(400, description="Invalid or missing bounding box coordinates.")

    bounding_box = [[west, south], [east, north]]

    try:
        query = {
            'location': { '$geoWithin': { '$box': bounding_box } },
            'status': 'approved'
        }
        # Define which fields to return
        projection = {
            'name': 1,
            'location': 1,
            'is_featured': 1,
            'price_range': 1,
            'accommodation_type': 1,
            'facilities': 1
        }
        hotels_cursor = mongo.db.hotels.find(query, projection)
        
        hotels_list = []
        for hotel in hotels_cursor:
            hotel['_id'] = str(hotel['_id'])
            # Get the count of active routes for this hotel
            hotel['route_count'] = mongo.db.routes.count_documents({
                'hotel_id': hotel['_id'],
                'status': 'active'
            })
            hotels_list.append(hotel)
            
        return jsonify({'hotels': hotels_list})
    except Exception as e:
        print(f"Error fetching hotels in view: {e}")
        return jsonify({'error': 'Could not fetch hotels in view'}), 500
