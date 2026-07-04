import asyncio
import re
from pathlib import Path


def parse_vtt(path: str) -> list[dict]:
    """Parse WebVTT subtitle file into [{start, text}] list."""
    segments = []
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = content.strip().split("\n")
    i = 0
    while i < len(lines):
        if "-->" in lines[i]:
            time_match = re.match(r"(\d+):(\d+):(\d+[.,]\d+)", lines[i])
            if time_match:
                h, m, s = time_match.groups()
                s = s.replace(",", ".")
                start_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                    text_lines.append(lines[i].strip())
                    i += 1
                text = " ".join(text_lines)
                text = re.sub(r"<[^>]+>", "", text).strip()
                if text:
                    segments.append({"start": start_seconds, "text": text})
            else:
                i += 1
        else:
            i += 1
    return segments


def parse_srt(path: str) -> list[dict]:
    """Parse SRT subtitle file into [{start, text}] list."""
    segments = []
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        for i, line in enumerate(lines):
            if "-->" in line:
                time_match = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", line)
                if time_match:
                    h, m, s, ms = time_match.groups()
                    start_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
                    text_lines = [l.strip() for l in lines[i + 1 :] if l.strip()]
                    text = " ".join(text_lines)
                    text = re.sub(r"<[^>]+>", "", text).strip()
                    if text:
                        segments.append({"start": start_seconds, "text": text})
                break
    return segments


async def get_transcript(job_dir: Path, video_filepath: Path, whisper_model_size: str) -> list[dict]:
    """Returns [{start: float, text: str}] segments.

    Tries existing subtitle files first; falls back to faster-whisper.
    """
    for ext, parser in [("*.vtt", parse_vtt), ("*.srt", parse_srt)]:
        for f in job_dir.glob(ext):
            segments = parser(str(f))
            if segments:
                return segments

    loop = asyncio.get_event_loop()

    def _transcribe():
        from faster_whisper import WhisperModel

        model = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(video_filepath), word_timestamps=False)
        return [{"start": seg.start, "text": seg.text.strip()} for seg in segments if seg.text.strip()]

    return await loop.run_in_executor(None, _transcribe)
