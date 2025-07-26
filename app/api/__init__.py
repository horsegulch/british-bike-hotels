# app/api/__init__.py

from flask import Blueprint

# This creates the 'api' blueprint. All routes defined in this blueprint
# will be prefixed with '/api' as specified in the application factory
# in app/__init__.py.
api = Blueprint('api', __name__)

# We import the route modules at the bottom to avoid circular dependencies.
# As the API grows, we can add more route files here to keep the code organized
# according to functionality (e.g., tracking, trip planning).
from . import api_routes
# The following will be created in later steps:
# from . import tracking_routes, planner_routes
