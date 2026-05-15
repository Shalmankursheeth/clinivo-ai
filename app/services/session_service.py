"""
Session Service — Redis-backed
REPLACES in-memory dict sessions.

WHY THIS IS CRITICAL:
  Old approach: sessions = {}  (Python dict, in-process)
  Problem: Deploy 2 instances behind a load balancer.
    Call 1 (turn 1) → Instance A → session created in A's memory
    Call 1 (turn 2) → Instance B → session NOT FOUND → conversation resets

  Redis solution: sessions live outside the process.
  Any instance can read/write any session. Stateless instances → horizontal scaling.

  Also: if instance crashes mid-call, Redis holds the session.
  Caller calls back → picks up context from Redis.
"""

import logging
from typing import Optional

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


async def get_session(phone: str) -> dict:
    """Get caller session from Redis. Creates default if not found."""
    session = await redis_client.get_session(phone)
    return session


async def save_session(phone: str, session: dict):
    """Persist session back to Redis after each turn."""
    await redis_client.save_session(phone, session)


async def delete_session(phone: str):
    """Clean up when call ends."""
    await redis_client.delete_session(phone)
    logger.info(f"Session cleaned: {phone}")


def merge_entities(session: dict, entities: dict) -> dict:
    """
    Merge new entities into session data.
    Only overwrites if new info is present (preserves context across turns).
    """
    data = session.get("data", {})

    if entities.get("doctor_name_normalized"):
        data["doctor"] = entities["doctor_name_normalized"]

    if entities.get("speciality_normalized"):
        data["speciality"] = entities["speciality_normalized"]
        data["doctor"] = None  # reset doctor when speciality changes

    if entities.get("date"):
        data["date"] = entities["date"]

    if entities.get("time_preference"):
        data["time_preference"] = entities["time_preference"]

    if entities.get("need_alternative"):
        data["need_alternative"] = True

    if entities.get("is_correction"):
        data["doctor"] = None

    session["data"] = data
    return session