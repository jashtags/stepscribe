import asyncio
from pathlib import Path

import yt_dlp


async def download_video(url: str, job_dir: Path) -> dict:
    """Download video + metadata using yt-dlp Python API.

    Returns dict with: title, duration, video_id, platform, filepath, subtitle_files.
    """
    job_dir.mkdir(parents=True, exist_ok=True)
    video_path = job_dir / "video.mp4"

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(video_path),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "vtt",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                return info
            except yt_dlp.utils.DownloadError as e:
                error_str = str(e).lower()
                if any(word in error_str for word in ("login", "private", "authentication", "sign in")):
                    raise ValueError(
                        "This video is private or login-required — StepScribe only works with public videos."
                    )
                raise ValueError(f"Download failed: {e}")

    info = await loop.run_in_executor(None, _download)

    subtitle_files = list(job_dir.glob("*.vtt")) + list(job_dir.glob("*.srt"))
    platform = "instagram" if "instagram" in url else "youtube"

    return {
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration"),
        "video_id": info.get("id", "unknown"),
        "platform": platform,
        "filepath": str(video_path),
        "subtitle_files": [str(f) for f in subtitle_files],
    }
