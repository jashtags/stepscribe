from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    error = "error"


class Step(BaseModel):
    n: int
    text: str
    start: float


class VideoMeta(BaseModel):
    title: str
    platform: str
    duration: Optional[float] = None
    video_id: str


class Job(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.queued
    stage: str = "Queued"
    progress: int = 0
    steps: Optional[list[Step]] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    video: Optional[VideoMeta] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubmitRequest(BaseModel):
    url: str


class SubmitResponse(BaseModel):
    job_id: str
