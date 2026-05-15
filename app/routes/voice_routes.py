from fastapi import APIRouter, Request
from app.services.twilio_voice_controller import handle_incoming, process_call, handle_status

router = APIRouter()

router.post("/incoming")(handle_incoming)
router.post("/process")(process_call)
router.post("/status")(handle_status)