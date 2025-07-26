```
# The Ride Archive

The Ride Archive is a web application for cyclists to share, rate, and discover community-created routes. Users can upload GPX/TCX files, which are processed to calculate difficulty and other metrics, and then share them with the community through reviews and photos.

---

## Features

-   **Route Processing:** Upload GPX/TCX files or provide URLs to have them analyzed for distance, elevation, and a calculated difficulty score.
-   **Community Reviews:** A rich review system allows users to give 5-star ratings on metrics like Scenery and Traffic, write a "Ride Report," and upload photos.
-   **Discovery:** Browse, search, and filter routes by surface type and tags.
-   **User Profiles:** Manage your profile, see your uploaded and favorited routes, and track your reviews.
-   **Background Jobs:** File processing is handled by Celery and Redis for a fast and non-blocking user experience.

---

## Tech Stack

-   **Backend:** Python 3, Flask
-   **Database:** MongoDB (with Flask-PyMongo)
-   **Async Tasks:** Celery with a Redis broker
-   **Frontend:** Jinja2 templates, CSS, vanilla JavaScript
-   **Key Python Libraries:** Flask-Login, Flask-Bcrypt, Flask-Limiter, geopy, Pillow, gpxpy

---

## Local Development Setup

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

-   Python 3.10+
-   MongoDB running locally or on a cloud service (e.g., MongoDB Atlas).
-   Redis running locally.

### 2. Installation

Clone the repository and navigate into the project directory:

```shell
git clone <your-repo-url>
cd Ride-Archive
```

Create and activate a Python virtual environment:

```
# For Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install the required packages from your requirements.txt file:

(Note: If you haven't created this file yet, do so now by running pip freeze > requirements.txt)

```
pip install -r requirements.txt
```

### 3. Configuration

Create a file named `.env` in the root of the project directory. Copy the contents of `.env.example` (or create it from scratch) and fill in your specific configuration details:

```
# .env

# A long, random string used to sign user sessions
SECRET_KEY='your_super_secret_key_here'

# Your MongoDB connection string
MONGO_URI='mongodb://localhost:27017/ride_archive_db'

# Your Redis connection string for Celery
REDIS_URI='redis://localhost:6379/0'
```

### 4. Running the Application

You need to run two separate processes in two separate terminals.

**Terminal 1: Run the Flask Web Server**

```
(venv) > python app.py
```

The web application will be available at `http://127.0.0.1:5000`.

**Terminal 2: Run the Celery Worker**

```
(venv) > celery -A celery_worker.celery worker --loglevel=info -P solo
```
