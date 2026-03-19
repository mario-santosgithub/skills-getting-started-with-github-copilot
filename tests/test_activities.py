"""
Tests for the Mergington High School Activities API.
Uses AAA (Arrange-Act-Assert) pattern for test structure.
"""

import pytest
from fastapi.testclient import TestClient
from urllib.parse import quote


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Test that GET /activities returns all available activities.
        
        Arrange: TestClient is ready
        Act: Make GET request to /activities
        Assert: Status is 200 and response contains activity data
        """
        # Arrange
        expected_activity_names = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Tennis Club", "Art Studio",
            "Music Ensemble", "Debate Team", "Science Club"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        for activity_name in expected_activity_names:
            assert activity_name in activities_data
            assert "description" in activities_data[activity_name]
            assert "schedule" in activities_data[activity_name]
            assert "max_participants" in activities_data[activity_name]
            assert "participants" in activities_data[activity_name]

    def test_get_activities_participants_is_list(self, client, reset_activities):
        """
        Test that participants field is always a list.
        
        Arrange: TestClient is ready
        Act: Make GET request to /activities
        Assert: Each activity's participants field is a list
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """
        Test that GET / redirects to /static/index.html.
        
        Arrange: TestClient is ready
        Act: Make GET request to /
        Assert: Response is a redirect (status 307)
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success_adds_participant(self, client, reset_activities, sample_email, sample_activity_name):
        """
        Test successful signup adds participant to activity.
        
        Arrange: Set up test email and activity name
        Act: Send POST request to signup endpoint
        Assert: Response is 200 and participant is in the activity
        """
        # Arrange
        email = sample_email
        activity = sample_activity_name

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        # Verify participant was actually added by fetching activities
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities, sample_email, nonexistent_activity_name):
        """
        Test signup fails with 404 when activity doesn't exist.
        
        Arrange: Set up non-existent activity name
        Act: Send POST request with non-existent activity
        Assert: Response is 404 with appropriate error message
        """
        # Arrange
        email = sample_email
        activity = nonexistent_activity_name

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_fails(self, client, reset_activities, sample_activity_name):
        """
        Test that signup fails with 400 when student already registered.
        
        Arrange: Get an existing participant from an activity
        Act: Try to sign up the same email again
        Assert: Response is 400 with duplicate signup error
        """
        # Arrange
        activities_response = client.get("/activities")
        activity = sample_activity_name
        existing_participants = activities_response.json()[activity]["participants"]
        assert len(existing_participants) > 0
        existing_email = existing_participants[0]

        # Act
        response = client.post(f"/activities/{activity}/signup?email={existing_email}")

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_new_participant_success(self, client, reset_activities, sample_activity_name):
        """
        Test successful signup with a brand new email.
        
        Arrange: Generate a unique email not in any activity
        Act: Sign up with new email
        Assert: Response is 200 and participant appears in activity
        """
        # Arrange
        new_email = "brandnew.student@mergington.edu"
        activity = sample_activity_name

        # Act
        response = client.post(f"/activities/{activity}/signup?email={new_email}")

        # Assert
        assert response.status_code == 200
        assert new_email in response.json()["message"]
        
        # Verify in database
        activities_response = client.get("/activities")
        assert new_email in activities_response.json()[activity]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_success_removes_participant(self, client, reset_activities, sample_activity_name):
        """
        Test successful unregister removes participant from activity.
        
        Arrange: Get an existing participant
        Act: Send DELETE request to unregister endpoint
        Assert: Response is 200 and participant removed from activity
        """
        # Arrange
        activities_response = client.get("/activities")
        activity = sample_activity_name
        participants_before = activities_response.json()[activity]["participants"]
        assert len(participants_before) > 0
        email_to_remove = participants_before[0]

        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email_to_remove}")

        # Assert
        assert response.status_code == 200
        assert email_to_remove in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email_to_remove not in activities_response.json()[activity]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities, sample_email, nonexistent_activity_name):
        """
        Test unregister fails with 404 when activity doesn't exist.
        
        Arrange: Set up non-existent activity
        Act: Send DELETE request for non-existent activity
        Assert: Response is 404
        """
        # Arrange
        email = sample_email
        activity = nonexistent_activity_name

        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_participant_not_found(self, client, reset_activities, sample_activity_name):
        """
        Test unregister fails with 400 when participant not signed up.
        
        Arrange: Use email that is not signed up
        Act: Try to unregister non-existent participant
        Assert: Response is 400
        """
        # Arrange
        email = "not.registered@mergington.edu"
        activity = sample_activity_name

        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_and_signup_again(self, client, reset_activities, sample_activity_name):
        """
        Test that student can signup again after unregistering.
        
        Arrange: Get an existing participant
        Act: Unregister, then sign up again with same email
        Assert: Both operations succeed
        """
        # Arrange
        activities_response = client.get("/activities")
        activity = sample_activity_name
        email = activities_response.json()[activity]["participants"][0]

        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity}/signup?email={email}")

        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]

        # Act - Sign up again
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert signup succeeded
        assert signup_response.status_code == 200
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_signup_with_special_characters_in_email(self, client, reset_activities, sample_activity_name):
        """
        Test signup with special characters in email.
        
        Arrange: Create email with special characters
        Act: Attempt to sign up
        Assert: Request succeeds (no email format validation)
        """
        # Arrange
        email = "student.test.2024@mergington.edu"  # Using dots which are safe in URLs
        activity = sample_activity_name

        # Act
        response = client.post(f"/activities/{activity}/signup?email={quote(email)}")

        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

    def test_activity_name_case_sensitive(self, client, reset_activities):
        """
        Test that activity names are case-sensitive.
        
        Arrange: Use wrong case for activity name
        Act: Try to sign up with wrong case
        Assert: Returns 404 (activity not found)
        """
        # Arrange
        email = "test@mergington.edu"
        activity = "chess club"  # lowercase instead of "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_multiple_signups_different_activities(self, client, reset_activities, sample_email):
        """
        Test that same student can sign up for multiple activities.
        
        Arrange: Prepare two different activities
        Act: Sign up for both activities
        Assert: Both signups succeed and email is in both activities
        """
        # Arrange
        email = sample_email
        activities_list = ["Chess Club", "Programming Class"]

        # Act & Assert
        for activity in activities_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200

        # Verify email is in both activities
        activities_response = client.get("/activities")
        for activity in activities_list:
            assert email in activities_response.json()[activity]["participants"]
