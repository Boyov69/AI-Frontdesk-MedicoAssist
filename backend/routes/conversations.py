"""MedicoAssist.it — Conversations Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database import get_supabase_admin
from auth import get_current_active_user

router = APIRouter(prefix="/api/conversations", tags=["Conversazioni"])


@router.get("/")
def list_conversations(
    practice_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_user=Depends(get_current_active_user)
):
    """List conversation logs."""
    supabase = get_supabase_admin()
    query = supabase.table("conversations").select("*")
    if practice_id:
        query = query.eq("practice_id", practice_id)
    response = query.order("created_at", desc=True).limit(limit).execute()
    return response.data


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, current_user=Depends(get_current_active_user)):
    """Get a single conversation by ID."""
    supabase = get_supabase_admin()
    response = supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return response.data
