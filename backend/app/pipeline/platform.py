import re


def detect_platform(url: str) -> str:
    """Returns 'youtube' or 'instagram'. Raises ValueError for anything else."""
    url = url.strip()
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch',
        r'(?:https?://)?(?:www\.)?youtu\.be/',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/',
    ]
    instagram_patterns = [
        r'(?:https?://)?(?:www\.)?instagram\.com/p/',
        r'(?:https?://)?(?:www\.)?instagram\.com/reel/',
    ]
    for pattern in youtube_patterns:
        if re.search(pattern, url):
            return "youtube"
    for pattern in instagram_patterns:
        if re.search(pattern, url):
            return "instagram"
    raise ValueError(
        "Only YouTube (youtube.com, youtu.be) and Instagram (instagram.com/p/ or /reel/) URLs are supported."
    )
