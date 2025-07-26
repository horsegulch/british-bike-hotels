# app/auth/auth_routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from . import auth
from .forms import LoginForm
from ..models import User

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the admin login process."""
    form = LoginForm()
    if form.validate_on_submit():
        # Find the user by their username in the database
        user = User.find_by_username(form.username.data)
        
        # Check if the user exists and the password is correct
        if user and user.check_password(form.password.data):
            # Log the user in using Flask-Login's login_user function
            login_user(user)
            flash('You have been logged in successfully!', 'success')
            
            # Redirect to the page the user was trying to access, or the dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html', title='Admin Login', form=form)

@auth.route('/logout')
@login_required # Protect this route so only logged-in users can access it
def logout():
    """Handles the admin logout process."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
