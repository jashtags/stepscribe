import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .config import get_settings
from .jobs import all_jobs, create_job, get_job, run_job_background
from .models import Job, SubmitRequest, SubmitResponse

app = FastAPI(title="StepScribe API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/jobs", response_model=SubmitResponse, status_code=201)
async def submit_job(request: SubmitRequest):
    job = create_job(request.url)
    asyncio.create_task(run_job_background(job.job_id, request.url))
    return SubmitResponse(job_id=job.job_id)


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/jobs", response_model=list[Job])
async def list_jobs():
    return all_jobs()


@app.post("/api/jobs/{job_id}/skill", response_class=PlainTextResponse)
async def generate_skill(job_id: str):
    """Generate a SKILL.md file from a completed job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status.value != "done":
        raise HTTPException(status_code=400, detail="Job must be completed before generating a skill file.")
    if not job.steps:
        raise HTTPException(status_code=400, detail="No steps available to generate a skill from.")

    from .pipeline.skill_generator import generate_skill_file

    config = get_settings()
    job_data = {
        "summary": job.summary or "",
        "tools": [],
        "steps": [{"n": s.n, "text": s.text, "start": s.start} for s in job.steps],
    }
    video_meta = {}
    if job.video:
        video_meta = {
            "title": job.video.title,
            "platform": job.video.platform,
            "video_id": job.video.video_id,
        }

    skill_md = await generate_skill_file(job_data, video_meta, config)
    return PlainTextResponse(content=skill_md, media_type="text/markdown")
