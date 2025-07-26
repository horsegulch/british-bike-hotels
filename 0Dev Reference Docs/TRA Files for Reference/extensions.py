# extensions.py

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Create extension instances
bcrypt = Bcrypt()
login_manager = LoginManager()
mongo = PyMongo()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv("REDIS_URI", "memory://"),
    strategy="fixed-window"
)

# Configure login_manager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'