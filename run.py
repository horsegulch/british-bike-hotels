# run.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app
from app.commands import create_admin_command

# Get the config name from environment or use default
config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(config_name)

# Register the custom command with the Flask app
app.cli.add_command(create_admin_command)

if __name__ == '__main__':
    app.run()