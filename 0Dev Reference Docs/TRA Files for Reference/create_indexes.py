import os
from dotenv import load_dotenv
from flask import Flask
from flask_pymongo import PyMongo
import pymongo # Import for accessing constants like DESCENDING

# --- DATABASE CONNECTION SETUP ---
# This setup is necessary to connect to your database via your .env file
print("--- Starting Index Creation Script ---")
load_dotenv()
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

try:
    mongo = PyMongo(app)
    db = mongo.db # This is the database object we'll use
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# --- INDEX CREATION FOR 'routes' COLLECTION ---
try:
    print("\n---> Creating indexes for 'routes' collection...")
    # As per the roadmap, for filtering on the browse page
    db.routes.create_index([("surface_type", pymongo.ASCENDING)], name="surface_type_asc")
    db.routes.create_index([("tags", pymongo.ASCENDING)], name="tags_asc")
    print("     - Created indexes for 'surface_type' and 'tags'.")

    # For sorting the homepage sections
    db.routes.create_index([("published_at", pymongo.DESCENDING)], name="published_at_desc")
    db.routes.create_index([("likes_count", pymongo.DESCENDING)], name="likes_count_desc")
    print("     - Created indexes for 'published_at' and 'likes_count'.")

    # For the future 'find routes near me' feature from Phase 4
    db.routes.create_index([("start_coordinates", pymongo.GEOSPHERE)], name="start_coordinates_geosphere")
    print("     - Created geospatial index for 'start_coordinates'.")
    
    print("--- 'routes' collection indexing complete. ---")
except Exception as e:
    print(f"An error occurred with 'routes' collection: {e}")


# --- INDEX CREATION FOR 'reviews' COLLECTION ---
try:
    print("\n---> Creating indexes for 'reviews' collection...")
    # To quickly find all reviews for a specific route
    db.reviews.create_index([("route_id", pymongo.ASCENDING)], name="route_id_asc")
    print("     - Created index for 'route_id'.")

    # To sort reviews by 'Latest'
    db.reviews.create_index([("created_at", pymongo.DESCENDING)], name="created_at_desc")
    print("     - Created index for 'created_at'.")
    
    # A compound index to efficiently sort by 'Top' reviews
    db.reviews.create_index(
        [("score", pymongo.DESCENDING), ("created_at", pymongo.DESCENDING)],
        name="score_created_at_desc"
    )
    print("     - Created compound index for 'score' and 'created_at'.")

    print("--- 'reviews' collection indexing complete. ---")
except Exception as e:
    print(f"An error occurred with 'reviews' collection: {e}")

print("\n--- Index Creation Script Finished ---")