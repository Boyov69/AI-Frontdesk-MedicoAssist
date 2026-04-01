"""MedicoAssist.it — Usage Routes (Utilizzo)"""

from fastapi import APIRouter, Depends
from auth import get_current_active_user
from database import get_supabase_admin

router = APIRouter(prefix="/api/usage", tags=["Utilizzo"])


@router.get("/{practice_id}")
def get_usage(practice_id: str, current_user=Depends(get_current_active_user)):
    """Get usage statistics for a practice."""
    supabase = get_supabase_admin()

    # Count patients
    patients = supabase.table("patients").select("id", count="exact").eq("practice_id", practice_id).execute()
    # Count appointments this month
    from datetime import date
    first_of_month = date.today().replace(day=1).isoformat()
    appointments = (
        supabase.table("appointments").select("id", count="exact")
        .eq("practice_id", practice_id)
        .gte("data_appuntamento", first_of_month)
        .execute()
    )

    return {
        "practice_id": practice_id,
        "total_patients": patients.count or 0,
        "appointments_this_month": appointments.count or 0,
    }


@router.get("/{practice_id}/users")
def get_users_route(practice_id: str, current_user=Depends(get_current_active_user)):
    """Redirect to users endpoint."""
    return {"message": "Use /api/users/ for user management"}
