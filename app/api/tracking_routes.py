# app/api/tracking_routes.py

from flask import request, jsonify, current_app
from . import api
from app import mongo
import datetime

@api.route('/tracking/event', methods=['POST'])
def track_event():
    """
    A fire-and-forget endpoint for tracking user interactions for analytics.
    
    This endpoint receives an event from the frontend (e.g., a hotel profile view),
    adds a timestamp, and inserts it into the `analytics_events` collection
    in the database.
    
    It's designed to respond quickly with a 204 No Content status to not hold
    up the client.
    """
    data = request.get_json()
    if not data or 'event_type' not in data or 'hotel_id' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    try:
        event = {
            "event_type": data.get("event_type"),
            "hotel_id": data.get("hotel_id"),
            "session_id": data.get("session_id"), # Optional: for session tracking
            "timestamp": datetime.datetime.utcnow()
        }
        mongo.db.analytics_events.insert_one(event)
        
        # Return 204 No Content for a successful fire-and-forget operation
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Error tracking event: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500
