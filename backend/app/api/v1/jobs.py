from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.schemas import Job, JobCreate, JobUpdate, JobStatus, VoiceProvider, ConversionMode, User
from app.services.auth import get_current_user
from app.services.job import JobService
from app.services.storage import StorageService
try:
    from worker.tasks import process_pdf_task
except ImportError:
    # Mock for testing
    process_pdf_task = None

router = APIRouter()


@router.post(
    "/",
    response_model=Job,
    summary="Create a New PDF Conversion Job",
    description="Upload a PDF file and create a new job to convert it into an audiobook. This endpoint accepts multipart/form-data.",
)
async def create_job(
    file: UploadFile = File(..., description="The PDF file to be converted."),
    voice_provider: VoiceProvider = Form(
        VoiceProvider.OPENAI,
        description="The TTS provider to use. See schema for available providers.",
    ),
    voice_type: str = Form(
        "default",
        description="The specific voice to use from the selected provider (e.g., 'alloy', 'nova').",
    ),
    reading_speed: float = Form(
        1.0, description="Adjust the reading speed (0.5 to 2.0)."
    ),
    include_summary: bool = Form(
        False, description="Prepend the audiobook with an AI-generated summary."
    ),
    conversion_mode: ConversionMode = Form(
        ConversionMode.FULL, description="Conversion mode: 'full' for word-for-word or 'summary_explanation' for core concepts explanation."
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Security: Validate file upload
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename"
        )

    # Check file extension
    allowed_extensions = {'.pdf'}
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if f'.{file_extension}' not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    # Check content type
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )

    # Check file size using configuration
    file_content = await file.read()
    if len(file_content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Reset file pointer for storage service
    await file.seek(0)
    """
    Creates a new job by uploading a PDF and specifying conversion options.

    - **file**: The PDF document to process.
    - **voice_provider**: The TTS service to use.
    - **voice_type**: The desired voice from the provider.
    - **reading_speed**: Audiobook reading speed.
    - **include_summary**: If true, an AI summary is added to the start.

    The endpoint first validates the user's credits, uploads the file to S3, creates a job record in the database, and finally queues a background task to perform the conversion.
    """
    job_service = JobService(db)
    if not job_service.can_user_create_job(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits or subscription limit reached",
        )

    storage_service = StorageService()
    pdf_s3_key = f"pdfs/{current_user.id}/{file.filename}"
    pdf_s3_url = await storage_service.upload_file(file, pdf_s3_key)

    job_data = JobCreate(
        original_filename=file.filename or "unknown.pdf",
        voice_provider=voice_provider,
        voice_type=voice_type,
        reading_speed=reading_speed,
        include_summary=include_summary,
        conversion_mode=conversion_mode,
    )
    job = job_service.create_job(current_user.id, job_data, pdf_s3_key, pdf_s3_url)

    if process_pdf_task and hasattr(process_pdf_task, 'delay'):
        process_pdf_task.delay(job.id)

    return job


@router.get(
    "/",
    response_model=List[Job],
    summary="List All Jobs for Current User",
    description="Retrieves a paginated list of all PDF conversion jobs created by the currently authenticated user.",
)
async def get_user_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """
    Fetches a list of jobs for the current user.

    - **skip**: Number of jobs to skip for pagination.
    - **limit**: Maximum number of jobs to return.
    """
    job_service = JobService(db)
    return job_service.get_user_jobs(current_user.id, skip=skip, limit=limit)


@router.get(
    "/{job_id}",
    response_model=Job,
    summary="Get Job by ID",
    description="Retrieves the full details of a specific job by its ID. The user must own the job.",
)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches a single job by its unique ID.

    - **job_id**: The ID of the job to retrieve.
    """
    job_service = JobService(db)
    job = job_service.get_user_job(current_user.id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


@router.patch(
    "/{job_id}",
    response_model=Job,
    summary="Manually Update a Job (for Testing)",
    description="Allows for manual update of a job's attributes. This endpoint is intended for testing and simulation of the worker process.",
)
async def update_job_manual(
    job_id: int,
    job_update: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually updates a job's status, progress, or error message.

    - **job_id**: The ID of the job to update.
    - **job_update**: A JSON body with the fields to update.
    """
    job_service = JobService(db)
    job = job_service.get_user_job(current_user.id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return job_service.update_job(job_id, job_update.model_dump(exclude_unset=True))


@router.get(
    "/{job_id}/status",
    summary="Get Job Status",
    description="Retrieves the current status, progress, and result of a specific job. This is a lightweight endpoint for polling.",
)
async def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Provides a quick way to check the status of a job without fetching all its details.

    - **job_id**: The ID of the job to check.

    Returns the status, progress percentage, and the final audio URL if completed.
    """
    job_service = JobService(db)
    job = job_service.get_user_job(current_user.id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percentage": job.progress_percentage,
        "error_message": job.error_message,
        "audio_url": job.audio_s3_url if job.status.value == "completed" else None,
    }
