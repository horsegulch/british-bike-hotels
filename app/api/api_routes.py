# app/api/api_routes.py

from flask import jsonify
from . import api
from .. import mongo # Import the mongo instance from the app factory

@api.route('/map-data', methods=['GET'])
def get_map_data():
    """
    Provides all necessary data to initialize the main homepage map.
    This includes all approved hotels.
    """
    try:
        # Access the 'hotels' collection from our MongoDB database
        hotels_collection = mongo.db.hotels

        # Define the fields we want to retrieve to keep the payload small.
        # 1 means include, 0 means exclude.
        projection = {
            "_id": 1,
            "name": 1,
            "location": 1,
            "is_featured": 1
        }

        # Find all hotels that have been approved by an admin
        # and apply the projection.
        approved_hotels = hotels_collection.find(
            {"status": "approved"},
            projection
        )

        # Prepare the list of hotels for the JSON response.
        # We must convert the MongoDB '_id' (which is an ObjectId) to a string.
        hotel_list = [
            {
                "_id": str(hotel['_id']),
                "name": hotel.get('name'),
                "location": hotel.get('location'),
                "is_featured": hotel.get('is_featured', False)
            }
            for hotel in approved_hotels
        ]

        # Return the data in the specified format
        return jsonify({"hotels": hotel_list})

    except Exception as e:
        # If there's any database error, return a 500 server error.
        return jsonify({"error": "Could not connect to the database.", "details": str(e)}), 500

