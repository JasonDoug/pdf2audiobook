import pytest
from unittest.mock import patch, MagicMock, ANY

from worker.tasks import process_pdf_task
from app.models import Job, JobStatus, VoiceProvider, ConversionMode


@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
@patch("worker.tasks.pipeline")
def test_process_pdf_task_success(
    mock_pipeline, MockSessionLocal, MockJobService, MockStorageService
):
    # Arrange
    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db

    mock_job_service = MockJobService.return_value
    mock_storage_service = MockStorageService.return_value

    job = Job(
        id=1,
        pdf_s3_key="test.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="default",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode=ConversionMode.FULL,
        user_id=1,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = job
    mock_storage_service.download_file.return_value = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n72 720 Td\n/F0 12 Tf\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"
    mock_pipeline.process_pdf.return_value = b"audio data"
    mock_storage_service.upload_file_data.return_value = "http://s3.com/audio.mp3"

    # Act
    result = process_pdf_task(1)

    # Assert
    assert result["status"] == "completed"
    mock_job_service.update_job_status.assert_any_call(1, JobStatus.PROCESSING, 0)
    mock_job_service.update_job_status.assert_any_call(1, JobStatus.COMPLETED, 100)
    mock_storage_service.download_file.assert_called_with("test.pdf")
    mock_pipeline.process_pdf.assert_called_once_with(
        pdf_path=ANY,
        voice_provider="openai",
        voice_type="default",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode="full",
        progress_callback=ANY,
    )
    mock_storage_service.upload_file_data.assert_called_with(
        b"audio data", "audio/1/1.mp3", "audio/mpeg"
    )


@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
@patch("worker.tasks.pipeline")
def test_process_pdf_task_success_summary_explanation(
    mock_pipeline, MockSessionLocal, MockJobService, MockStorageService
):
    # Arrange
    mock_db = MagicMock()
    MockSessionLocal.return_value = mock_db

    mock_job_service = MockJobService.return_value
    mock_storage_service = MockStorageService.return_value

    job = Job(
        id=2,
        pdf_s3_key="science.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="default",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode=ConversionMode.SUMMARY_EXPLANATION,
        user_id=1,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = job
    mock_storage_service.download_file.return_value = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n72 720 Td\n/F0 12 Tf\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"
    mock_pipeline.process_pdf.return_value = b"summary audio data"
    mock_storage_service.upload_file_data.return_value = "http://s3.com/summary.mp3"

    # Act
    result = process_pdf_task(2)

    # Assert
    assert result["status"] == "completed"
    mock_job_service.update_job_status.assert_any_call(2, JobStatus.PROCESSING, 0)
    mock_job_service.update_job_status.assert_any_call(2, JobStatus.COMPLETED, 100)
    mock_storage_service.download_file.assert_called_with("science.pdf")
    mock_pipeline.process_pdf.assert_called_once_with(
        pdf_path=ANY,
        voice_provider="openai",
        voice_type="default",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode="summary_explanation",
        progress_callback=ANY,
    )
    mock_storage_service.upload_file_data.assert_called_with(
        b"summary audio data", "audio/1/2.mp3", "audio/mpeg"
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
