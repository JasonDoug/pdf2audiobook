from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_logging_middleware(client):
    # Arrange
    headers = {"User-Agent": "pytest"}

    # Act & Assert
    with patch('main.logger') as mock_logger:
        response = client.get("/", headers=headers)

        assert response.status_code == 200
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert '"GET /" 200' in log_message
