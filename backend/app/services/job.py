from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import Job, User, JobStatus
from app.schemas import JobCreate, JobUpdate


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self, user_id: int, job_data: JobCreate, pdf_s3_key: str, pdf_s3_url: str
    ) -> Job:
        job = Job(
            user_id=user_id,
            original_filename=job_data.original_filename,
            pdf_s3_key=pdf_s3_key,
            pdf_s3_url=pdf_s3_url,
            voice_provider=job_data.voice_provider,
            voice_type=job_data.voice_type,
            reading_speed=job_data.reading_speed,
            include_summary=job_data.include_summary,
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_user_job(self, user_id: int, job_id: int) -> Optional[Job]:
        return (
            self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        )

    def get_user_jobs(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Job]:
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_job(self, job_id: int, job_update: dict) -> Optional[Job]:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        for field, value in job_update.items():
            setattr(job, field, value)

        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_status(
        self,
        job_id: int,
        status: JobStatus,
        progress: int = None,
        error_message: str = None,
    ):
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        job.status = status

        if progress is not None:
            job.progress_percentage = progress

        if error_message is not None:
            job.error_message = error_message

        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.now()
        elif status == JobStatus.COMPLETED:
            job.completed_at = datetime.now()
            job.progress_percentage = 100

        self.db.commit()
        self.db.refresh(job)
        return job

    def can_user_create_job(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Check subscription limits
        if user.subscription_tier.value == "free":
            # Free tier: 2 jobs per month
            monthly_jobs = (
                self.db.query(Job)
                .filter(
                    Job.user_id == user_id,
                    Job.created_at >= datetime.now().replace(day=1),
                )
                .count()
            )
            return monthly_jobs < 2

        elif user.subscription_tier.value == "pro":
            # Pro tier: 50 jobs per month
            monthly_jobs = (
                self.db.query(Job)
                .filter(
                    Job.user_id == user_id,
                    Job.created_at >= datetime.now().replace(day=1),
                )
                .count()
            )
            return monthly_jobs < 50

        elif user.subscription_tier.value == "enterprise":
            # Enterprise: unlimited
            return True

        # Check one-time credits
        if user.one_time_credits > 0:
            return True

        return False

    def consume_credit(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        if user.one_time_credits > 0:
            user.one_time_credits -= 1
            self.db.commit()
            return True

        return False
