import os
import uuid
from app import app
from extensions import mongo
from staticmap import StaticMap, Line

def regenerate_thumbnails():
    """
    Finds routes missing a thumbnail, generates one, and updates the database.
    """
    # Use the Flask app context to access extensions and config
    with app.app_context():
        # Find routes where the thumbnail filename field is missing or null
        routes_to_fix = mongo.db.routes.find({
            "$or": [
                {"static_map_thumbnail_filename": {"$exists": False}},
                {"static_map_thumbnail_filename": None}
            ]
        })

        count = 0
        for route in routes_to_fix:
            print(f"Processing route: {route.get('route_name', route['_id'])}...")

            track_points = route.get("track_points")
            if not track_points:
                print(f"  -> Skipping, no track points found.")
                continue

            try:
                # --- This is the same logic from your celery_worker.py ---
                line_coordinates = [(p['lon'], p['lat']) for p in track_points]
                if not line_coordinates:
                    print(f"  -> Skipping, no valid coordinates.")
                    continue

                m = StaticMap(400, 250, url_template='https://tile.jawg.io/jawg-terrain/{z}/{x}/{y}.png?access-token=YBQv7FTjjrXurBWVElcKyml8cHSNvYxKsuM9Xs8PdHco0wQj0bpqAj6aLDbbCZ6p')
                line = Line(line_coordinates, '#f3ba19', 3)
                m.add_line(line)
                
                image = m.render(zoom=None)
                thumbnail_filename = f"map_{uuid.uuid4().hex[:10]}.png"
                thumbnail_path = os.path.join(app.config['STATIC_MAP_THUMBNAILS_FOLDER'], thumbnail_filename)
                
                image.save(thumbnail_path)
                
                # --- Update the database document ---
                mongo.db.routes.update_one(
                    {"_id": route["_id"]},
                    {"$set": {"static_map_thumbnail_filename": thumbnail_filename}}
                )
                
                print(f"  -> SUCCESS: Generated {thumbnail_filename}")
                count += 1

            except Exception as e:
                print(f"  -> ERROR generating thumbnail for route {route['_id']}: {e}")

        print(f"\nFinished. Successfully generated {count} new thumbnails.")

if __name__ == '__main__':
    regenerate_thumbnails()
