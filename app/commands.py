# app/commands.py

import click
from flask.cli import with_appcontext
from .models import User

@click.command('create-admin')
@with_appcontext
@click.option('--username', prompt=True, help='The username for the new admin.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password for the new admin.')
def create_admin_command(username, password):
    """Creates a new admin user."""
    
    # Check if user already exists
    if User.find_by_username(username):
        click.echo(f"Error: User '{username}' already exists.")
        return

    # Create new user instance
    admin_user = User(username=username)
    admin_user.set_password(password)
    
    # Save to database
    admin_user.save()
    
    click.echo(f"Admin user '{username}' created successfully.")

