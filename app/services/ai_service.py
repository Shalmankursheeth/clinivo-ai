"""
AI Service — Orchestrator
STT → intent extraction → AI brain → TTS

Called by:
  - twilioVoiceController (phone calls)
  - ai_test_routes (direct HTTP testing)
"""

import logging
import time

from app.services import intent_extractor, session_service, ai_brain

logger = logging.getLogger(__name__)


async def process_message(text: str, phone: str, clinic_id: str) -> str:
    """
    Full AI pipeline:
      1. Load session from Redis
      2. Extract intents + entities via Groq
      3. Merge entities into session
      4. Run clinic logic brain
      5. Persist session back to Redis
      6. Return reply text
    """
    if not text or not text.strip():
        return "Sorry, I didn't catch that. Could you repeat?"

    t0 = time.monotonic()
    logger.info(f"🧠 Processing | phone={phone} | text='{text}'")

    # 1. Session
    session = await session_service.get_session(phone)

    # 2. Intent extraction
    extracted = await intent_extractor.extract(text)
    intents = extracted.get("intents") or ["unknown"]
    entities = extracted.get("entities") or {}

    # 3. Merge entities into session
    session = session_service.merge_entities(session, entities)

    # 4. AI brain
    reply = await ai_brain.run(
        intents=intents,
        entities=entities,
        session=session,
        clinic_id=clinic_id,
        message=text
    )

    # 5. Persist session
    await session_service.save_session(phone, session)

    elapsed = (time.monotonic() - t0) * 1000
    logger.info(f"💬 Reply ({elapsed:.0f}ms): '{reply}'")

    return reply or "Let me connect you to our staff."