"""MedicoAssist.it — Patients Routes (Pazienti)"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database import get_supabase_admin
from auth import get_current_active_user
from schemas import PatientCreate, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["Pazienti"])


@router.get("/")
def list_patients(
    practice_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_active_user)
):
    """List all patients, optionally filtered by practice and search term."""
    supabase = get_supabase_admin()
    query = supabase.table("patients").select("*")

    if practice_id:
        query = query.eq("practice_id", practice_id)
    if search:
        query = query.or_(f"nome.ilike.%{search}%,cognome.ilike.%{search}%,codice_fiscale.ilike.%{search}%")

    response = query.order("cognome").execute()
    return response.data


@router.get("/{patient_id}")
def get_patient(patient_id: int, current_user=Depends(get_current_active_user)):
    """Get a single patient by ID."""
    supabase = get_supabase_admin()
    response = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return response.data


@router.post("/")
def create_patient(patient: PatientCreate, current_user=Depends(get_current_active_user)):
    """Create a new patient."""
    supabase = get_supabase_admin()

    # Validate Codice Fiscale if provided
    if patient.codice_fiscale:
        from services.appointment_tools import ItalianHealthcareValidator
        validator = ItalianHealthcareValidator()
        if not validator.validate_codice_fiscale(patient.codice_fiscale):
            raise HTTPException(status_code=400, detail="Codice Fiscale non valido")

        # Check uniqueness
        existing = supabase.table("patients").select("id").eq("codice_fiscale", patient.codice_fiscale).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail="Paziente con questo Codice Fiscale già registrato")

    patient_data = patient.model_dump()
    response = supabase.table("patients").insert(patient_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Errore durante la creazione del paziente")
    return response.data[0]


@router.put("/{patient_id}")
def update_patient(patient_id: int, patient: PatientUpdate, current_user=Depends(get_current_active_user)):
    """Update a patient."""
    supabase = get_supabase_admin()
    update_data = patient.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    if "codice_fiscale" in update_data and update_data["codice_fiscale"]:
        from services.appointment_tools import ItalianHealthcareValidator
        validator = ItalianHealthcareValidator()
        if not validator.validate_codice_fiscale(update_data["codice_fiscale"]):
            raise HTTPException(status_code=400, detail="Codice Fiscale non valido")

    response = supabase.table("patients").update(update_data).eq("id", patient_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return response.data[0]


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, current_user=Depends(get_current_active_user)):
    """Delete a patient (soft delete recommended for GDPR)."""
    supabase = get_supabase_admin()
    response = supabase.table("patients").delete().eq("id", patient_id).execute()
    return {"message": "Paziente eliminato", "id": patient_id}


@router.get("/search/cf/{codice_fiscale}")
def search_by_cf(codice_fiscale: str, current_user=Depends(get_current_active_user)):
    """Search for a patient by Codice Fiscale."""
    supabase = get_supabase_admin()
    response = supabase.table("patients").select("*").eq("codice_fiscale", codice_fiscale.upper()).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Nessun paziente trovato con questo Codice Fiscale")
    return response.data[0]
