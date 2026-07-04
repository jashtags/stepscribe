# Tools Used in StepScribe

A breakdown of every tool in the stack — what it is, what it does here, why we chose it, and how it keeps StepScribe free to run.

---

## yt-dlp

**What it is:** A feature-rich command-line program and Python library for downloading videos from YouTube, Instagram, and 1000+ other sites.

**What it does in StepScribe:** Downloads the tutorial video to a local temp directory and retrieves existing subtitle/caption tracks (VTT/SRT format) if available. Also extracts metadata: title, duration, video ID.

**Why we chose it:** yt-dlp is the de-facto standard for YouTube/Instagram download. It handles authentication flows, rate limits, format selection, and subtitle extraction out of the box. The Python API means we avoid subprocess shell calls and get structured metadata directly.

**Free/local angle:** Completely free and open-source. No API key or account required for public videos.

---

## faster-whisper

**What it is:** A reimplementation of OpenAI's Whisper model using CTranslate2, achieving 2–4× faster inference at lower memory usage.

**What it does in StepScribe:** Transcribes the audio track into timestamped text segments when captions aren't available (e.g. most Instagram Reels). Returns `[{start: float, text: str}]` segments that power the "jump to step" timestamps.

**Why we chose it:** Runs entirely on CPU (or GPU if available) with no external service call. The `small` model is a good balance of speed and accuracy for tutorial speech. faster-whisper specifically is chosen over the original Whisper for its speed advantage on CPU.

**Free/local angle:** Fully local inference. The model weights download once and run offline forever.

---

## ffmpeg

**What it is:** The universal open-source multimedia processing framework — decodes, encodes, filters, and analyzes virtually any audio/video format.

**What it does in StepScribe:** Extracts keyframes at scene-change boundaries using the `select='gt(scene,threshold)'` filter. This gives us the frames where the screen actually changes (a new tool opens, a setting changes) rather than sampling blindly every N seconds.

**Why we chose it:** ffmpeg is the industry standard for this kind of frame-level analysis. The scene-change filter is purpose-built for detecting visual cuts and edits, making it ideal for tutorial screen recordings.

**Free/local angle:** Open-source (LGPL/GPL), runs locally, installed via brew/apt.

---

## EasyOCR

**What it is:** A ready-to-use Python OCR library supporting 80+ languages, built on PyTorch.

**What it does in StepScribe:** When `ENABLE_OCR=true`, reads on-screen text from each keyframe — menu names, button labels, setting values — that may never be spoken aloud. This text is fed to the LLM alongside the transcript.

**Why we chose it:** Requires no API key, runs locally, and handles the kind of UI text typical in software tutorials well. It's off by default because it adds significant processing time.

**Free/local angle:** Fully local PyTorch inference. Disabled by default to keep the pipeline fast.

---

## Ollama

**What it is:** A tool for running large language models locally, providing an OpenAI-compatible REST API for models like Llama, Mistral, and Qwen.

**What it does in StepScribe:** The default LLM backend. Receives the assembled prompt (transcript + keyframe context) and returns the structured JSON step list. Uses a text model (`llama3.2:3b`) for speed, or a vision model for richer frame analysis.

**Why we chose it:** Ollama makes local LLM inference as simple as `ollama pull <model> && ollama serve`. No API key, no usage fees, no data sent to third parties. The HTTP API is clean and easy to call with `httpx`.

**Free/local angle:** The entire step-extraction pipeline runs locally for free. This is the core "no paid API required" promise of StepScribe.

---

## FastAPI

**What it is:** A modern, high-performance Python web framework for building APIs, built on Starlette and Pydantic.

**What it does in StepScribe:** Powers the backend HTTP server. Handles job submission (`POST /api/jobs`), job status polling (`GET /api/jobs/{id}`), runs the pipeline as async background tasks, and serializes responses via Pydantic models.

**Why we chose it:** FastAPI's async support is well-suited to a pipeline that does I/O-heavy work (downloads, subprocess calls, HTTP to Ollama). Automatic OpenAPI docs are a bonus. Pydantic integration means our job models double as both storage and API response schemas.

**Free/local angle:** Open-source. The entire backend runs in a single Python process, no database server required.

---

## React + Vite

**What it is:** React is the leading UI library for building component-based interfaces; Vite is a next-generation build tool with instant HMR.

**What it does in StepScribe:** Provides the single-page UI: URL input, real-time progress display (polling the backend every 2s), the numbered step rail, timestamp links, and Markdown export.

**Why we chose it:** React's component model fits the step-list UI well. Vite's dev server starts instantly and the proxy feature lets us hit the FastAPI backend without CORS config during development.

**Free/local angle:** All open-source. The built static bundle is served by nginx in Docker — no Node.js runtime in production.

---

## docker-compose

**What it is:** A tool for defining and running multi-container Docker applications from a single YAML file.

**What it does in StepScribe:** Wires together four services — Ollama (LLM inference), an init container that pulls the required models, the FastAPI backend, and the nginx-served frontend — with a single `docker compose up` command.

**Why we chose it:** Eliminates the need to install ffmpeg, Python, Node.js, or Ollama on the host machine. Handles networking between services, volume mounts for persistent model storage, and health checks to ensure Ollama is ready before the backend starts.

**Free/local angle:** Open-source. The only cost is disk space for model weights and compute for inference — both local.
