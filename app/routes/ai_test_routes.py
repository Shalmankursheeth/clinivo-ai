"""
AI Test Routes — Test the full stack without making a phone call.

POST /api/ai/test           → text → AI reply
POST /api/ai/tts-test       → text → audio URL
POST /api/ai/full-pipeline  → text → AI reply + audio URL + latency breakdown
"""

import time
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import ai_service
from app.voice import tts_service, stt_service
from app.core.config import settings

router = APIRouter()


class TextRequest(BaseModel):
    message: str
    phone: str = "test-user"
    clinic_id: str = ""


class TTSRequest(BaseModel):
    text: str


class STSRequest(BaseModel):
    audio_url: str


@router.post("/test")
async def test_ai(req: TextRequest):
    clinic_id = req.clinic_id or settings.DEFAULT_CLINIC_ID
    t0 = time.monotonic()
    reply = await ai_service.process_message(req.message, req.phone, clinic_id)
    return {
        "input": req.message,
        "reply": reply,
        "latency_ms": round((time.monotonic() - t0) * 1000),
        "clinic_id": clinic_id
    }


@router.post("/tts-test")
async def test_tts(req: TTSRequest):
    t0 = time.monotonic()
    audio_url = await tts_service.synthesize_and_save(req.text, "tts_test")
    return {
        "text": req.text,
        "audio_url": audio_url,
        "latency_ms": round((time.monotonic() - t0) * 1000)
    }


@router.post("/stt-test")
async def test_stt(req: STSRequest):
    t0 = time.monotonic()
    transcript = await stt_service.transcribe_from_url(req.audio_url)
    return {
        "audio_url": req.audio_url,
        "transcript": transcript,
        "latency_ms": round((time.monotonic() - t0) * 1000)
    }


@router.post("/full-pipeline")
async def full_pipeline(req: TextRequest):
    """
    Full pipeline: text → AI → TTS
    Returns latency breakdown so you can see where time is spent.
    Useful for demo: shows <500ms AI + <800ms TTS = <1.3s total end-to-end.
    """
    clinic_id = req.clinic_id or settings.DEFAULT_CLINIC_ID

    t0 = time.monotonic()
    reply = await ai_service.process_message(req.message, req.phone, clinic_id)
    ai_ms = round((time.monotonic() - t0) * 1000)

    t1 = time.monotonic()
    audio_url = await tts_service.synthesize_and_save(reply, "pipeline_test")
    tts_ms = round((time.monotonic() - t1) * 1000)

    return {
        "input": req.message,
        "reply": reply,
        "audio_url": audio_url,
        "latency": {
            "ai_ms": ai_ms,
            "tts_ms": tts_ms,
            "total_ms": ai_ms + tts_ms
        }
    }