import pytest
from fastapi.testclient import TestClient

from app.main import app, limiter


@pytest.fixture
def client():
    limiter.enabled = True
    yield TestClient(app)
    limiter.enabled = False


def test_rate_limiting_middleware(client):
    # Arrange
    headers = {"User-Agent": "pytest"}

    # Act & Assert
    for i in range(100):
        response = client.get("/", headers=headers)
        assert response.status_code == 200

    response = client.get("/", headers=headers)
    assert response.status_code == 429
