import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
