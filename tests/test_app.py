import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def restore_state():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


client = TestClient(app_module.app)


def test_unregister_participant_removes_email():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]

    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_missing_participant_returns_404():
    response = client.delete("/activities/Chess Club/participants/not-found@example.com")

    assert response.status_code == 404


def test_signup_rejects_blank_email():
    response = client.post("/activities/Chess Club/signup", params={"email": "   "})

    assert response.status_code == 400
    assert "Email is required" in response.json()["detail"]


def test_signup_rejects_case_insensitive_duplicate():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "MICHAEL@MERGINGTON.EDU"},
    )

    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_rejects_when_activity_is_full():
    activity_name = "Chess Club"
    activity = app_module.activities[activity_name]
    activity["participants"] = [f"student{i}@example.com" for i in range(activity["max_participants"])]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "newstudent@example.com"},
    )

    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_signup_rejects_blank_activity_name():
    response = client.post("/activities/signup", params={"email": "student@example.com"})

    assert response.status_code == 400
    assert "Activity name is required" in response.json()["detail"]
