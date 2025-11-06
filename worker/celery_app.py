from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Create Celery app
celery_app = Celery(
    "pdf2audiobook_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["worker.tasks"],
)

from celery.schedules import crontab

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic Task Schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "worker.tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM UTC
    },
}


# Optional: Set up logging
@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    print(f"Task {task_id} ({task.name}) started")


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwds,
):
    print(f"Task {task_id} ({task.name}) finished with state: {state}")


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds
):
    print(f"Task {task_id} failed: {exception}")


if __name__ == "__main__":
    celery_app.start()
