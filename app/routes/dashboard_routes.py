from fastapi import APIRouter
from app.db.supabase_client import supabase

router = APIRouter()


@router.get("/{clinic_id}")
async def get_dashboard(clinic_id: str):
    doctors = supabase.table("doctors").select("*").eq("clinic_id", clinic_id).execute()
    return {
        "clinic_id": clinic_id,
        "doctors": doctors.data or [],
        "total_doctors": len(doctors.data or [])
    }