# config.py

import os
from dotenv import load_dotenv

# Find the absolute path of the root directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from a .env file if it exists.
# This is useful for development environments.
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    Base configuration class. Contains default settings and settings
    loaded from environment variables that are common to all environments.
    """
    # A secret key is required for session management and other security features.
    # It's read from an environment variable for security best practices.
    # A default value is provided for convenience in development.
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-fallback-secret-key')

    # The MongoDB URI is also loaded from an environment variable.
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/britishbikehotels')
    
    JAWG_TOKEN = os.environ.get('JAWG_ACCESS_TOKEN')


    # Flask-PyMongo specific settings can be added here if needed,
    # for example, app.config['MONGO_DBNAME'] = 'britishbikehotels'

    # ADD THESE NEW EMAIL SETTINGS
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') # Reads 'MAIL_USERNAME' from .env [cite: 1]
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # Reads 'MAIL_PASSWORD' from .env [cite: 1]
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    @staticmethod
    def init_app(app):
        """
        This method can be used to perform application-specific initializations.
        For now, it does nothing but is kept for good practice.
        """
        pass

class DevelopmentConfig(Config):
    """
    Configuration settings for development. Inherits from the base Config
    and overrides settings for a development environment.
    """
    # Enables debug mode, which provides helpful error pages and reloads
    # the server automatically when code changes.
    DEBUG = True

class TestingConfig(Config):
    """
    Configuration settings for testing. Inherits from the base Config.
    """
    # Enables testing mode in Flask extensions.
    TESTING = True
    
    # Use a separate database for testing to avoid conflicts with
    # development or production data.
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/britishbikehotels_test')
    
    # WTForms requires this to be False for tests to work correctly with CSRF protection.
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """
    Configuration settings for production. Inherits from the base Config.
    This class would contain settings optimized for a live environment,
    such as different database credentials or logging configurations.
    """
    # Production configuration would be more robust.
    # For example, you might want to configure logging to a file.
    pass

# A dictionary to map configuration names to their respective classes.
# This allows for easy selection of the configuration in the app factory.
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
