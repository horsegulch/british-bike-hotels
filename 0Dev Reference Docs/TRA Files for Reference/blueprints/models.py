# models.py
from flask_login import UserMixin
from bson import ObjectId, errors

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password')
        self.favorites = user_data.get('favorites', []) 
        self.ridden = user_data.get('ridden', [])     

    @staticmethod
    def get(user_id):
        from flask import g  # Use g.mongo instead of mongo
        try:
            user_data = g.mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(user_data)
            return None
        except (errors.InvalidId, TypeError):
            return None