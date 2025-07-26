BritishBikeHotels.com

Discover your next ride's rest stop. A modern, map-centric web application for cyclists to discover bike-friendly hotels and their best routes across the UK.

This platform provides a rich, interactive map for users to explore locations, a powerful admin panel for content management, and a dynamic API to serve data efficiently.
Table of Contents

    About The Project

        Core Features

        Built With

    Getting Started

        Prerequisites

        Installation

    Usage

        Running the Application

        Creating an Admin User

    Project Structure

    API Endpoints

About The Project

BritishBikeHotels.com is a full-stack web application built with Python (Flask) and MongoDB. It aims to be the premier resource for cycle-tourists in the UK, providing a curated database of hotels that cater specifically to the needs of cyclists, complete with detailed route information and planning tools.
Core Features

    Interactive Homepage Map: A dynamic map showing all approved hotels, with marker clustering for clean visualization.

    Reactive Sidebar: A live-updating list of hotels currently visible on the map, allowing for easy Browse and comparison.

    Location Search: An autocomplete search bar to quickly find and navigate to specific towns, regions, or national parks.

    Detailed Hotel & Route Profiles: SEO-friendly pages for each hotel and cycling route, featuring descriptions, key stats, interactive maps, and elevation profiles.

    Content Management System: A secure admin dashboard for managing all site content, including hotels, GPX routes, and blog posts.

    Content-Rich Blog: An integrated blog for sharing regional guides, tips, and news.

Built With

    Backend: Python with Flask

    Database: MongoDB with PyMongo

    Frontend: HTML, Tailwind CSS, and vanilla JavaScript

    Mapping: Leaflet.js with Jawg Maps tiles and the Leaflet.markercluster plugin.

    Authentication: Flask-Login and Flask-Bcrypt

Getting Started

Follow these steps to get a local copy up and running.
Prerequisites

    Python 3.8+

    pip and venv

    A running instance of MongoDB Community Server.

Installation

    Clone the repository:

    git clone [https://github.com/your-username/british-bike-hotels.git](https://github.com/your-username/british-bike-hotels.git)
    cd british-bike-hotels

    Create and activate a virtual environment:

    # For Windows (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    Install the required Python packages:

    pip install -r requirements.txt

    Set up your environment variables:

        Make a copy of the .env.example file and rename it to .env.

        Open the .env file and fill in the required values, such as your SECRET_KEY and JAWG_ACCESS_TOKEN. The default MONGO_URI should work for a standard local installation.

    Seed the database with sample data:

        Ensure your MongoDB server is running.

        Run the seed script from your terminal:

    python seed_db.py

Usage
Running the Application

Once the installation is complete, you can run the Flask development server:

flask run

The application will be available at http://127.0.0.1:5000.
Creating an Admin User

To access the admin dashboard, you must first create an administrator account. Run the following custom command in your terminal and follow the prompts:

flask create-admin

