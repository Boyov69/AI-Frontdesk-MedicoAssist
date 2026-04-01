"""MedicoAssist.it — Appointments Routes (Appuntamenti)"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database import get_supabase_admin
from auth import get_current_active_user
from schemas import AppointmentCreate, AppointmentUpdate

router = APIRouter(prefix="/api/appointments", tags=["Appuntamenti"])


@router.get("/")
def list_appointments(
    practice_id: Optional[str] = Query(None),
    paziente_id: Optional[int] = Query(None),
    data: Optional[str] = Query(None),
    stato: Optional[str] = Query(None),
    current_user=Depends(get_current_active_user)
):
    """List appointments with optional filters."""
    supabase = get_supabase_admin()
    query = supabase.table("appointments").select("*")

    if practice_id:
        query = query.eq("practice_id", practice_id)
    if paziente_id:
        query = query.eq("paziente_id", paziente_id)
    if data:
        query = query.eq("data_appuntamento", data)
    if stato:
        query = query.eq("stato", stato)

    response = query.order("data_appuntamento", desc=True).execute()
    return response.data


@router.get("/{appointment_id}")
def get_appointment(appointment_id: int, current_user=Depends(get_current_active_user)):
    """Get a single appointment by ID."""
    supabase = get_supabase_admin()
    response = supabase.table("appointments").select("*").eq("id", appointment_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return response.data


@router.post("/")
def create_appointment(appt: AppointmentCreate, current_user=Depends(get_current_active_user)):
    """Create a new appointment."""
    supabase = get_supabase_admin()

    # Validate NRE if provided
    if appt.nre:
        from services.appointment_tools import ItalianHealthcareValidator
        validator = ItalianHealthcareValidator()
        if not validator.validate_nre(appt.nre):
            raise HTTPException(status_code=400, detail="Numero Ricetta Elettronica (NRE) non valido")

    # Calculate ticket if esenzione provided
    if appt.codice_esenzione and appt.ticket_eur is None:
        from services.appointment_tools import AppointmentManager
        manager = AppointmentManager()
        appt_data = appt.model_dump()
        ticket = manager._calcola_ticket(appt_data)
        appt_data["ticket_eur"] = ticket
    else:
        appt_data = appt.model_dump()

    response = supabase.table("appointments").insert(appt_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Errore durante la creazione dell'appuntamento")

    return response.data[0]


@router.put("/{appointment_id}")
def update_appointment(appointment_id: int, appt: AppointmentUpdate, current_user=Depends(get_current_active_user)):
    """Update an appointment."""
    supabase = get_supabase_admin()
    update_data = appt.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    response = supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return response.data[0]


@router.delete("/{appointment_id}")
def cancel_appointment(appointment_id: int, current_user=Depends(get_current_active_user)):
    """Cancel an appointment (sets status to 'annullato')."""
    supabase = get_supabase_admin()
    response = supabase.table("appointments").update({"stato": "annullato"}).eq("id", appointment_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return {"message": "Appuntamento annullato", "id": appointment_id}


@router.get("/today/{practice_id}")
def get_today_appointments(practice_id: str, current_user=Depends(get_current_active_user)):
    """Get today's appointments for a practice."""
    from datetime import date
    today = date.today().isoformat()
    supabase = get_supabase_admin()
    response = (
        supabase.table("appointments")
        .select("*")
        .eq("practice_id", practice_id)
        .eq("data_appuntamento", today)
        .order("ora_appuntamento")
        .execute()
    )
    return response.data
