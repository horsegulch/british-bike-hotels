# app/api/__init__.py

from flask import Blueprint

api = Blueprint('api', __name__)

# Import the routes to make them available to the blueprint
from . import api_routes
from . import tracking_routes
from . import planner_routes
