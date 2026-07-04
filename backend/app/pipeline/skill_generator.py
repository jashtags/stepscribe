import json
import re

import httpx

# Known MCP mappings for common tools
_MCP_HINTS = {
    "github": ("github", "Use the **GitHub MCP** to automate repo operations, PR creation, and issue tracking."),
    "git": ("git", "Use a **git MCP** or shell tool to run git commands programmatically."),
    "figma": ("figma", "Use the **Figma MCP** to read designs and export assets programmatically."),
    "notion": ("notion", "Use the **Notion MCP** to read/write pages and databases."),
    "slack": ("slack", "Use the **Slack MCP** to send messages and read channels."),
    "gmail": ("gmail", "Use the **Gmail MCP** to read and send emails."),
    "google sheets": ("google-sheets", "Use the **Google Sheets MCP** to read/write spreadsheet data."),
    "google docs": ("google-docs", "Use the **Google Docs MCP** to read/write documents."),
    "vs code": ("vscode", "Use the **VS Code MCP** or shell commands to open files and run tasks."),
    "vscode": ("vscode", "Use the **VS Code MCP** or shell commands to open files and run tasks."),
    "terminal": ("shell", "Use a **shell/bash MCP** to execute terminal commands."),
    "youtube": ("browser", "Use a **browser automation MCP** (e.g. claude-in-chrome) to navigate YouTube."),
    "instagram": ("browser", "Use a **browser automation MCP** to interact with Instagram."),
    "twitter": ("browser", "Use a **browser automation MCP** to interact with Twitter/X."),
    "chrome": ("browser", "Use the **claude-in-chrome MCP** to automate Chrome browser actions."),
    "browser": ("browser", "Use the **claude-in-chrome MCP** to automate any web browser workflow."),
}

_WEBSITE_MCP_HINT = "Use the **claude-in-chrome MCP** (browser automation) to navigate to this site, click elements, and extract content automatically."


def _detect_mcps(tools: list[str], steps: list[dict]) -> list[str]:
    """Return MCP suggestions based on tools/websites mentioned."""
    hints = set()
    all_text = " ".join(tools + [s.get("text", "") for s in steps]).lower()

    # Check known tools
    for keyword, (_, hint) in _MCP_HINTS.items():
        if keyword in all_text:
            hints.add(hint)

    # Any .com/.fr/.io/.org URL → browser MCP (if not already covered)
    has_website = bool(re.search(r'\b\w+\.(com|fr|io|org|net|co|app|dev)\b', " ".join(tools).lower()))
    if has_website and not any("browser" in h.lower() for h in hints):
        hints.add(_WEBSITE_MCP_HINT)

    return sorted(hints)


def _format_timestamp(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _build_skill_prompt(job_data: dict, video_meta: dict) -> str:
    title = video_meta.get("title", "Tutorial")
    summary = job_data.get("summary", "")
    tools = job_data.get("tools", [])
    steps = job_data.get("steps", [])

    lines = [
        f"Tutorial title: {title}",
        f"Summary: {summary}",
        f"Tools/sites mentioned: {', '.join(tools) if tools else 'not specified'}",
        "",
        "Steps extracted from the video:",
    ]
    for step in steps:
        ts = _format_timestamp(step.get("start", 0))
        lines.append(f"{step['n']}. [{ts}] {step['text']}")

    lines += [
        "",
        "Generate a SKILL.md file for this tutorial. The file must:",
        "1. Have YAML frontmatter with name (kebab-case), description, and tools fields",
        "2. Include a ## Summary section",
        "3. Include a ## Steps section with each step numbered and timestamped",
        "4. Include a ## Tools & Websites section listing each tool with a one-line description",
        "5. Be written so an AI agent reading it can reproduce the tutorial without watching the video",
        "",
        "Return ONLY the raw markdown (no code fences).",
    ]
    return "\n".join(lines)


SKILL_SYSTEM_PROMPT = """You generate SKILL.md files — reusable skill documents for AI agents.
A SKILL.md describes a real-world tutorial as a machine-readable + human-readable skill.
Be concrete and specific. Name every tool, website, button, and setting exactly.
Format the output as clean markdown starting with YAML frontmatter."""


async def _call_ollama_skill(prompt: str, config) -> str:
    payload = {
        "model": config.OLLAMA_TEXT_MODEL,
        "prompt": f"{SKILL_SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{config.OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]


async def _call_anthropic_skill(prompt: str, config) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2048,
        system=SKILL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _build_skill_markdown(job_data: dict, video_meta: dict, llm_output: str) -> str:
    """Combine LLM output with MCP hints to produce the final skill file."""
    tools = job_data.get("tools", [])
    steps = job_data.get("steps", [])
    mcp_hints = _detect_mcps(tools, steps)

    content = llm_output.strip()

    # Append MCP section if hints exist
    if mcp_hints:
        mcp_section = "\n\n## MCP Opportunities\n\n"
        mcp_section += "An AI agent can automate this skill using:\n\n"
        for hint in mcp_hints:
            mcp_section += f"- {hint}\n"
        mcp_section += "\n> Install MCPs via Claude Code settings. For browser automation, ensure the `claude-in-chrome` extension is active."
        content += mcp_section

    # Append video source
    platform = video_meta.get("platform", "youtube")
    video_id = video_meta.get("video_id", "")
    if platform == "youtube" and video_id:
        content += f"\n\n## Source Video\n\nhttps://www.youtube.com/watch?v={video_id}\n"

    return content


async def generate_skill_file(job_data: dict, video_meta: dict, config) -> str:
    """Generate a SKILL.md file from completed job data. Returns markdown string."""
    prompt = _build_skill_prompt(job_data, video_meta)

    if config.LLM_BACKEND == "anthropic":
        llm_output = await _call_anthropic_skill(prompt, config)
    else:
        llm_output = await _call_ollama_skill(prompt, config)

    return _build_skill_markdown(job_data, video_meta, llm_output)
