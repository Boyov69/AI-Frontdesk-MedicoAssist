"""MedicoAssist.it — Pydantic Schemas

Italian healthcare schemas with Codice Fiscale support.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ============================================================
# User schemas
# ============================================================
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nome: str = ""
    cognome: str = ""
    ruolo: str = "fisioterapista"  # fisioterapista | admin | segretaria

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    nome: Optional[str] = None
    cognome: Optional[str] = None
    ruolo: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    nome: str
    cognome: str
    ruolo: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Patient schemas (Pazienti)
# ============================================================
class PatientCreate(BaseModel):
    nome: str
    cognome: str
    codice_fiscale: Optional[str] = None  # CF — 16 chars
    tessera_sanitaria: Optional[str] = None  # TS-CNS — 20 digits
    email: Optional[EmailStr] = None
    telefono: str
    data_nascita: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    cap: Optional[str] = None
    nre: Optional[str] = None  # Numero Ricetta Elettronica
    codice_esenzione: Optional[str] = None  # E/R/G/D/I
    note_mediche: Optional[str] = None

class PatientUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    codice_fiscale: Optional[str] = None
    tessera_sanitaria: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    data_nascita: Optional[str] = None
    nre: Optional[str] = None
    codice_esenzione: Optional[str] = None
    note_mediche: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    practice_id: Optional[str] = None
    nome: str
    cognome: str
    codice_fiscale: Optional[str] = None
    email: Optional[str] = None
    telefono: str
    data_nascita: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Appointment schemas (Appuntamenti)
# ============================================================
class AppointmentCreate(BaseModel):
    paziente_id: int
    fisioterapista_nome: str
    fisioterapista_id: Optional[int] = None
    data_appuntamento: str  # YYYY-MM-DD
    ora_appuntamento: str   # HH:MM
    prestazione: str        # e.g. "FKT_001"
    durata_minuti: int = 45
    motivo: Optional[str] = None
    nre: Optional[str] = None
    codice_esenzione: Optional[str] = None
    ticket_eur: Optional[float] = None
    stato: str = "confermato"

class AppointmentUpdate(BaseModel):
    data_appuntamento: Optional[str] = None
    ora_appuntamento: Optional[str] = None
    prestazione: Optional[str] = None
    durata_minuti: Optional[int] = None
    motivo: Optional[str] = None
    nre: Optional[str] = None
    codice_esenzione: Optional[str] = None
    ticket_eur: Optional[float] = None
    stato: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    practice_id: Optional[str] = None
    paziente_id: int
    fisioterapista_nome: str
    data_appuntamento: str
    ora_appuntamento: str
    prestazione: str
    durata_minuti: int
    stato: str
    ticket_eur: Optional[float] = None
    nre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Token schema
# ============================================================
class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# Voice Call Statistics schemas
# ============================================================
class VoiceCallLog(BaseModel):
    id: str
    session_id: str
    practice_id: str
    caller_phone: Optional[str] = None
    caller_name: Optional[str] = None
    call_duration: int = 0
    call_type: str = "generale"
    ai_handled: bool = False
    appointment_created: bool = False
    appointment_id: Optional[int] = None
    transcription: Optional[str] = None
    codice_fiscale_verificato: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VoiceCallStats(BaseModel):
    total_calls: int = 0
    ai_handled_calls: int = 0
    human_transferred_calls: int = 0
    avg_call_duration: float = 0.0
    cf_verification_success_rate: float = 0.0
    appointment_conversion_rate: float = 0.0
    error_rate: float = 0.0
    peak_hours: List[dict] = []
    call_types_distribution: dict = {}
    daily_stats: List[dict] = []
    last_updated: datetime

    class Config:
        from_attributes = True


# ============================================================
# Practice schemas (Studio fisioterapico)
# ============================================================
class PracticeCreate(BaseModel):
    nome: str
    partita_iva: Optional[str] = None
    codice_fiscale_studio: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    cap: Optional[str] = None
    regione: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    asl_convenzione: Optional[str] = None
    ssn_convenzionato: bool = True
    timezone: str = "Europe/Rome"
    lingua: str = "it"

class PracticeResponse(BaseModel):
    id: str
    nome: str
    partita_iva: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    regione: Optional[str] = None
    ssn_convenzionato: bool
    timezone: str
    lingua: str
    created_at: datetime

    class Config:
        from_attributes = True
