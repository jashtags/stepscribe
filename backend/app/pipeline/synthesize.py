import json
import re

import httpx

SYSTEM_PROMPT = """You are a meticulous tutorial analyst. Your job is to extract EVERY concrete action the viewer must take.

You receive a spoken transcript with timestamps from a tutorial video. Extract each distinct user action as a numbered step.

STRICT RULES:
1. Produce AT LEAST 5 steps. Most tutorials have 8–20 steps.
2. Each step = ONE physical action: open a site, click a button, type something, tap an icon, select a menu item.
3. Name EVERY website URL, app, tool, icon, and button EXACTLY as mentioned or shown (e.g. "animeclipsraw.fr", "hamburger icon", "search bar at the top").
4. Include exact screen locations: "top-right corner", "bottom navigation bar", "hamburger menu (☰) at the top-left".
5. If the presenter says to go to a website, that is ONE step: "Open [exact URL] in your browser."
6. If they click a specific icon/button, that is ONE step: "Click the [name] icon in the [location]."
7. If they type something, include exactly what to type.
8. Split ANY compound action into separate steps.
9. Drop intros, outros, and "like and subscribe" filler.
10. For any referenced URL or link mentioned verbally (not shown), include it as-is; DO NOT invent URLs.

Also extract:
- tools: a list of every website, app, or tool mentioned by name

Return ONLY valid JSON (no markdown fences, no extra text):
{
  "summary": "one sentence describing exactly what this tutorial achieves",
  "tools": ["website1.com", "App Name", "tool name"],
  "steps": [
    { "n": 1, "text": "Exact action description.", "start": 5.0 }
  ]
}"""


def _build_user_prompt(transcript: list[dict], frames: list[dict]) -> str:
    parts = ["## Spoken transcript (timestamps in seconds — use these for the 'start' field)\n"]
    for seg in transcript[:300]:
        parts.append(f"[{seg['start']:.1f}s] {seg['text']}")

    if frames:
        parts.append("\n## On-screen changes detected by keyframe analysis\n")
        for frame in frames[:30]:
            ocr = frame.get("ocr_text", "")
            if ocr:
                parts.append(f"[{frame['timestamp']:.1f}s] Screen text visible: {ocr}")
            else:
                parts.append(f"[{frame['timestamp']:.1f}s] Visual scene change")

    parts.append("\n## Your task\nExtract every user action as a numbered step. Be specific about UI elements and websites. Return valid JSON only.")
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
