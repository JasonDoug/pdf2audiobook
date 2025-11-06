import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.models import Job, User, JobStatus
from app.core.database import get_db
from app.services.auth import get_current_user
from app.services.storage import StorageService


# Fixtures
@pytest.fixture
def mock_user():
    return User(id=1, email="test@test.com")





# Tests
def test_create_job_success(client: TestClient, db_session):
    with (
        patch.object(
            StorageService, "upload_file",
            return_value="http://s3.com/test.pdf",
        ),
        patch("app.api.v1.jobs.process_pdf_task") as mock_task,
    ):
        response = client.post(
            "/api/v1/jobs/",
            data={"voice_provider": "openai", "voice_type": "default", "reading_speed": "1.0", "include_summary": "false", "conversion_mode": "full"},
            files={"file": ("test.pdf", b"pdf content", "application/pdf")},
            headers={"Authorization": "Bearer dev-secret-key-for-testing-only"},
        )
        if response.status_code != 200:
            print(f"Response body: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(data["id"])


def test_get_job_by_id(client: TestClient, db_session, mock_user):
    job = Job(id=1, original_filename="test.pdf", pdf_s3_key="test.pdf", user_id=mock_user.id)
    db_session.add(job)
    db_session.commit()

    response = client.get("/api/v1/jobs/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_job_manual(client: TestClient, db_session, mock_user):
    # 1. Create a job first
    job = Job(
        id=1,
        original_filename="test.pdf",
        pdf_s3_key="test.pdf",
        user_id=mock_user.id,
        status=JobStatus.PENDING,
        progress_percentage=0,
    )
    db_session.add(job)
    db_session.commit()

    # 2. Now, update it
    update_data = {"status": "processing", "progress_percentage": 50}
    response = client.patch("/api/v1/jobs/1", json=update_data)

    # 3. Assert the update was successful
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress_percentage"] == 50

    # 4. Verify the data in the DB
    updated_job = db_session.query(Job).filter(Job.id == 1).first()
    assert updated_job.status == JobStatus.PROCESSING
    assert updated_job.progress_percentage == 50


def test_get_job_status(client: TestClient, db_session, mock_user):
    job = Job(
        id=1,
        original_filename="test.pdf",
        pdf_s3_key="test.pdf",
        user_id=mock_user.id,
        status=JobStatus.COMPLETED,
        progress_percentage=100,
        audio_s3_url="http://s3.com/audio.mp3",
    )
    db_session.add(job)
    db_session.commit()

    response = client.get("/api/v1/jobs/1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == 1
    assert data["status"] == "completed"
    assert data["progress_percentage"] == 100
    assert data["audio_url"] == "http://s3.com/audio.mp3"
