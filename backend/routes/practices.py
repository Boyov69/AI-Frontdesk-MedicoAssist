"""MedicoAssist.it — Practices Routes (Studi)"""

from fastapi import APIRouter, Depends, HTTPException
from database import get_supabase_admin
from auth import get_current_active_user
from schemas import PracticeCreate

router = APIRouter(prefix="/api/practices", tags=["Studi"])


@router.get("/")
def list_practices(current_user=Depends(get_current_active_user)):
    """List all practices."""
    supabase = get_supabase_admin()
    response = supabase.table("practices").select("*").execute()
    return response.data


@router.get("/{practice_id}")
def get_practice(practice_id: str, current_user=Depends(get_current_active_user)):
    """Get a single practice by ID."""
    supabase = get_supabase_admin()
    response = supabase.table("practices").select("*").eq("id", practice_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Studio non trovato")
    return response.data


@router.post("/")
def create_practice(practice: PracticeCreate, current_user=Depends(get_current_active_user)):
    """Create a new practice."""
    supabase = get_supabase_admin()
    practice_data = practice.model_dump()
    response = supabase.table("practices").insert(practice_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Errore durante la creazione dello studio")
    return response.data[0]


@router.put("/{practice_id}")
def update_practice(practice_id: str, updates: dict, current_user=Depends(get_current_active_user)):
    """Update a practice."""
    supabase = get_supabase_admin()
    response = supabase.table("practices").update(updates).eq("id", practice_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Studio non trovato")
    return response.data[0]
