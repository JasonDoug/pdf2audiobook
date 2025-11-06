import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from main import app


@pytest.fixture
def client():
    # Create a limiter with in-memory storage for testing
    test_limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"], storage_uri="memory://")

    # Add a test route with rate limiting
    @app.get("/test-rate-limit")
    @test_limiter.limit("5/minute")
    def test_rate_limit(request: Request):
        return {"message": "Rate limited endpoint"}

    yield TestClient(app)

    # Remove the test route
    app.routes[:] = [route for route in app.routes if getattr(route, 'path', None) != '/test-rate-limit']


def test_rate_limiting_middleware(client):
    # Arrange
    headers = {"User-Agent": "pytest"}

    # Act & Assert - make 5 requests (should all succeed)
    for i in range(5):
        response = client.get("/test-rate-limit", headers=headers)
        assert response.status_code == 200

    # 6th request should be rate limited
    response = client.get("/test-rate-limit", headers=headers)
    assert response.status_code == 429
