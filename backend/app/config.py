from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_BACKEND: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2-vision:11b"
    OLLAMA_TEXT_MODEL: str = "llama3.2:3b"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    WHISPER_MODEL: str = "small"
    ENABLE_OCR: bool = False
    MEDIA_DIR: str = "./media"
    CLEANUP_AFTER_SUCCESS: bool = True
    MAX_KEYFRAMES: int = 30
    SCENE_THRESHOLD: float = 0.3

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
