"""
STT Service — Deepgram Nova-2
Async speech-to-text for phone call audio.

Deepgram nova-2 with en-IN handles:
  - Indian-accented English
  - Phone-quality audio (8kHz mulaw from Twilio)
  - Better than Whisper for real-time latency (~300ms vs 1s+)
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEEPGRAM_BASE = "https://api.deepgram.com/v1/listen"

DEEPGRAM_PARAMS = {
    "model": "nova-2",
    "language": "en-IN",
    "smart_format": "true",
    "punctuate": "true",
    "keywords": "doctor:2,appointment:2,token:2,fee:1,clinic:1,morning:1,evening:1"
}

HEADERS = {
    "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
    "Content-Type": "audio/mpeg"
}


async def transcribe_buffer(audio_bytes: bytes, encoding: str = "mulaw", sample_rate: int = 8000) -> Optional[str]:
    """
    Transcribe raw audio buffer (from Twilio).
    encoding: mulaw for phone calls, linear16 or wav for others
    """
    params = {**DEEPGRAM_PARAMS, "encoding": encoding, "sample_rate": sample_rate, "channels": 1}

    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/mulaw"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                DEEPGRAM_BASE,
                content=audio_bytes,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            transcript = (
                data.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
            )
            logger.info(f"🎤 STT: '{transcript}'")
            return transcript or None

        except httpx.HTTPError as e:
            logger.error(f"Deepgram HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return None


async def transcribe_from_url(audio_url: str) -> Optional[str]:
    """
    Transcribe from a public URL (e.g. Twilio recording URL).
    Twilio sends a RecordingUrl after <Record> completes.
    """
    headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
    payload = {"url": audio_url}

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(
                DEEPGRAM_BASE,
                json=payload,
                headers=headers,
                params=DEEPGRAM_PARAMS
            )
            response.raise_for_status()
            data = response.json()
            transcript = (
                data.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
            )
            logger.info(f"🎤 STT (URL): '{transcript}'")
            return transcript or None

        except Exception as e:
            logger.error(f"STT from URL failed: {e}")
            return None