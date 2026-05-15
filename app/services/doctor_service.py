"""
Doctor Service — Supabase
Async queries for doctor data.
"""

import logging
from typing import Optional

from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)


async def get_doctors(clinic_id: str) -> list[dict]:
    try:
        result = supabase.table("doctors").select("*").eq("clinic_id", clinic_id).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_doctors failed: {e}")
        return []


async def get_doctor_by_id(doctor_id: str) -> Optional[dict]:
    try:
        result = supabase.table("doctors").select("*").eq("id", doctor_id).maybe_single().execute()
        return result.data
    except Exception as e:
        logger.error(f"get_doctor_by_id failed: {e}")
        return None


async def add_doctor(clinic_id: str, name: str, speciality: str,
                     consultation_fee: int = 300,
                     schedule_days: list = None,
                     schedule_sessions: list = None) -> Optional[dict]:
    payload = {
        "clinic_id": clinic_id,
        "name": name,
        "speciality": speciality,
        "consultation_fee": consultation_fee,
        "schedule_days": schedule_days or ["mon", "tue", "wed", "thu", "fri"],
        "schedule_sessions": schedule_sessions or ["morning"],
        "status": "offline"
    }
    try:
        result = supabase.table("doctors").insert(payload).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"add_doctor failed: {e}")
        return None


async def update_doctor_status(doctor_id: str, status: str) -> Optional[dict]:
    try:
        result = (
            supabase.table("doctors")
            .update({"status": status})
            .eq("id", doctor_id)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"update_doctor_status failed: {e}")
        return None


async def delete_doctor(doctor_id: str) -> bool:
    try:
        supabase.table("doctors").delete().eq("id", doctor_id).execute()
        return True
    except Exception as e:
        logger.error(f"delete_doctor failed: {e}")
        return False