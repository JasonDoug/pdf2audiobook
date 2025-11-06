import pytest
from unittest.mock import patch, MagicMock

from worker.tasks import process_pdf_task
from app.models import Job, JobStatus


@patch("worker.tasks.PDFToAudioPipeline")
@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
def test_process_pdf_task_success(
    MockSessionLocal, MockJobService, MockStorageService, MockPDFToAudioPipeline
):
    # Arrange
    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db

    mock_job_service = MockJobService.return_value
    mock_storage_service = MockStorageService.return_value
    mock_pipeline = MockPDFToAudioPipeline.return_value

    job = Job(
        id=1,
        pdf_s3_key="test.pdf",
        voice_provider="openai",
        voice_type="default",
        reading_speed=1.0,
        include_summary=False,
        user_id=1,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = job
    mock_storage_service.download_file.return_value = b"pdf content"
    mock_pipeline.process_pdf.return_value = b"audio data"
    mock_storage_service.upload_file_data.return_value = "http://s3.com/audio.mp3"

    # Act
    result = process_pdf_task(1)

    # Assert
    assert result["status"] == "completed"
    mock_job_service.update_job_status.assert_any_call(1, JobStatus.PROCESSING, 0)
    mock_job_service.update_job_status.assert_any_call(1, JobStatus.COMPLETED, 100)
    mock_storage_service.download_file.assert_called_with("test.pdf")
    mock_pipeline.process_pdf.assert_called_once()
    mock_storage_service.upload_file_data.assert_called_with(
        b"audio data", "audio/1/1.mp3", "audio/mpeg"
    )


from datetime import datetime, timedelta
from worker.tasks import cleanup_old_files


@patch("worker.tasks.StorageService")
@patch("worker.tasks.SessionLocal")
def test_cleanup_old_files(MockSessionLocal, MockStorageService):
    # Arrange
    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db
    mock_storage_service = MockStorageService.return_value

    old_job = Job(
        id=1,
        pdf_s3_key="old.pdf",
        audio_s3_key="old.mp3",
        status=JobStatus.COMPLETED,
        completed_at=datetime.now() - timedelta(days=31),
    )
    new_job = Job(
        id=2,
        pdf_s3_key="new.pdf",
        audio_s3_key="new.mp3",
        status=JobStatus.COMPLETED,
        completed_at=datetime.now() - timedelta(days=1),
    )
    mock_db.query.return_value.filter.return_value.all.return_value = [old_job]

    # Act
    result = cleanup_old_files()

    # Assert
    assert result == "Cleaned up 1 old jobs"
    mock_storage_service.delete_file.assert_any_call("old.pdf")
    mock_storage_service.delete_file.assert_any_call("old.mp3")
    mock_db.delete.assert_called_with(old_job)
    mock_db.commit.assert_called_once()
