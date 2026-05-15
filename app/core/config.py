"""
Config — Pydantic Settings
All env vars validated at startup. App won't start with missing keys.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    PORT: int = 5000
    DEBUG: bool = False
    PUBLIC_URL: str = "https://your-ngrok-or-domain.com"

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TRANSFER_PHONE_NUMBER: str = ""

    # Deepgram (STT)
    DEEPGRAM_API_KEY: str

    # Groq (LLM)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ElevenLabs (TTS)
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    SESSION_TTL_SECONDS: int = 3600  # sessions expire after 1h

    # Clinic
    DEFAULT_CLINIC_ID: str = ""

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()