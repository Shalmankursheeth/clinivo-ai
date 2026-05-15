"""
AI Brain — Clinic Logic Engine
Python port of aiBrainV2.js with proper async throughout.

Handles all conversation intents:
  fees, doctor availability, speciality routing, schedule resolution,
  alternative doctor requests, clinic info, smalltalk, unknown fallback
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services import doctor_service

logger = logging.getLogger(__name__)

DAYS_MAP = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]


async def run(intents: list, entities: dict, session: dict, clinic_id: str, message: str = "") -> str:
    message = (message or "").lower()
    doctors = await doctor_service.get_doctors(clinic_id)
    data = session.get("data", {})

    # ── Smalltalk ─────────────────────────────────────────────────────────────
    if "smalltalk" in intents:
        return "Seri sir 😊 Vera help venuma?"

    # ── Token block (no token system in this deployment) ─────────────────────
    if "book_token" in intents:
        return "Token system inga illa. Neenga direct-aa clinic ku vaanga sir."

    # ── Fees ──────────────────────────────────────────────────────────────────
    if "fees" in intents:
        doctor_name = entities.get("doctor_name_normalized") or data.get("doctor")
        if doctor_name:
            doctor = _find_doctor_by_name(doctors, doctor_name)
            if doctor:
                return f"{doctor['name']} consultation fee ₹{doctor['consultation_fee']} sir."
        if doctors:
            fee_list = "\n".join(f"{d['name']} — ₹{d['consultation_fee']}" for d in doctors)
            return f"Doctor fees:\n{fee_list}"
        return "Fee details clinic-la kettu confirm pannunga sir."

    # ── Clinic info ───────────────────────────────────────────────────────────
    if "clinic_info" in intents:
        return "Clinic morning 9 mani open aagum, evening 8 mani close aagum sir."

    # ── Other services fallback ───────────────────────────────────────────────
    other_keywords = ["lab", "test", "scan", "xray", "blood", "report", "checkup"]
    if "unknown" in intents or any(w in message for w in other_keywords):
        return "Clinic ku morning 9 mani ku vaanga sir. Anga details solluvaanga."

    # ── Speciality reset ──────────────────────────────────────────────────────
    if entities.get("speciality_normalized"):
        data["speciality"] = entities["speciality_normalized"]
        data["doctor"] = None

    # ── Correction ────────────────────────────────────────────────────────────
    if entities.get("is_correction"):
        data["doctor"] = None

    # ── Alternative doctor ────────────────────────────────────────────────────
    if entities.get("need_alternative") or "ask_alternative" in intents:
        return await _handle_alternative(doctors, data)

    # ── Resolve by speciality ─────────────────────────────────────────────────
    speciality = data.get("speciality") or entities.get("speciality_normalized")
    if speciality:
        filtered = [d for d in doctors if speciality.lower() in (d.get("speciality") or "").lower()]
        if not filtered:
            return f"Inga {speciality} doctor illa sir."
        doctor = filtered[0]
        data["doctor"] = doctor["name"]
        session["data"] = data
        next_slot = _get_next_available(doctor, data)
        return f"{doctor['name']} {next_slot} varuvaanga sir."

    # ── Resolve by doctor name ────────────────────────────────────────────────
    doctor_name = data.get("doctor") or entities.get("doctor_name_normalized")
    doctor = _find_doctor_by_name(doctors, doctor_name) if doctor_name else None

    if not doctor:
        names = ", ".join(d["name"] for d in doctors)
        return f"Endha doctor venum sir? {names}"

    next_slot = _get_next_available(doctor, data)
    return f"{doctor['name']} {next_slot} varuvaanga sir. Neenga appo clinic ku vaanga."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_doctor_by_name(doctors: list, name: str) -> Optional[dict]:
    if not name:
        return None
    name_lower = name.lower()
    return next((d for d in doctors if name_lower in d["name"].lower()), None)


async def _handle_alternative(doctors: list, data: dict) -> str:
    if not data.get("speciality") and not data.get("doctor"):
        names = ", ".join(d["name"] for d in doctors)
        return f"Available doctors: {names}"

    if data.get("doctor"):
        current = _find_doctor_by_name(doctors, data["doctor"])
        if not current:
            return "Doctor details kedaikala sir."
        same_spec = [d for d in doctors if d.get("speciality") == current.get("speciality") and d["id"] != current["id"]]
        if not same_spec:
            return f"Inga {current.get('speciality', 'same')} ku vera doctor illa sir."
        names = ", ".join(d["name"] for d in same_spec)
        return f"Vera {current.get('speciality')} doctor irukaanga: {names}"

    if data.get("speciality"):
        filtered = [d for d in doctors if data["speciality"].lower() in (d.get("speciality") or "").lower()]
        names = ", ".join(d["name"] for d in filtered)
        return f"Inga {data['speciality']} doctor irukaanga: {names}"

    return "Doctor details sollunga sir."


def _get_next_available(doctor: dict, data: dict) -> str:
    """Find next available session for doctor based on schedule."""
    schedule_days = doctor.get("schedule_days") or []
    schedule_sessions = doctor.get("schedule_sessions") or ["morning"]

    today = datetime.now().weekday()
    # Python weekday: Mon=0, Sun=6 — convert to DAYS_MAP (Sun=0)
    today_idx = (today + 1) % 7

    start_offset = 0
    if data.get("date") == "tomorrow":
        start_offset = 1

    for i in range(start_offset, 7):
        day_idx = (today_idx + i) % 7
        day = DAYS_MAP[day_idx]

        if day not in schedule_days:
            continue

        session_pref = data.get("time_preference")
        session = None

        if session_pref:
            if session_pref in schedule_sessions:
                session = session_pref
            else:
                continue
        else:
            session = schedule_sessions[0]

        time_text = "saayangaalam 5 mani" if session == "evening" else "kalaila 9 mani"

        if i == 0:
            return f"innaiku {time_text}"
        if i == 1:
            return f"nalai {time_text}"
        return f"{day} {time_text}"

    return "schedule confirm pannum, clinic-la kettu vaanga sir"