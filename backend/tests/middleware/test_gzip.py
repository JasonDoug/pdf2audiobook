import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_gzip_middleware(client):
    # Arrange
    headers = {"Accept-Encoding": "gzip"}
    long_string = "a" * 2000

    # Act
    response = client.get("/", headers=headers, params={"text": long_string})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
