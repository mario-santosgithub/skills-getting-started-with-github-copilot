"""
Pytest configuration and shared fixtures for activity API tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provides a TestClient instance for making API requests.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets activities to initial state before and after each test.
    Ensures test isolation and prevents test pollution.
    """
    # Store original state
    original_activities = {
        key: {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy(),
        }
        for key, value in activities.items()
    }

    yield  # Test runs here

    # Restore original state after test
    for activity_name, activity_data in activities.items():
        activity_data["participants"] = original_activities[activity_name]["participants"].copy()


@pytest.fixture
def sample_email():
    """Provides a sample test email."""
    return "test.student@mergington.edu"


@pytest.fixture
def sample_activity_name():
    """Provides a sample activity name that exists in the database."""
    return "Chess Club"


@pytest.fixture
def nonexistent_activity_name():
    """Provides an activity name that does not exist."""
    return "Nonexistent Activity"
