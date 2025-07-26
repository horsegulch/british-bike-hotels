# app/auth/__init__.py

from flask import Blueprint

# This creates the 'auth' blueprint. All routes defined in this blueprint
# will be prefixed with '/auth' as specified in the application factory.
auth = Blueprint('auth', __name__)

# Import routes and forms at the bottom to avoid circular dependencies.
from . import auth_routes
