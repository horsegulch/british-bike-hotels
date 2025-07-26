# app/models.py

from flask_login import UserMixin
from app import mongo, bcrypt

class User(UserMixin):
    """
    Represents an admin user for BritishBikeHotels.com.

    This class integrates with Flask-Login to handle user sessions.
    It's not an ORM model but a helper class to interact with the 'users'
    collection in MongoDB.
    """
    def __init__(self, username, password_hash=None):
        self.username = username
        self.password_hash = password_hash

    @property
    def id(self):
        """
        Returns the user's ID for Flask-Login. In our case, it's the username.
        """
        return self.username

    def set_password(self, password):
        """Hashes the provided password and stores it."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        if self.password_hash is None:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    def save(self):
        """Saves the user to the database (used for creating the first admin)."""
        mongo.db.users.update_one(
            {'_id': self.username},
            {'$set': {'password': self.password_hash}},
            upsert=True
        )

    @staticmethod
    def find_by_username(username):
        """
        Finds a user in the database by their username.
        Returns a User object if found, otherwise None.
        """
        user_data = mongo.db.users.find_one({"_id": username})
        if user_data:
            return User(
                username=user_data['_id'],
                password_hash=user_data.get('password')
            )
        return None

    # Flask-Login requires a `get` method to load a user from the session ID
    @staticmethod
    def get(user_id):
        """Static method to retrieve a user by their ID (which is their username)."""
        return User.find_by_username(user_id)
