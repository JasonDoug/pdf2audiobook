import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.models import Job, User, JobStatus
from app.core.database import get_db
from app.services.auth import get_current_user


# Fixtures
@pytest.fixture
def mock_user():
    return User(id=1, email="test@test.com")


@pytest.fixture
def client(db_session, mock_user):
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return mock_user

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield TestClient(app)

    app.dependency_overrides.clear()


# Tests
def test_create_job_success(client: TestClient, db_session):
    with (
        patch(
            "app.services.storage.StorageService.upload_file",
            return_value="http://s3.com/test.pdf",
        ),
        patch("worker.tasks.process_pdf_task.delay") as mock_delay,
    ):
        response = client.post(
            "/api/v1/jobs/",
            files={"file": ("test.pdf", b"pdf content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["status"] == "pending"
        mock_delay.assert_called_once_with(data["id"])


def test_get_job_by_id(client: TestClient, db_session, mock_user):
    job = Job(id=1, original_filename="test.pdf", user_id=mock_user.id)
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
