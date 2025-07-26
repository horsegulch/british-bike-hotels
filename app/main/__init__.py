# app/main/__init__.py

from flask import Blueprint

# A Blueprint is a way to organize a group of related views and other code.
# Rather than registering views and other code directly with an application,
# they are registered with a blueprint. Then the blueprint is registered
# with the application when it is available in a factory function.
main = Blueprint('main', __name__)

# This import is placed at the bottom to avoid circular dependencies.
# The routes module needs to import the 'main' blueprint object from this file,
# so we import the routes after the blueprint has been defined.
from . import main_routes
