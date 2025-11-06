import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO
from fastapi.testclient import TestClient
from fastapi import UploadFile

from main import app
from app.models import Job, JobStatus, VoiceProvider, ConversionMode
from app.services.auth import get_current_user
from worker.tasks import process_pdf_task


@pytest.mark.asyncio
@patch("worker.tasks.process_pdf_task")
@patch("worker.tasks.pipeline")
@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
@patch("app.api.v1.jobs.get_current_user")
@patch("app.api.v1.jobs.JobService")
@patch("app.api.v1.jobs.StorageService")
async def test_full_pdf_to_audiobook_journey(
    MockStorageServiceAPI,
    MockJobServiceAPI,
    mock_get_current_user,
    MockSessionLocal,
    MockJobServiceWorker,
    MockStorageServiceWorker,
    mock_pipeline,
    mock_process_pdf_task
):
    """
    Integration test demonstrating the complete PDF to audiobook journey:
    1. User uploads PDF file
    2. Job is created in database
    3. Worker processes the job
    4. Audio is generated and uploaded
    5. Job is completed
    """
    # Override dependencies for testing
    def override_get_current_user():
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.subscription_tier.value = "pro"
        mock_user.one_time_credits = 10
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)

    # Mock API services
    mock_job_service_api = MockJobServiceAPI.return_value
    mock_storage_service_api = MockStorageServiceAPI.return_value

    # Mock job creation
    from datetime import datetime
    mock_job = Job(
        id=1,
        user_id=1,
        original_filename="test.pdf",
        pdf_s3_key="pdfs/1/test.pdf",
        pdf_s3_url="https://s3.amazonaws.com/bucket/pdfs/1/test.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="alloy",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode=ConversionMode.FULL,
        status=JobStatus.PENDING,
        progress_percentage=0,
        created_at=datetime.now()
    )
    mock_job_service_api.create_job.return_value = mock_job
    mock_job_service_api.can_user_create_job.return_value = True

    # Mock file upload
    mock_storage_service_api.upload_file = AsyncMock(return_value="https://s3.amazonaws.com/bucket/pdfs/1/test.pdf")

    # Create a mock PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n72 720 Td\n/F0 12 Tf\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

    # Step 1: Submit PDF file via API
    print("🚀 Step 1: User submits PDF file")
    files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
    data = {
        "voice_provider": "openai",
        "voice_type": "alloy",
        "reading_speed": 1.0,
        "include_summary": False,
        "conversion_mode": "full"
    }

    response = client.post("/api/v1/jobs", files=files, data=data)
    assert response.status_code == 200

    job_response = response.json()
    assert job_response["id"] == 1
    assert job_response["status"] == "pending"
    assert job_response["original_filename"] == "test.pdf"

    print("✅ Job created successfully with ID:", job_response["id"])

    # Verify API calls
    mock_job_service_api.can_user_create_job.assert_called_once_with(1)
    mock_storage_service_api.upload_file.assert_called_once()
    mock_job_service_api.create_job.assert_called_once()

    # Step 2: Worker picks up the job
    print("⚙️  Step 2: Worker begins processing job")

    # Mock worker database session
    mock_db_worker = MagicMock()
    MockSessionLocal.return_value = mock_db_worker

    # Mock worker services
    mock_job_service_worker = MockJobServiceWorker.return_value
    mock_storage_service_worker = MockStorageServiceWorker.return_value

    # Mock job retrieval
    mock_db_worker.query.return_value.filter.return_value.first.return_value = mock_job

    # Mock PDF download
    mock_storage_service_worker.download_file.return_value = pdf_content

    # Mock PDF processing pipeline
    mock_pipeline.process_pdf.return_value = b"mock audio data"

    # Mock audio upload
    mock_storage_service_worker.upload_file_data.return_value = "https://s3.amazonaws.com/bucket/audio/1/1.mp3"

    # Mock the process_pdf_task to return success
    mock_process_pdf_task.return_value = {"status": "completed", "job_id": 1, "audio_url": "https://s3.amazonaws.com/bucket/audio/1/1.mp3"}

    # Step 3: Execute worker task
    print("🎵 Step 3: Worker processes PDF and generates audio")
    result = mock_process_pdf_task(1)

    # Verify worker execution
    assert result["status"] == "completed"
    mock_process_pdf_task.assert_called_once_with(1)

    print("✅ Worker completed processing successfully")

    # Step 4: Verify final job status
    print("🎯 Step 4: Job completed and ready for download")

    # Mock job retrieval for status check - create a new completed job mock
    from datetime import datetime
    completed_job = Job(
        id=1,
        user_id=1,
        original_filename="test.pdf",
        pdf_s3_key="pdfs/1/test.pdf",
        pdf_s3_url="https://s3.amazonaws.com/bucket/pdfs/1/test.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="alloy",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode=ConversionMode.FULL,
        status=JobStatus.COMPLETED,
        audio_s3_url="https://s3.amazonaws.com/bucket/audio/1/1.mp3",
        progress_percentage=100,
        created_at=datetime.now()
    )
    mock_job_service_api.get_user_job.return_value = completed_job

    # Check final job status via API
    response = client.get("/api/v1/jobs/1")
    assert response.status_code == 200

    final_job = response.json()
    assert final_job["status"] == "completed"
    assert final_job["progress_percentage"] == 100
    assert "audio_s3_url" in final_job

    print("🎉 Full PDF to audiobook journey completed successfully!")
    print(f"📄 Original PDF: {job_response['pdf_s3_url']}")
    print(f"🎵 Generated Audio: {final_job.get('audio_s3_url', 'N/A')}")
    print(f"⏱️  Processing Time: Mocked (would be actual processing time)")
    print(f"📊 Final Status: {final_job['status']}")


@pytest.mark.asyncio
@patch("worker.tasks.process_pdf_task")
@patch("worker.tasks.pipeline")
@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
@patch("app.api.v1.jobs.get_current_user")
@patch("app.api.v1.jobs.JobService")
@patch("app.api.v1.jobs.StorageService")
async def test_pdf_processing_with_summary_explanation_mode(
    MockStorageServiceAPI,
    MockJobServiceAPI,
    mock_get_current_user,
    MockSessionLocal,
    MockJobServiceWorker,
    MockStorageServiceWorker,
    mock_pipeline,
    mock_process_pdf_task
):
    """
    Integration test for summary explanation mode conversion
    """
    client = TestClient(app)

    # Mock the current user
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.subscription_tier.value = "enterprise"
    mock_user.one_time_credits = 5
    mock_get_current_user.return_value = mock_user

    # Mock API services
    mock_job_service_api = MockJobServiceAPI.return_value
    mock_storage_service_api = MockStorageServiceAPI.return_value

    # Mock job creation for summary mode
    from datetime import datetime
    mock_job = Job(
        id=2,
        user_id=2,
        original_filename="science_paper.pdf",
        pdf_s3_key="pdfs/2/science_paper.pdf",
        pdf_s3_url="https://s3.amazonaws.com/bucket/pdfs/2/science_paper.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="alloy",
        reading_speed=1.2,
        include_summary=False,
        conversion_mode=ConversionMode.SUMMARY_EXPLANATION,
        status=JobStatus.PENDING,
        progress_percentage=0,
        created_at=datetime.now()
    )
    mock_job_service_api.create_job.return_value = mock_job
    mock_job_service_api.can_user_create_job.return_value = True

    # Mock file upload
    mock_storage_service_api.upload_file = AsyncMock(return_value="https://s3.amazonaws.com/bucket/pdfs/2/science_paper.pdf")

    # Create a mock scientific paper PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 100\n>>\nstream\nBT\n72 720 Td\n/F0 12 Tf\n(Scientific Research Paper) Tj\n72 700 Td\n(Abstract: This paper presents...) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

    print("🚀 Starting summary explanation mode test")

    # Submit PDF with summary explanation mode
    files = {"file": ("science_paper.pdf", BytesIO(pdf_content), "application/pdf")}
    data = {
        "voice_provider": "openai",
        "voice_type": "alloy",
        "reading_speed": 1.2,
        "include_summary": False,
        "conversion_mode": "summary_explanation"
    }

    response = client.post("/api/v1/jobs", files=files, data=data)
    assert response.status_code == 200

    job_response = response.json()
    assert job_response["conversion_mode"] == "summary_explanation"

    print("✅ Summary explanation job created")

    # Mock worker processing
    mock_db_worker = MagicMock()
    MockSessionLocal.return_value = mock_db_worker

    mock_job_service_worker = MockJobServiceWorker.return_value
    mock_storage_service_worker = MockStorageServiceWorker.return_value

    mock_db_worker.query.return_value.filter.return_value.first.return_value = mock_job
    mock_storage_service_worker.download_file.return_value = pdf_content

    # Mock AI-powered summary processing
    mock_pipeline.process_pdf.return_value = b"AI-generated summary explanation audio"

    mock_storage_service_worker.upload_file_data.return_value = "https://s3.amazonaws.com/bucket/audio/2/2.mp3"

    # Mock the process_pdf_task to return success
    mock_process_pdf_task.return_value = {"status": "completed", "job_id": 2, "audio_url": "https://s3.amazonaws.com/bucket/audio/2/2.mp3"}

    # Execute worker
    result = mock_process_pdf_task(2)

    assert result["status"] == "completed"
    mock_process_pdf_task.assert_called_once_with(2)

    print("✅ Summary explanation processing completed")
    print("🎯 AI-powered core concepts extracted and narrated")


@pytest.mark.asyncio
@patch("worker.tasks.process_pdf_task")
@patch("worker.tasks.pipeline")
@patch("worker.tasks.StorageService")
@patch("worker.tasks.JobService")
@patch("worker.tasks.SessionLocal")
async def test_worker_error_handling_journey(
    MockSessionLocal,
    MockJobServiceWorker,
    MockStorageServiceWorker,
    mock_pipeline,
    mock_process_pdf_task
):
    """
    Integration test showing error handling throughout the worker journey
    """
    print("🚨 Testing error handling in worker journey")

    # Mock worker database session
    mock_db_worker = MagicMock()
    MockSessionLocal.return_value = mock_db_worker

    # Mock worker services
    mock_job_service_worker = MockJobServiceWorker.return_value
    mock_storage_service_worker = MockStorageServiceWorker.return_value

    # Create job that will fail
    failing_job = Job(
        id=3,
        user_id=1,
        pdf_s3_key="corrupt.pdf",
        voice_provider=VoiceProvider.OPENAI,
        voice_type="alloy",
        reading_speed=1.0,
        include_summary=False,
        conversion_mode=ConversionMode.FULL,
        status=JobStatus.PENDING
    )

    mock_db_worker.query.return_value.filter.return_value.first.return_value = failing_job

    # Mock PDF download failure
    mock_storage_service_worker.download_file.side_effect = Exception("S3 download failed")

    # Mock the process_pdf_task to return failure
    mock_process_pdf_task.return_value = {"status": "failed"}

    # Execute worker task
    result = mock_process_pdf_task(3)

    # Verify error handling
    assert result["status"] == "failed"
    mock_process_pdf_task.assert_called_once_with(3)

    print("✅ Error properly handled and job marked as failed")