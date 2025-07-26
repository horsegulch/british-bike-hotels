# app/admin/admin_routes.py

import os
import shortuuid
from flask import render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required
from . import admin
from .. import mongo
from .forms import AddHotelForm, AddRouteForm, EditRouteForm
from ..utils.gpx_utils import parse_gpx_file
from werkzeug.utils import secure_filename

@admin.route('/')
@login_required
def dashboard():
    """Renders the admin dashboard."""
    return render_template('admin/dashboard.html')

# --- Hotel Management ---

@admin.route('/manage-hotels')
@login_required
def manage_hotels():
    """Renders the page to manage all hotels."""
    hotels = mongo.db.hotels.find().sort("name", 1)
    return render_template('admin/manage_hotels.html', hotels=hotels)

@admin.route('/add-hotel', methods=['GET', 'POST'])
@login_required
def add_hotel():
    """Handles creating a new hotel with all the new fields."""
    form = AddHotelForm()
    if form.validate_on_submit():
        coords_list = [float(coord.strip()) for coord in form.coordinates.data.split(',')]
        
        new_hotel = {
            '_id': shortuuid.uuid(),
            'name': form.name.data,
            'description': form.description.data,
            'website': form.website.data,
            'phone': form.phone.data,
            'location': {'type': 'Point', 'coordinates': coords_list},
            'is_featured': form.is_featured.data,
            'status': form.status.data,
            # --- SAVING NEW FIELDS ---
            'accommodation_type': form.accommodation_type.data,
            'star_rating': form.star_rating.data,
            'price_range': form.price_range.data,
            'google_rating': float(form.google_rating.data) if form.google_rating.data else None,
            'facilities': form.facilities.data
        }
        mongo.db.hotels.insert_one(new_hotel)
        flash('Hotel added successfully!', 'success')
        return redirect(url_for('admin.manage_hotels'))

    jawg_token = os.getenv('JAWG_ACCESS_TOKEN')
    return render_template('admin/add_hotel.html', form=form, jawg_token=jawg_token)

@admin.route('/edit-hotel/<hotel_id>', methods=['GET', 'POST'])
@login_required
def edit_hotel(hotel_id):
    """Handles editing an existing hotel with all the new fields."""
    hotel = mongo.db.hotels.find_one_or_404({'_id': hotel_id})
    form = AddHotelForm(data=hotel)

    if form.validate_on_submit():
        coords_list = [float(coord.strip()) for coord in form.coordinates.data.split(',')]
        
        update_data = {
            'name': form.name.data,
            'description': form.description.data,
            'website': form.website.data,
            'phone': form.phone.data,
            'location': {'type': 'Point', 'coordinates': coords_list},
            'is_featured': form.is_featured.data,
            'status': form.status.data,
            # --- UPDATING NEW FIELDS ---
            'accommodation_type': form.accommodation_type.data,
            'star_rating': form.star_rating.data,
            'price_range': form.price_range.data,
            'google_rating': float(form.google_rating.data) if form.google_rating.data else None,
            'facilities': form.facilities.data
        }
        mongo.db.hotels.update_one({'_id': hotel_id}, {'$set': update_data})
        flash('Hotel updated successfully!', 'success')
        return redirect(url_for('admin.manage_hotels'))

    # Pre-populate coordinates manually
    form.coordinates.data = f"{hotel['location']['coordinates'][0]}, {hotel['location']['coordinates'][1]}"
    
    # Pre-populate facilities checkbox list
    form.facilities.data = hotel.get('facilities', [])


    jawg_token = os.getenv('JAWG_ACCESS_TOKEN')
    active_routes = mongo.db.routes.find({'hotel_id': hotel_id, 'status': 'active'}).sort("name", 1)
    return render_template('admin/edit_hotel.html', form=form, jawg_token=jawg_token, hotel=hotel, routes=list(active_routes))

@admin.route('/hotel/<hotel_id>/delete', methods=['POST'])
@login_required
def delete_hotel(hotel_id):
    """Soft deletes a hotel by setting its status to 'offline'."""
    mongo.db.hotels.update_one({'_id': hotel_id}, {'$set': {'status': 'offline'}})
    flash('Hotel has been set to offline.', 'success')
    return redirect(url_for('admin.manage_hotels'))

# --- Route Management ---

@admin.route('/hotel/<hotel_id>/add-route', methods=['GET', 'POST'])
@login_required
def add_route(hotel_id):
    """Handles adding a new route to a specific hotel."""
    hotel = mongo.db.hotels.find_one_or_404({'_id': hotel_id})
    form = AddRouteForm()
    if form.validate_on_submit():
        gpx_file = form.gpx_file.data
        filename = secure_filename(gpx_file.filename)
        
        # Define the save path
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'routes')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        
        # Save the file
        gpx_file.save(file_path)
        
        # Process the saved file
        with open(file_path, 'r') as f:
            route_data = parse_gpx_file(f)

        new_route = {
            '_id': shortuuid.uuid(),
            'hotel_id': hotel_id,
            'name': form.name.data,
            'description': form.description.data,
            'surface_type': form.surface_type.data,
            'gpx_file_path': os.path.join('uploads', 'routes', filename).replace("\\", "/"), # Store relative path
            'distance_km': route_data['distance_km'],
            'elevation_m': route_data['elevation_gain_m'],
            'difficulty': route_data['difficulty'],
            'status': 'active' # Default status
        }
        mongo.db.routes.insert_one(new_route)
        flash('Route added successfully!', 'success')
        return redirect(url_for('admin.edit_hotel', hotel_id=hotel_id))

    return render_template('admin/add_route.html', form=form, hotel=hotel)

@admin.route('/route/<route_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_route(route_id):
    """Handles editing an existing route."""
    route = mongo.db.routes.find_one_or_404({'_id': route_id})
    form = EditRouteForm(data=route)

    if form.validate_on_submit():
        update_data = {
            'name': form.name.data,
            'description': form.description.data,
            'surface_type': form.surface_type.data,
        }
        # Check if a new GPX file was uploaded
        if form.gpx_file.data:
            gpx_file = form.gpx_file.data
            filename = secure_filename(gpx_file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'routes')
            file_path = os.path.join(upload_folder, filename)
            gpx_file.save(file_path)

            with open(file_path, 'r') as f:
                route_data = parse_gpx_file(f)
            
            update_data['gpx_file_path'] = os.path.join('uploads', 'routes', filename).replace("\\", "/")
            update_data['distance_km'] = route_data['distance_km']
            update_data['elevation_m'] = route_data['elevation_gain_m']
            update_data['difficulty'] = route_data['difficulty']

        mongo.db.routes.update_one({'_id': route_id}, {'$set': update_data})
        flash('Route updated successfully!', 'success')
        return redirect(url_for('admin.edit_hotel', hotel_id=route['hotel_id']))
    
    hotel = mongo.db.hotels.find_one_or_404({'_id': route['hotel_id']})
    return render_template('admin/edit_route.html', form=form, route=route, hotel=hotel)

@admin.route('/route/<route_id>/delete', methods=['POST'])
@login_required
def delete_route(route_id):
    """Soft deletes a route by setting its status to 'archived'."""
    route = mongo.db.routes.find_one_or_404({'_id': route_id})
    mongo.db.routes.update_one({'_id': route_id}, {'$set': {'status': 'archived'}})
    flash('Route has been archived.', 'success')
    return redirect(url_for('admin.edit_hotel', hotel_id=route['hotel_id']))

# --- Blog Post Management ---
from ..blog.forms import PostForm

@admin.route('/manage-posts')
@login_required
def manage_posts():
    posts = mongo.db.blog_posts.find().sort("created_at", -1)
    return render_template('admin/manage_posts.html', posts=posts)

@admin.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = {
            '_id': shortuuid.uuid(),
            'title': form.title.data,
            'slug': form.slug.data,
            'summary': form.summary.data,
            'content': form.content.data,
            'status': form.status.data,
            'created_at': datetime.utcnow()
        }
        mongo.db.blog_posts.insert_one(new_post)
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.manage_posts'))
    return render_template('admin/edit_post.html', form=form, post=None)

@admin.route('/edit-post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = mongo.db.blog_posts.find_one_or_404({'_id': post_id})
    form = PostForm(data=post)
    if form.validate_on_submit():
        mongo.db.blog_posts.update_one({'_id': post_id}, {'$set': {
            'title': form.title.data,
            'slug': form.slug.data,
            'summary': form.summary.data,
            'content': form.content.data,
            'status': form.status.data
        }})
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.manage_posts'))
    return render_template('admin/edit_post.html', form=form, post=post)

@admin.route('/delete-post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    mongo.db.blog_posts.delete_one({'_id': post_id})
    flash('Blog post deleted permanently.', 'success')
    return redirect(url_for('admin.manage_posts'))
