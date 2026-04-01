"""MedicoAssist.it — Voice Routes"""

from fastapi import APIRouter, Depends, HTTPException
from database import get_supabase_admin
from auth import get_current_active_user

router = APIRouter(prefix="/api/voice", tags=["Voce"])


@router.get("/stats/{practice_id}")
def get_voice_stats(practice_id: str, current_user=Depends(get_current_active_user)):
    """Get voice call statistics for a practice."""
    supabase = get_supabase_admin()
    response = supabase.table("voice_calls").select("*").eq("practice_id", practice_id).execute()

    calls = response.data or []
    total = len(calls)
    ai_handled = sum(1 for c in calls if c.get("ai_handled"))
    avg_duration = sum(c.get("call_duration", 0) for c in calls) / max(total, 1)

    return {
        "total_calls": total,
        "ai_handled_calls": ai_handled,
        "human_transferred_calls": total - ai_handled,
        "avg_call_duration": round(avg_duration, 1),
        "ai_handling_rate": round(ai_handled / max(total, 1) * 100, 1),
    }


@router.get("/calls/{practice_id}")
def get_voice_calls(practice_id: str, limit: int = 50, current_user=Depends(get_current_active_user)):
    """Get recent voice call logs for a practice."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("voice_calls")
        .select("*")
        .eq("practice_id", practice_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data
