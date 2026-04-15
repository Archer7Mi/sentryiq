from fastapi.testclient import TestClient

from sentryiq_api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_stack_assessment_detects_chain() -> None:
    response = client.post(
        "/api/stack/assess",
        json={
            "organization": "Demo SMB",
            "stack": [
                {
                    "category": "web",
                    "name": "Apache HTTP Server",
                    "version": "2.4.58",
                    "internet_facing": True,
                },
                {
                    "category": "security",
                    "name": "OpenSSL",
                    "version": "3.0.0",
                    "internet_facing": False,
                },
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["findings"]
    assert data["chains"]
    assert data["priority_queue"][0]["rank"] == 1


def test_phishing_simulation_returns_copy() -> None:
    response = client.post(
        "/api/simulations/phishing",
        json={
            "target_name": "Maya Okafor",
            "target_role": "Finance Manager",
            "channel": "email",
            "scenario": "invoice update",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "Maya Okafor" in data["body"]
