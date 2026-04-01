"""
MedicoAssist.it — Supabase Service
High-level service layer for Supabase operations.
Wraps common CRUD patterns with practice isolation.
"""

import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SupabaseService:
    """High-level Supabase operations with practice isolation."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    def _get_supabase(self):
        if not self.supabase:
            try:
                from database import get_supabase_admin
                self.supabase = get_supabase_admin()
            except Exception as e:
                logger.error(f"Errore connessione Supabase: {e}")
        return self.supabase

    # ================================================================
    # Patient Operations
    # ================================================================

    def get_patient_by_cf(self, codice_fiscale: str, practice_id: Optional[str] = None) -> Optional[Dict]:
        """Find a patient by Codice Fiscale."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            query = supabase.table("patients").select("*").eq("codice_fiscale", codice_fiscale.upper())
            if practice_id:
                query = query.eq("practice_id", practice_id)
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Errore ricerca paziente CF: {e}")
            return None

    def get_patient_by_phone(self, phone: str, practice_id: Optional[str] = None) -> Optional[Dict]:
        """Find a patient by phone number."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            from utils.phone import normalize_italian_phone
            normalized = normalize_italian_phone(phone)
            query = supabase.table("patients").select("*").eq("telefono", normalized)
            if practice_id:
                query = query.eq("practice_id", practice_id)
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Errore ricerca paziente telefono: {e}")
            return None

    def create_patient(self, patient_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new patient."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            response = supabase.table("patients").insert(patient_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Errore creazione paziente: {e}")
            return None

    # ================================================================
    # Appointment Operations
    # ================================================================

    def get_appointments_by_date(self, practice_id: str, date: str) -> List[Dict]:
        """Get appointments for a specific date."""
        supabase = self._get_supabase()
        if not supabase:
            return []
        try:
            response = (
                supabase.table("appointments")
                .select("*")
                .eq("practice_id", practice_id)
                .eq("data_appuntamento", date)
                .order("ora_appuntamento")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Errore recupero appuntamenti: {e}")
            return []

    def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new appointment."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            response = supabase.table("appointments").insert(appointment_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Errore creazione appuntamento: {e}")
            return None

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        supabase = self._get_supabase()
        if not supabase:
            return False
        try:
            supabase.table("appointments").update({"stato": "annullato"}).eq("id", appointment_id).execute()
            return True
        except Exception as e:
            logger.error(f"Errore annullamento appuntamento: {e}")
            return False

    # ================================================================
    # Practice Operations
    # ================================================================

    def get_practice(self, practice_id: str) -> Optional[Dict]:
        """Get practice details."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            response = supabase.table("practices").select("*").eq("id", practice_id).single().execute()
            return response.data
        except Exception:
            return None

    def get_practice_settings(self, practice_id: str) -> Dict[str, Any]:
        """Get practice settings including AI config."""
        practice = self.get_practice(practice_id)
        if not practice:
            return {}
        return practice.get("settings", {})

    # ================================================================
    # Voice Call Logging
    # ================================================================

    def log_voice_call(self, call_data: Dict[str, Any]) -> Optional[Dict]:
        """Log a voice call."""
        supabase = self._get_supabase()
        if not supabase:
            return None
        try:
            response = supabase.table("voice_calls").insert(call_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Errore registrazione chiamata: {e}")
            return None


# Global singleton
supabase_service = SupabaseService()
