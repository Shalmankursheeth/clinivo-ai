"""
Intent Extractor Service — Groq LLaMA-3.3-70b
Async LLM call with exponential backoff retry.

WHY GROQ over OpenAI for this use case:
  ~10x faster inference for LLaMA-3.3-70b.
  Voice calls need response in <2s total. Groq delivers ~200-400ms LLM latency.
  OpenAI GPT-4 would add 1-2s, blowing the budget.
"""

import json
import logging
import asyncio
from typing import Optional

from groq import AsyncGroq

from app.core.config import settings

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a smart clinic receptionist AI for Tamil Nadu clinics.
Extract structured data STRICTLY in JSON. No preamble, no markdown.

INTENTS (choose all that apply):
smalltalk, doctor_available, book_token, token_status, check_my_token,
clinic_info, fees, directions, transfer_reception, change_doctor,
ask_alternative, ask_by_speciality, ask_by_time, ask_by_date,
urgent_request, unknown

RETURN FORMAT (JSON only):
{
  "intents": [],
  "entities": {
    "doctor_name": string|null,
    "doctor_name_normalized": string|null,
    "speciality": string|null,
    "speciality_normalized": string|null,
    "patient_name": string|null,
    "date": "today" | "tomorrow" | "future" | null,
    "time_preference": "morning" | "evening" | null,
    "confirmation": "yes" | "no" | null,
    "emotion": "pain" | "urgent" | "normal" | null,
    "is_correction": boolean,
    "need_alternative": boolean,
    "same_problem": boolean
  }
}

RULES:
1. Tamil/Tanglish names → normalize to English (மீனா → meena)
2. "kidney doctor", "heart doctor" → speciality, NOT doctor_name
3. "innaiku" → today, "nalaikku" → tomorrow
4. "seekiram", "urgent", "fast" → urgent_request + emotion=urgent
5. "seri", "ok", "haan" → confirmation=yes
6. "illa", "venam" → confirmation=no
7. NEVER hallucinate doctor names
8. ALWAYS return valid JSON only
"""


async def extract(text: str, max_retries: int = 3) -> dict:
    """
    Extract intents and entities from caller message.
    Retries with exponential backoff on failure.
    """
    for attempt in range(max_retries):
        try:
            response = await groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f'Message: "{text}"'}
                ],
                temperature=0,
                max_tokens=512,
                response_format={"type": "json_object"}  # force JSON output
            )

            raw = response.choices[0].message.content
            logger.info(f"LLM raw: {raw}")

            parsed = json.loads(raw)
            logger.info(f"🎯 Intents: {parsed.get('intents')} | Entities: {parsed.get('entities')}")
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed (attempt {attempt+1}): {e}")
        except Exception as e:
            logger.warning(f"LLM call failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s backoff

    logger.error("Intent extraction failed after all retries")
    return {"intents": ["unknown"], "entities": {}}