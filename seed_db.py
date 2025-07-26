import os
from pymongo import MongoClient, GEOSPHERE
from dotenv import load_dotenv

# It's good practice to load environment variables at the start
load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI environment variable not set!")

# --- Sample Data (Brighton & Hove Area) ---
HOTELS = [
    {
        "_id": "H01",
        "name": "The Grand Brighton",
        "description": "Iconic Victorian hotel on the Brighton seafront, offering luxurious accommodation and secure bike storage.",
        "location": {"type": "Point", "coordinates": [-0.1446, 50.8225]}, # Lon, Lat
        "facilities": ["secure_storage", "bike_wash", "workshop_tools", "drying_room"],
        "website": "[https://www.grandbrighton.co.uk/](https://www.grandbrighton.co.uk/)",
        "phone": "01273 224300",
        "is_featured": True,
        "status": "approved",
    },
    {
        "_id": "H02",
        "name": "Artist Residence Brighton",
        "description": "A quirky, art-filled boutique hotel in Regency Square with a view of the sea.",
        "location": {"type": "Point", "coordinates": [-0.1478, 50.8214]},
        "facilities": ["secure_storage"],
        "website": "[https://www.artistresidence.co.uk/brighton/](https://www.artistresidence.co.uk/brighton/)",
        "phone": "01273 324302",
        "is_featured": False,
        "status": "approved",
    },
    {
        "_id": "H03",
        "name": "YHA Brighton",
        "description": "Modern, budget-friendly accommodation perfect for cycling groups, located next to a major cycle path.",
        "location": {"type": "Point", "coordinates": [-0.1505, 50.8285]},
        "facilities": ["secure_storage", "bike_wash", "self_catering"],
        "website": "[https://www.yha.org.uk/hostel/yha-brighton](https://www.yha.org.uk/hostel/yha-brighton)",
        "phone": "0345 371 9108",
        "is_featured": False,
        "status": "pending", # Example of a hotel awaiting admin approval
    }
]

ROUTES = [
    {
        "_id": "R01",
        "hotel_id": "H01",
        "name": "Classic Seafront Cruise",
        "description": "A flat and easy ride along Brighton's famous seafront path, heading west towards Hove Lagoon.",
        "distance_km": 15.5,
        "elevation_m": 50,
        "surface_type": "Road",
        "tags": ["flat", "family-friendly", "coastal"],
        "gpx_file_path": "uploads/routes/seafront_cruise.gpx", # Placeholder
    },
    {
        "_id": "R02",
        "hotel_id": "H01",
        "name": "Devil's Dyke Loop",
        "description": "A challenging loop from the city into the South Downs, featuring the iconic Devil's Dyke climb and rewarding views.",
        "distance_km": 42.0,
        "elevation_m": 650,
        "surface_type": "Road",
        "tags": ["climbing", "views", "South Downs"],
        "gpx_file_path": "uploads/routes/devils_dyke.gpx",
    }
]

POINTS_OF_INTEREST = [
    {
        "_id": "POI01",
        "route_id": "R02",
        "name": "Small Batch Coffee Roasters",
        "type": "cafe",
        "location": {"type": "Point", "coordinates": [-0.1537, 50.8306]}
    },
    {
        "_id": "POI02",
        "route_id": "R02",
        "name": "Devil's Dyke Viewpoint",
        "type": "viewpoint",
        "location": {"type": "Point", "coordinates": [-0.2085, 50.8845]}
    }
]

def seed_database():
    """Connects to MongoDB and populates it with sample data."""
    client = MongoClient(MONGO_URI)
    db = client.get_default_database() # Gets DB name from URI

    print("Dropping existing collections...")
    db.hotels.drop()
    db.routes.drop()
    db.points_of_interest.drop()

    print("Seeding 'hotels' collection...")
    db.hotels.insert_many(HOTELS)
    # Create a geospatial index for location-based queries
    db.hotels.create_index([("location", GEOSPHERE)])
    print(f"{db.hotels.count_documents({})} hotels inserted.")

    print("\nSeeding 'routes' collection...")
    db.routes.insert_many(ROUTES)
    print(f"{db.routes.count_documents({})} routes inserted.")
    
    print("\nSeeding 'points_of_interest' collection...")
    db.points_of_interest.insert_many(POINTS_OF_INTEREST)
    db.points_of_interest.create_index([("location", GEOSPHERE)])
    print(f"{db.points_of_interest.count_documents({})} POIs inserted.")

    print("\nDatabase seeding complete!")
    client.close()

if __name__ == "__main__":
    seed_database()
