"""
AI Clinic Voice Receptionist — FastAPI Backend
Stack: FastAPI + Redis + Supabase + Groq + Deepgram + ElevenLabs + Twilio
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.redis_client import redis_client
from app.routes import voice_routes, ai_test_routes, doctor_routes, dashboard_routes
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ── Lifespan: startup + shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Starting AI Clinic Voice Receptionist...")
    await redis_client.connect()
    logger.info("Redis connected ✓")
    yield
    # SHUTDOWN
    await redis_client.disconnect()
    logger.info("Shutdown complete")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Clinic Voice Receptionist",
    description="Production voice AI for clinics — Twilio + Deepgram + Groq + ElevenLabs",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=60)

# ── Static files (TTS audio served to Twilio) ────────────────────────────────
import os
os.makedirs("public/audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="public/audio"), name="audio")

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(voice_routes.router,     prefix="/voice",     tags=["Voice (Twilio)"])
app.include_router(ai_test_routes.router,   prefix="/api/ai",    tags=["AI Testing"])
app.include_router(doctor_routes.router,    prefix="/api/doctors", tags=["Doctors"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["Dashboard"])


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health():
    redis_ok = await redis_client.ping()
    return {
        "status": "ok",
        "service": "AI Clinic Voice Receptionist",
        "version": "2.0.0",
        "dependencies": {
            "redis": "ok" if redis_ok else "down",
        },
        "voice_stack": {
            "stt": "Deepgram Nova-2 (en-IN)",
            "llm": "Groq LLaMA-3.3-70b",
            "tts": "ElevenLabs Multilingual v2",
            "telephony": "Twilio"
        },
        "webhooks": {
            "incoming_call": "POST /voice/incoming",
            "process_speech": "POST /voice/process",
            "call_status":    "POST /voice/status"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG,
        log_level="info"
    )