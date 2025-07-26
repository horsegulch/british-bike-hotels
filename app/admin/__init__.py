# app/admin/__init__.py

from flask import Blueprint

# This creates the 'admin' blueprint, which will be prefixed with '/admin'.
admin = Blueprint('admin', __name__)

# Import routes at the bottom to avoid circular dependencies.
from . import admin_routes
