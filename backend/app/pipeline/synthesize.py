import json
import re

import httpx

SYSTEM_PROMPT = """You convert a tutorial video into clear, ordered steps for a beginner.
You are given the spoken transcript (with timestamps) and descriptions of
key on-screen moments. Produce a numbered list of actions the viewer must
take to reproduce the result.

Rules:
- Each step is ONE concrete action, in plain language.
- Say WHERE to click / tap and WHAT to do ("Tap the + icon at the bottom",
  not "add media").
- Use the exact tool, button, and setting names shown on screen when known.
- Attach the start timestamp (seconds) of the moment the step begins.
- Merge filler; drop intros, outros, and "like and subscribe".
- If the video says "link in bio / comment X", add a final step noting a
  link is referenced and that the user should check the source, but DO NOT
  invent a URL.

Return ONLY valid JSON, no prose, no markdown fences:
{
  "summary": "one sentence on what this tutorial achieves",
  "steps": [
    { "n": 1, "text": "...", "start": 12.4 }
  ]
}"""


def _build_user_prompt(transcript: list[dict], frames: list[dict]) -> str:
    parts = ["## Transcript (timestamps in seconds)\n"]
    for seg in transcript[:200]:
        parts.append(f"[{seg['start']:.1f}s] {seg['text']}")

    if frames:
        parts.append("\n## Key on-screen moments\n")
        for frame in frames[:30]:
            ocr = frame.get("ocr_text", "")
            if ocr:
                parts.append(f"[{frame['timestamp']:.1f}s] Screen shows: {ocr}")
            else:
                parts.append(f"[{frame['timestamp']:.1f}s] Screen change detected")

    return "\n".join(parts)


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()
    return json.loads(text)


async def _call_ollama(prompt: str, config, retry: bool = False) -> str:
    if retry:
        prompt += "\n\nIMPORTANT: Return ONLY valid JSON, no prose, no markdown fences."
    payload = {
        "model": config.OLLAMA_TEXT_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4096},
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(f"{config.OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]


async def _call_anthropic(prompt: str, config, retry: bool = False) -> str:
    import anthropic

    if retry:
        prompt += "\n\nIMPORTANT: Return ONLY valid JSON, no prose, no markdown fences."
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def synthesize_steps(transcript: list[dict], frames: list[dict], config) -> dict:
    """Returns {summary: str, steps: [{n, text, start}]}."""
    user_prompt = _build_user_prompt(transcript, frames)

    for attempt in range(2):
        retry = attempt > 0
        try:
            if config.LLM_BACKEND == "anthropic":
                raw = await _call_anthropic(user_prompt, config, retry=retry)
            else:
                raw = await _call_ollama(user_prompt, config, retry=retry)

            result = _parse_json_response(raw)

            if "steps" not in result or not isinstance(result["steps"], list):
                raise ValueError("LLM response missing valid 'steps' list")

            steps = [
                {
                    "n": s.get("n", i + 1),
                    "text": s.get("text", ""),
                    "start": float(s.get("start", 0)),
                }
                for i, s in enumerate(result["steps"])
            ]

            return {"summary": result.get("summary", ""), "steps": steps}

        except (json.JSONDecodeError, ValueError, KeyError):
            if attempt == 0:
                continue
            raise ValueError("LLM returned invalid JSON after 2 attempts. Try a different model or check OLLAMA_TEXT_MODEL.")
