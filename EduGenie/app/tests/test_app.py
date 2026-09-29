import os

# Test database and configuration.
os.environ["DATABASE_PATH"] = "data/test_edugenie.db"
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["GEMINI_API_KEY"] = ""


from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    assert "EduGenie" in response.text


def test_login_required():

    response = client.post(
        "/api/chat",
        json={
            "message": "hello",
            "history": [],
        },
    )

    assert response.status_code == 401