"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        activity: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for activity, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity, details in original_activities.items():
        if activity in activities:
            activities[activity]["participants"] = details["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Check structure of first activity
    first_activity = list(data.values())[0]
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity


def test_signup_success(client):
    """Test successful signup for an activity"""
    # Pick an activity with available spots
    activity_name = "Soccer Team"
    email = "test@mergington.edu"
    
    # Ensure the email is not already registered
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was added
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate(client):
    """Test signing up when already registered"""
    activity_name = "Soccer Team"
    email = "duplicate@mergington.edu"
    
    # First signup
    activities[activity_name]["participants"].append(email)
    
    # Try to signup again
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_signup_invalid_activity(client):
    """Test signing up for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_unregister_success(client):
    """Test successful unregistration from an activity"""
    activity_name = "Basketball Team"
    email = "unregister@mergington.edu"
    
    # First, add the participant
    activities[activity_name]["participants"].append(email)
    
    # Now unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Unregistered" in data["message"]
    
    # Verify participant was removed
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_registered(client):
    """Test unregistering when not signed up"""
    activity_name = "Drama Club"
    email = "notregistered@mergington.edu"
    
    # Ensure email is not in participants
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"].lower()


def test_unregister_invalid_activity(client):
    """Test unregistering from non-existent activity"""
    response = client.delete(
        "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_and_unregister_flow(client):
    """Test complete flow of signing up and then unregistering"""
    activity_name = "Art Studio"
    email = "flow@mergington.edu"
    
    # Ensure clean state
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)
    
    initial_count = len(activities[activity_name]["participants"])
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    assert len(activities[activity_name]["participants"]) == initial_count
    assert email not in activities[activity_name]["participants"]
