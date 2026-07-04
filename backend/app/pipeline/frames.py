import asyncio
import json
import re
from pathlib import Path


async def _get_duration(video_filepath: Path) -> float:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(video_filepath),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    try:
        info = json.loads(stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception:
        return 300.0


async def _scene_detect(video_filepath: Path, frames_dir: Path, threshold: float) -> list[dict]:
    output_pattern = str(frames_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", str(video_filepath),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr",
        "-q:v", "2",
        output_pattern,
        "-y",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()

    stderr_text = stderr.decode("utf-8", errors="replace")
    timestamps = [float(m.group(1)) for m in re.finditer(r"pts_time:(\d+\.?\d*)", stderr_text)]

    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    result = []
    for i, frame_file in enumerate(frame_files):
        ts = timestamps[i] if i < len(timestamps) else i * 5.0
        result.append({"timestamp": ts, "path": str(frame_file)})

    return sorted(result, key=lambda x: x["timestamp"])


async def _fixed_interval(video_filepath: Path, frames_dir: Path, max_frames: int) -> list[dict]:
    duration = await _get_duration(video_filepath)
    interval = max(duration / max_frames, 5.0)

    cmd = [
        "ffmpeg", "-i", str(video_filepath),
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        str(frames_dir / "frame_%04d.jpg"),
        "-y",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    return [{"timestamp": i * interval, "path": str(f)} for i, f in enumerate(frame_files)]


async def extract_keyframes(
    video_filepath: Path,
    job_dir: Path,
    max_frames: int,
    scene_threshold: float,
) -> list[dict]:
    """Returns [{timestamp: float, path: str}] sorted by timestamp."""
    frames_dir = job_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    frames = await _scene_detect(video_filepath, frames_dir, scene_threshold)

    if len(frames) < 5:
        frames = await _fixed_interval(video_filepath, frames_dir, max_frames)

    frames = frames[:max_frames]

    manifest_path = job_dir / "timestamps.json"
    manifest_path.write_text(json.dumps(frames, indent=2))

    return frames
