import shutil
from pathlib import Path

from ..jobs import update_job
from ..models import JobStatus, Step, VideoMeta
from .download import download_video
from .frames import extract_keyframes
from .platform import detect_platform
from .synthesize import synthesize_steps
from .transcribe import get_transcript


async def run_pipeline(job_id: str, url: str, config) -> None:
    """Run all 7 pipeline stages, updating job status after each."""
    media_dir = Path(config.MEDIA_DIR)
    job_dir = media_dir / job_id

    try:
        # Stage 1 — platform detection
        update_job(job_id, stage="Detecting platform…", progress=5)
        detect_platform(url)

        # Stage 2 — download
        update_job(job_id, stage="Downloading video…", progress=15)
        meta = await download_video(url, job_dir)
        update_job(
            job_id,
            video=VideoMeta(
                title=meta["title"],
                platform=meta["platform"],
                duration=meta["duration"],
                video_id=meta["video_id"],
            ),
            progress=30,
        )

        # Stage 3 — transcript
        update_job(job_id, stage="Transcribing audio…", progress=35)
        transcript = await get_transcript(
            job_dir,
            Path(meta["filepath"]),
            config.WHISPER_MODEL,
        )

        # Stage 4 — keyframes
        update_job(job_id, stage="Extracting keyframes…", progress=55)
        frames = await extract_keyframes(
            Path(meta["filepath"]),
            job_dir,
            config.MAX_KEYFRAMES,
            config.SCENE_THRESHOLD,
        )

        # Stage 5 — OCR (optional)
        if config.ENABLE_OCR:
            update_job(job_id, stage="Reading on-screen text…", progress=65)
            from .ocr import extract_text_from_frames

            frames = await extract_text_from_frames(frames)

        # Stage 6 — LLM synthesis
        update_job(job_id, stage="Writing steps…", progress=80)
        result = await synthesize_steps(transcript, frames, config)

        # Stage 7 — done
        steps = [Step(n=s["n"], text=s["text"], start=s["start"]) for s in result["steps"]]
        update_job(
            job_id,
            status=JobStatus.done,
            stage="Done",
            progress=100,
            steps=steps,
            summary=result.get("summary", ""),
        )

        # Cleanup
        if config.CLEANUP_AFTER_SUCCESS and job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)

    except Exception as e:
        update_job(
            job_id,
            status=JobStatus.error,
            stage="Error",
            error=str(e),
            progress=0,
        )
