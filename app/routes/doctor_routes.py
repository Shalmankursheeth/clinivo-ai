from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services import doctor_service

router = APIRouter()


class DoctorCreate(BaseModel):
    clinic_id: str
    name: str
    speciality: str
    consultation_fee: int = 300
    schedule_days: list[str] = ["mon", "tue", "wed", "thu", "fri"]
    schedule_sessions: list[str] = ["morning"]


@router.get("/{clinic_id}")
async def list_doctors(clinic_id: str):
    doctors = await doctor_service.get_doctors(clinic_id)
    return {"doctors": doctors}


@router.post("/")
async def create_doctor(body: DoctorCreate):
    doctor = await doctor_service.add_doctor(
        clinic_id=body.clinic_id,
        name=body.name,
        speciality=body.speciality,
        consultation_fee=body.consultation_fee,
        schedule_days=body.schedule_days,
        schedule_sessions=body.schedule_sessions
    )
    return {"doctor": doctor}


@router.delete("/{doctor_id}")
async def remove_doctor(doctor_id: str):
    ok = await doctor_service.delete_doctor(doctor_id)
    return {"deleted": ok}