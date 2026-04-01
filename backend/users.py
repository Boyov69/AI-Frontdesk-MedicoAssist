"""MedicoAssist.it — User Management Routes"""

from fastapi import APIRouter, Depends, HTTPException, status

from database import get_supabase_admin
from auth import get_current_active_user
from schemas import UserUpdate

router = APIRouter(prefix="/api/users", tags=["Utenti"])


@router.get("/me")
def read_current_user(current_user=Depends(get_current_active_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.put("/me")
def update_current_user(user_update: UserUpdate, current_user=Depends(get_current_active_user)):
    """Update the current user's profile."""
    supabase = get_supabase_admin()
    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        from auth import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    response = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
    return response.data[0] if response.data else current_user


@router.get("/")
def list_users(current_user=Depends(get_current_active_user)):
    """List all users (admin only)."""
    if current_user.get("ruolo") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permessi insufficienti"
        )

    supabase = get_supabase_admin()
    response = supabase.table("users").select("id, email, nome, cognome, ruolo, created_at").execute()
    return response.data
