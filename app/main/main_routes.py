# app/main/main_routes.py

import os
import json
import secrets
import datetime
import shortuuid
from flask import render_template, request, flash, abort, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import mail
from . import main
from .. import mongo
from ..utils.gpx_utils import parse_gpx_file
from bson.objectid import ObjectId
from .forms import HotelSignupForm, HotelOnboardingForm


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

@main.route('/pricing')
def pricing():
    """Renders the hotel pricing and subscription page."""
    return render_template('pricing.html')


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

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles hotel sign-up."""
    plan = request.args.get('plan', 'standard')
    form = HotelSignupForm()
    
    # Pre-populate the hidden plan field when the form is first loaded
    if request.method == 'GET':
        form.plan.data = plan

    if form.validate_on_submit():
        hotel_name = form.hotel_name.data
        contact_name = form.contact_name.data
        email = form.email.data
        selected_plan = form.plan.data
        
        # Compose the email
        msg = Message(
            subject=f"New Hotel Signup: {hotel_name}",
            recipients=[os.environ.get('MAIL_USERNAME')] # Sends the email to yourself
        )
        msg.body = f"""
        A new hotel has signed up!

        Hotel Name: {hotel_name}
        Contact Name: {contact_name}
        Contact Email: {email}
        Selected Plan: {selected_plan}
        """
        
        # Send the email
        mail.send(msg)

        flash('Thank you for signing up! We will be in touch shortly to complete your listing.', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('main/signup.html', form=form, plan=form.plan.data or plan)

@main.route('/terms')
def terms():
    """Renders the placeholder terms and conditions page."""
    # In a real application, you would render a template with your full T&Cs.
    return "<h1>Terms and Conditions</h1><p>This is a placeholder page. You must consult a legal professional to create your own terms.</p>"

@main.route('/onboarding/<token>', methods=['GET', 'POST'])
def onboarding(token):
    onboarding_token = mongo.db.onboarding_tokens.find_one({'token': token, 'status': 'unused'})
    if not onboarding_token:
        flash('This invitation link is invalid or has already been used.', 'danger')
        return redirect(url_for('main.index'))

    form = HotelOnboardingForm()
    if form.validate_on_submit():
        # --- Handle File Uploads (your existing code) ---
        photos_path = os.path.join(current_app.root_path, 'static/uploads/hotel_photos')
        routes_path = os.path.join(current_app.root_path, 'static/uploads/routes')
        os.makedirs(photos_path, exist_ok=True)
        os.makedirs(routes_path, exist_ok=True)

        photo_filenames = []
        for photo_file in form.photos.data:
            if photo_file:
                filename = secure_filename(photo_file.filename)
                photo_file.save(os.path.join(photos_path, filename))
                photo_filenames.append(os.path.join('uploads/hotel_photos', filename).replace("\\", "/"))

        route_filenames = []
        for route_file in form.routes.data:
            if route_file:
                filename = secure_filename(route_file.filename)
                route_file.save(os.path.join(routes_path, filename))
                route_filenames.append(os.path.join('uploads/routes', filename).replace("\\", "/"))

        # --- Create a new hotel document with 'pending' status ---
        coords_list = [float(coord.strip()) for coord in form.coordinates.data.split(',')]
        
        new_hotel = {
            '_id': shortuuid.uuid(),
            'name': form.hotel_name.data,
            'plan': onboarding_token.get('plan', 'standard'), # Get plan from the token
            'description': form.description.data,
            'website': form.website.data,
            'phone': form.phone_number.data,
            'location': {'type': 'Point', 'coordinates': coords_list},
            'accommodation_type': form.accommodation_type.data,
            'facilities': form.facilities.data,
            'photos': photo_filenames, # Store relative paths to photos
            'status': 'pending', # Set status to pending for approval
            'is_featured': onboarding_token.get('plan') == 'premium' # Also set featured status
            # Other fields like star_rating can be added by admin later
        }
        mongo.db.hotels.insert_one(new_hotel)
        
        # --- Add submitted routes to the routes collection ---
        for route_path in route_filenames:
            full_path = os.path.join(current_app.root_path, 'static', route_path)
            try:
                with open(full_path, 'r') as f:
                    route_data = parse_gpx_file(f)
                
                new_route = {
                    '_id': shortuuid.uuid(),
                    'hotel_id': new_hotel['_id'],
                    'name': os.path.splitext(os.path.basename(route_path))[0].replace('_', ' ').title(),
                    'plan': onboarding_token.get('plan', 'standard'),
                    'description': 'Route provided by hotel.',
                    'surface_type': 'Mixed', # Default surface type
                    'gpx_file_path': route_path,
                    'distance_km': route_data.get('distance_km', 0),
                    'elevation_m': route_data.get('elevation_gain_m', 0), # Use .get() with a default of 0
                    'difficulty': route_data.get('difficulty', 'moderate'), # Use .get() with a default
                    'status': 'active'
                }
                mongo.db.routes.insert_one(new_route)
            except Exception as e:
                print(f"Error processing GPX file {route_path}: {e}")


        # --- Mark token as used ---
        mongo.db.onboarding_tokens.update_one(
            {'_id': onboarding_token['_id']},
            {'$set': {'status': 'used', 'submitted_at': datetime.datetime.utcnow(), 'hotel_id': new_hotel['_id']}}
        )

        # --- Send Email Notification to Admin ---
        msg = Message(
            subject=f"New Hotel Submission for Approval: {form.hotel_name.data}",
            recipients=[os.environ.get('MAIL_USERNAME')]
        )
        msg.body = f"""
        A new hotel has submitted their profile for approval.

        Hotel Name: {form.hotel_name.data}
        
        You can review and approve it by visiting your admin dashboard.
        """
        mail.send(msg)

        flash('Thank you for your submission! We will review your profile and be in touch shortly.', 'success')
        return redirect(url_for('main.index'))

    jawg_token = current_app.config.get('JAWG_TOKEN')
    plan = onboarding_token.get('plan', 'standard') # Get the plan from the token
    return render_template('main/onboarding.html', form=form, jawg_token=jawg_token, token=token, plan=plan)


    return render_template('main/onboarding.html', form=form, jawg_token=jawg_token, token=token)