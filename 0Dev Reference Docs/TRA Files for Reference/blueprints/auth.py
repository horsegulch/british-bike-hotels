# auth.py - Corrected

from flask import Blueprint, render_template, request, redirect, url_for, g
from flask_login import login_user, logout_user, login_required, current_user
from .models import User # Import the User model
from extensions import limiter

# 1. Define the blueprint at the top
auth_bp = Blueprint('auth', __name__)

# 2. Define the routes for this blueprint

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("100 per day; 20 per hour")
def register():
    if current_user.is_authenticated:
        # Note the 'routes.serve_index' - we'll create this blueprint next.
        # For now, let's point to the future structure.
        return redirect(url_for('routes.serve_index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if g.mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
            return render_template('register.html', error="Username or email already exists.")
        g.mongo.db.users.insert_one({'username': username, 'email': email, 
                                   'password': g.bcrypt.generate_password_hash(password).decode('utf-8'),
                                   'favorites': [], 'ridden': []})
        # Use '.login' to refer to the login route within this same blueprint
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("50 per hour; 10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.serve_index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_doc = g.mongo.db.users.find_one({'username': username})
        if user_doc and g.bcrypt.check_password_hash(user_doc['password'], password):
            # We need the User class to log the user in
            login_user(User(user_doc), remember=request.form.get('remember') == 'on')
            return redirect(request.args.get('next') or url_for('routes.serve_index'))
        return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.serve_index'))

# 3. DO NOT include app.run() or app.register_blueprint() here.
#    This file is now a self-contained component.