import asyncio
from pathlib import Path


async def extract_text_from_frames(frames: list[dict]) -> list[dict]:
    """Adds 'ocr_text' key to each frame dict. Requires easyocr installed."""
    try:
        import easyocr
    except ImportError:
        raise ImportError(
            "easyocr is not installed. Add 'easyocr' to requirements.txt and rebuild the Docker image."
        )

    loop = asyncio.get_event_loop()

    def _run_ocr():
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        for frame in frames:
            if Path(frame["path"]).exists():
                results = reader.readtext(frame["path"])
                frame["ocr_text"] = " ".join(r[1] for r in results if r[2] > 0.5)
            else:
                frame["ocr_text"] = ""
        return frames

    return await loop.run_in_executor(None, _run_ocr)
