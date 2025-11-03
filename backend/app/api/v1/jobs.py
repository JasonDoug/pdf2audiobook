from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas import Job, JobCreate, JobUpdate, JobStatus
from app.services.auth import get_current_user
from app.services.job import JobService
from app.services.storage import StorageService
from worker.tasks import process_pdf_task

router = APIRouter()


@router.post("/", response_model=Job)
async def create_job(
    file: UploadFile = File(...),
    voice_provider: str = Form("openai"),
    voice_type: str = Form("default"),
    reading_speed: float = Form(1.0),
    include_summary: bool = Form(False),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check user credits/subscription
    job_service = JobService(db)
    if not job_service.can_user_create_job(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits or subscription limit reached",
        )

    # Upload file to S3
    storage_service = StorageService()
    pdf_s3_key = f"pdfs/{current_user.id}/{file.filename}"
    pdf_s3_url = await storage_service.upload_file(file, pdf_s3_key)

    # Create job record
    job_data = JobCreate(
        original_filename=file.filename,
        voice_provider=voice_provider,
        voice_type=voice_type,
        reading_speed=reading_speed,
        include_summary=include_summary,
    )
    job = job_service.create_job(current_user.id, job_data, pdf_s3_key, pdf_s3_url)

    # Queue processing task
    process_pdf_task.delay(job.id)

    return job


@router.get("/", response_model=List[Job])
async def get_user_jobs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    job_service = JobService(db)
    return job_service.get_user_jobs(current_user.id, skip=skip, limit=limit)


@router.get("/{job_id}", response_model=Job)
async def get_job(
    job_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    job_service = JobService(db)
    job = job_service.get_user_job(current_user.id, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
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
        "audio_url": job.audio_s3_url if job.status == JobStatus.COMPLETED else None,
    }
