from celery import Celery
from .celery_app import celery_app
import os
import sys
import tempfile
from typing import Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal, engine
from app.models import Job, JobStatus
from app.services.storage import StorageService
from app.services.job import JobService
from app.core.config import settings

# Import PDF processing pipeline

from .pdf_pipeline import PDFToAudioPipeline

pipeline = PDFToAudioPipeline()


@celery_app.task(bind=True)
def process_pdf_task(self, job_id: int):
    """
    Process a PDF file and convert it to audio
    """
    db = SessionLocal()
    storage_service = StorageService()
    job_service = JobService(db)

    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job status to processing
        job_service.update_job_status(job_id, JobStatus.PROCESSING, 0)

        # Download PDF from S3
        pdf_data = storage_service.download_file(job.pdf_s3_key)

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_file.write(pdf_data)
            pdf_path = pdf_file.name

        # Process PDF
        audio_data = pipeline.process_pdf(
            pdf_path=pdf_path,
            voice_provider=job.voice_provider.value,
            voice_type=job.voice_type,
            reading_speed=float(job.reading_speed),
            include_summary=job.include_summary,
            progress_callback=lambda progress: job_service.update_job_status(
                job_id, JobStatus.PROCESSING, progress
            ),
        )

        # Upload audio to S3
        audio_key = f"audio/{job.user_id}/{job.id}.mp3"
        audio_url = storage_service.upload_file_data(
            audio_data, audio_key, "audio/mpeg"
        )

        # Update job with completion
        job.audio_s3_key = audio_key
        job.audio_s3_url = audio_url
        job_service.update_job_status(job_id, JobStatus.COMPLETED, 100)

        # Clean up temporary file
        os.unlink(pdf_path)

        return {"status": "completed", "job_id": job_id, "audio_url": audio_url}

    except Exception as e:
        # Update job with error
        error_message = str(e)
        job_service.update_job_status(
            job_id, JobStatus.FAILED, error_message=error_message
        )

        # Clean up temporary file if it exists
        if "pdf_path" in locals():
            try:
                os.unlink(pdf_path)
            except:
                pass

        # Re-raise exception for Celery to handle
        raise self.retry(exc=e, countdown=60, max_retries=3)

    finally:
        db.close()


@celery_app.task
def cleanup_old_files():
    """
    Clean up old temporary files and completed jobs older than 30 days
    """
    db = SessionLocal()

    try:
        # Find old completed jobs
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=30)

        old_jobs = (
            db.query(Job)
            .filter(Job.status == JobStatus.COMPLETED, Job.completed_at < cutoff_date)
            .all()
        )

        storage_service = StorageService()

        for job in old_jobs:
            # Delete files from S3
            if job.pdf_s3_key:
                storage_service.delete_file(job.pdf_s3_key)
            if job.audio_s3_key:
                storage_service.delete_file(job.audio_s3_key)

            # Delete job record
            db.delete(job)

        db.commit()
        return f"Cleaned up {len(old_jobs)} old jobs"

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
