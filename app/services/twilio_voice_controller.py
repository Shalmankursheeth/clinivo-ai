"""
Twilio Voice Controller — FastAPI
Handles the complete phone call lifecycle.

CALL FLOW:
  1. POST /voice/incoming  → greeting TwiML
  2. POST /voice/process   → STT → LLM → TTS → reply TwiML
  3. POST /voice/status    → cleanup on call end
"""

import logging
from fastapi import Request
from fastapi.responses import Response

from twilio.twiml.voice_response import VoiceResponse, Gather

from app.core.config import settings
from app.services import ai_service, session_service
from app.voice import tts_service

logger = logging.getLogger(__name__)


def _get_clinic_id(to_number: str) -> str:
    # In production: DB lookup (twilio_number → clinic_id)
    # For demo: env var
    return settings.DEFAULT_CLINIC_ID


def _twiml_response(twiml: VoiceResponse) -> Response:
    return Response(content=str(twiml), media_type="application/xml")


async def handle_incoming(request: Request) -> Response:
    """
    Twilio calls this when someone dials your number.
    Returns TwiML: greet caller, then listen.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    from_phone = form.get("From", "unknown")
    to_phone = form.get("To", "")

    logger.info(f"📞 Incoming | SID={call_sid} | From={from_phone}")

    clinic_id = _get_clinic_id(to_phone)

    from app.services.greeting_service import get_greeting
    greeting_text = get_greeting()

    audio_url = await tts_service.synthesize_and_save(greeting_text, call_sid + "_greeting")

    twiml = VoiceResponse()

    if audio_url:
        twiml.play(audio_url)
    else:
        twiml.say(greeting_text, voice="alice", language="en-IN")

    gather = Gather(
        input="speech",
        action=f"{settings.PUBLIC_URL}/voice/process",
        method="POST",
        speechTimeout="3",
        speechModel="phone_call",
        language="en-IN",
        actionOnEmptyResult=True,
        timeout=10
    )
    twiml.append(gather)
    twiml.redirect(f"{settings.PUBLIC_URL}/voice/process")

    return _twiml_response(twiml)


async def process_call(request: Request) -> Response:
    """
    Called by Twilio after <Gather> captures caller speech.
    Runs full AI pipeline and returns audio reply.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    from_phone = form.get("From", "unknown")
    to_phone = form.get("To", "")
    transcript = (form.get("SpeechResult") or "").strip()

    logger.info(f"🎤 Caller: '{transcript}' | SID={call_sid}")

    clinic_id = _get_clinic_id(to_phone)
    twiml = VoiceResponse()

    if not transcript:
        reply_text = "Sorry, I didn't catch that. Could you repeat please?"
    else:
        try:
            reply_text = await ai_service.process_message(transcript, from_phone, clinic_id)
        except Exception as e:
            logger.error(f"AI pipeline error: {e}")
            reply_text = "Sorry, there was a technical issue. Please call back in a moment."

    # TTS
    audio_url = await tts_service.synthesize_and_save(
        reply_text, f"{call_sid}_reply"
    )

    if audio_url:
        twiml.play(audio_url)
    else:
        twiml.say(reply_text, voice="alice", language="en-IN")

    # Keep conversation loop going
    gather = Gather(
        input="speech",
        action=f"{settings.PUBLIC_URL}/voice/process",
        method="POST",
        speechTimeout="3",
        speechModel="phone_call",
        language="en-IN",
        actionOnEmptyResult=True,
        timeout=10
    )
    twiml.append(gather)
    twiml.redirect(f"{settings.PUBLIC_URL}/voice/process")

    return _twiml_response(twiml)


async def handle_status(request: Request) -> Response:
    """
    Twilio notifies here when call ends.
    Clean up Redis session.
    """
    form = await request.form()
    call_sid = form.get("CallSid")
    status = form.get("CallStatus")
    from_phone = form.get("From")
    duration = form.get("CallDuration", "0")

    logger.info(f"📵 Call ended | SID={call_sid} | Status={status} | Duration={duration}s")

    if from_phone:
        await session_service.delete_session(from_phone)

    # Async cleanup of old audio files (fire and forget)
    import asyncio
    asyncio.create_task(tts_service.cleanup_old_audio())

    return Response(status_code=204)