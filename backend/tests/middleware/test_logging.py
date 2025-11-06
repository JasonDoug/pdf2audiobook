import logging
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_logger():
    logger = logging.getLogger("api")
    logger.info = MagicMock()
    return logger


def test_logging_middleware(client, mock_logger):
    # Arrange
    headers = {"User-Agent": "pytest"}

    # Act
    response = client.get("/", headers=headers)

    # Assert
    assert response.status_code == 200
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert '"GET /" 200' in log_message
