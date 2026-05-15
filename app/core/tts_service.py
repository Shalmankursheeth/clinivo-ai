"""
TTS Service — ElevenLabs Multilingual v2
Async text-to-speech with Redis-backed caching.

WHY ELEVENLABS over Google TTS:
  eleven_multilingual_v2 handles Tamil words embedded in English sentences
  naturally. Google TTS mispronounces Tamil doctor names and place names.

CACHING STRATEGY:
  Common phrases (greetings, fee responses) are MD5-hashed.
  Audio URL stored in Redis with 24h TTL.
  Same phrase on 1000 calls → 1 ElevenLabs API call.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
AUDIO_DIR = Path("public/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.2,
    "use_speaker_boost": True
}


async def synthesize(text: str) -> Optional[bytes]:
    """
    Convert text to MP3 audio bytes.
    Checks Redis cache first (by MD5 hash of text).
    """
    if not text:
        return None

    text_hash = hashlib.md5(text.encode()).hexdigest()

    # Check Redis cache
    cached_url = await redis_client.get_tts_cache(text_hash)
    if cached_url:
        logger.info(f"🔊 TTS cache hit: '{text[:40]}...'")
        # Read file from disk
        filename = cached_url.split("/audio/")[-1]
        filepath = AUDIO_DIR / filename
        if filepath.exists():
            return filepath.read_bytes()

    logger.info(f"🔊 TTS generating: '{text[:60]}'")

    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": VOICE_SETTINGS
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(ELEVENLABS_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None


async def synthesize_and_save(text: str, call_sid: str) -> Optional[str]:
    """
    Synthesize TTS, save to disk, cache URL in Redis.
    Returns public URL Twilio can play.
    """
    text_hash = hashlib.md5(text.encode()).hexdigest()

    # Check Redis for cached URL
    cached_url = await redis_client.get_tts_cache(text_hash)
    if cached_url:
        filepath = AUDIO_DIR / cached_url.split("/audio/")[-1]
        if filepath.exists():
            logger.info(f"🔊 TTS served from cache")
            return cached_url

    audio_bytes = await synthesize(text)
    if not audio_bytes:
        return None

    # Save
    filename = f"{call_sid}_{text_hash[:8]}.mp3"
    filepath = AUDIO_DIR / filename
    filepath.write_bytes(audio_bytes)

    public_url = f"{settings.PUBLIC_URL}/audio/{filename}"

    # Cache in Redis (24h)
    await redis_client.set_tts_cache(text_hash, public_url, ttl=86400)

    return public_url


async def cleanup_old_audio(max_age_seconds: int = 3600):
    """Remove audio files older than max_age_seconds. Call periodically."""
    import time
    now = time.time()
    for filepath in AUDIO_DIR.glob("*.mp3"):
        if now - filepath.stat().st_mtime > max_age_seconds:
            filepath.unlink(missing_ok=True)