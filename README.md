# StepScribe

> Paste a YouTube or Instagram link — get the tutorial as clear numbered steps.

![Demo](demo.gif)

StepScribe downloads a tutorial video, transcribes the speech, detects key screen moments, and asks a local LLM to extract every action into a numbered checklist with clickable timestamps. No API key required by default — everything runs locally via Ollama and Whisper.

---

## Quick start (Docker — recommended)

```bash
git clone https://github.com/jashtags/stepscribe.git
cd stepscribe
cp .env.example .env
docker compose up
```

Open [http://localhost:5173](http://localhost:5173) and paste a YouTube or public Instagram link.

> **First run note:** Docker will pull the Ollama language models (~4–7 GB). This takes a few minutes on first start. Subsequent starts are instant.

---

## Quick start (local, no Docker)

**Backend:**
```bash
# Install ffmpeg first
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu/Debian

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

You also need [Ollama](https://ollama.com) running locally:
```bash
ollama pull llama3.2:3b
ollama serve
```

---

## How it works

```
URL
 │
 ├─▶ 1. Detect platform (YouTube / Instagram)
 ├─▶ 2. Download video + metadata  (yt-dlp)
 ├─▶ 3. Get transcript
 │       ├─ YouTube: existing captions  (fast path, no compute)
 │       └─ else: faster-whisper  (local, with word timestamps)
 ├─▶ 4. Extract keyframes  (ffmpeg scene detection)
 ├─▶ 5. OCR on-screen text  (optional, ENABLE_OCR=true)
 ├─▶ 6. LLM step synthesis  (Ollama / Anthropic)
 └─▶ 7. Return numbered steps with timestamps → UI
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_BACKEND` | `ollama` | `ollama` (local, free) or `anthropic` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2-vision:11b` | Vision model for frame analysis |
| `OLLAMA_TEXT_MODEL` | `llama3.2:3b` | Text-only model (faster) |
| `ANTHROPIC_API_KEY` | *(empty)* | Required only when `LLM_BACKEND=anthropic` |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Claude model to use |
| `WHISPER_MODEL` | `small` | Whisper model size: `tiny` / `base` / `small` / `medium` |
| `ENABLE_OCR` | `false` | Enable EasyOCR for on-screen text (slower) |
| `CLEANUP_AFTER_SUCCESS` | `true` | Delete media files after processing |
| `MAX_KEYFRAMES` | `30` | Cap on extracted frames |
| `SCENE_THRESHOLD` | `0.3` | FFmpeg scene-change sensitivity (0–1) |

---

## Switching to Anthropic for higher quality

Set these in your `.env`:
```env
LLM_BACKEND=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

This uses Claude (Haiku by default — fast and affordable) for step extraction. The rest of the pipeline (download, transcription, keyframes) remains free and local.

---

## Limitations

- **Public videos only.** Private Instagram accounts and login-required YouTube videos are not supported.
- **Personal and educational use.** Respect platform terms of service. Prefer the YouTube captions path (no audio download needed).
- **Instagram captions** are rarely available — Whisper always runs for Instagram Reels, which requires more compute time.
- **Long videos** take longer to process. Whisper transcription and LLM inference both scale with video length.

---

## Contributing

PRs welcome. Open an issue first for significant changes.

---

## License

MIT — see [LICENSE](LICENSE).
