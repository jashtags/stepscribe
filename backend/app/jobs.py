import uuid
from datetime import datetime
from typing import Dict, Optional

from .models import Job, JobStatus

_jobs: Dict[str, Job] = {}


def create_job(url: str) -> Job:
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, status=JobStatus.queued, stage="Queued", created_at=datetime.utcnow())
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    if job_id in _jobs:
        job = _jobs[job_id]
        for key, value in kwargs.items():
            setattr(job, key, value)


def all_jobs() -> list[Job]:
    return list(_jobs.values())


async def run_job_background(job_id: str, url: str) -> None:
    from .pipeline.orchestrator import run_pipeline
    from .config import get_settings

    config = get_settings()
    update_job(job_id, status=JobStatus.processing)
    await run_pipeline(job_id, url, config)
