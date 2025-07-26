import pytest
from app import app, mongo # Import the main app and the mongo object

# This is our robust fixture that handles setup and teardown.
@pytest.fixture
def client():
    app.config.update({"TESTING": True})

    # --- SETUP ---
    # Ensure the test user doesn't exist before the test.
    mongo.db.users.delete_one({"email": "test@example.com"})

    with app.test_client() as client:
        yield client # The test runs here

    # --- TEARDOWN ---
    # Clean up the user after the test is done.
    mongo.db.users.delete_one({"email": "test@example.com"})


# Test 1: Homepage loads
def test_home_page_loads_successfully(client):
    """
    GIVEN a running Flask application configured for testing
    WHEN a GET request is made to the homepage ('/')
    THEN the response status code should be 200 (OK).
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Find Your Next Great Ride" in response.data


# Test 2: User can register
def test_successful_registration(client):
    """
    GIVEN a running Flask application
    WHEN a POST request is made to the '/register' route with new user data
    THEN the user should be redirected to the login page
    AND a new user should be created in the database.
    """
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 302
    assert response.location == '/login'
    user = mongo.db.users.find_one({"email": "test@example.com"})
    assert user is not None
    assert user['username'] == 'testuser'


# Test 3 (NEW): User can log in
def test_successful_login(client):
    """
    GIVEN a user has been created
    WHEN a POST request is made to the '/login' route with correct credentials
    THEN the user should be redirected to the homepage.
    """
    # GIVEN: First, we create the user by calling the register endpoint.
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })

    # WHEN: Now we attempt to log in with that user's credentials.
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # THEN: We assert that the login was successful and redirected to the homepage.
    assert response.status_code == 302
    assert response.location == '/' # Successful login should redirect to the homepage