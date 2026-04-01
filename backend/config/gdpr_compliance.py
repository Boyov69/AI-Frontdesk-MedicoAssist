"""
MedicoAssist.it — GDPR & GARANTE Privacy Compliance Module

Italian healthcare data protection rules:
- EU GDPR (General Data Protection Regulation)
- D.Lgs. 196/2003 (Codice Privacy italiano)
- D.Lgs. 101/2018 (Adeguamento GDPR)
- Garante per la protezione dei dati personali
- Fascicolo Sanitario Elettronico (FSE) regulations
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================================
# GDPR Data Categories (Italian Healthcare)
# ============================================================
SENSITIVE_FIELDS = {
    "codice_fiscale",
    "tessera_sanitaria",
    "data_nascita",
    "indirizzo",
    "telefono",
    "email",
    "note_mediche",
    "nre",  # Numero Ricetta Elettronica
    "codice_esenzione",
    "anamnesi",
    "diagnosi",
    "terapia",
}

PII_FIELDS = {
    "nome",
    "cognome",
    "codice_fiscale",
    "tessera_sanitaria",
    "email",
    "telefono",
    "indirizzo",
    "data_nascita",
}

HEALTH_DATA_FIELDS = {
    "note_mediche",
    "nre",
    "codice_esenzione",
    "anamnesi",
    "diagnosi",
    "terapia",
    "prestazione",
}


# ============================================================
# Data Retention Policies (Italian Healthcare)
# ============================================================
RETENTION_POLICIES = {
    "patient_data": {
        "retention_years": 10,  # D.Lgs. 196/2003 — healthcare records
        "description": "Dati paziente (conservazione obbligatoria 10 anni)",
    },
    "appointment_data": {
        "retention_years": 10,
        "description": "Dati appuntamenti (conservazione obbligatoria)",
    },
    "conversation_logs": {
        "retention_days": 90,
        "description": "Log conversazioni AI (90 giorni per audit)",
    },
    "voice_recordings": {
        "retention_days": 30,
        "description": "Registrazioni vocali (30 giorni, consenso esplicito richiesto)",
    },
    "access_logs": {
        "retention_days": 365,
        "description": "Log di accesso (1 anno per sicurezza)",
    },
    "consent_records": {
        "retention_years": 10,
        "description": "Registri del consenso (conservazione obbligatoria)",
    },
}


# ============================================================
# Consent Types (Italian Healthcare)
# ============================================================
class ConsentType:
    TRATTAMENTO_DATI = "trattamento_dati_personali"  # Art. 6 GDPR
    DATI_SANITARI = "trattamento_dati_sanitari"       # Art. 9 GDPR
    COMUNICAZIONI = "comunicazioni_marketing"          # Consenso facoltativo
    AI_ASSISTENTE = "interazione_assistente_ai"        # Consenso specifico
    REGISTRAZIONE_VOCALE = "registrazione_vocale"      # Consenso esplicito
    FSE = "fascicolo_sanitario_elettronico"            # Consenso FSE


REQUIRED_CONSENTS = [
    ConsentType.TRATTAMENTO_DATI,
    ConsentType.DATI_SANITARI,
    ConsentType.AI_ASSISTENTE,
]


# ============================================================
# Data Anonymization
# ============================================================
def anonymize_patient_data(patient: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize patient data for analytics/logging (GDPR Art. 5)."""
    anonymized = patient.copy()

    for field in PII_FIELDS:
        if field in anonymized and anonymized[field]:
            if field == "codice_fiscale":
                cf = str(anonymized[field])
                anonymized[field] = f"***{cf[-4:]}" if len(cf) >= 4 else "***"
            elif field == "email":
                email = str(anonymized[field])
                parts = email.split("@")
                anonymized[field] = f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else "***"
            elif field == "telefono":
                phone = str(anonymized[field])
                anonymized[field] = f"***{phone[-4:]}" if len(phone) >= 4 else "***"
            else:
                anonymized[field] = "***"

    for field in HEALTH_DATA_FIELDS:
        if field in anonymized:
            anonymized[field] = "[DATI_SANITARI_RIMOSSI]"

    return anonymized


def hash_identifier(value: str) -> str:
    """Create a one-way hash of a personal identifier (for analytics)."""
    salt = os.getenv("GDPR_HASH_SALT", "medicoassist_default_salt")
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:16]


def sanitize_log_entry(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove PII from log entries before storage."""
    sanitized = log_data.copy()
    for field in PII_FIELDS | HEALTH_DATA_FIELDS:
        if field in sanitized:
            sanitized[field] = "[REDACTED]"
    return sanitized


# ============================================================
# GDPR Data Subject Rights (Art. 15-22)
# ============================================================
def get_data_export(patient_id: str, supabase_client=None) -> Dict[str, Any]:
    """
    Esporta tutti i dati di un paziente (Diritto di accesso, Art. 15 GDPR).
    """
    if not supabase_client:
        return {"error": "Database non disponibile"}

    export = {
        "export_date": datetime.utcnow().isoformat(),
        "data_controller": "MedicoAssist.it",
        "legal_basis": "Art. 15 GDPR — Diritto di accesso",
        "patient_data": {},
        "appointments": [],
        "consent_records": [],
    }

    try:
        # Patient data
        patient = supabase_client.table("patients").select("*").eq("id", patient_id).single().execute()
        if patient.data:
            export["patient_data"] = patient.data

        # Appointments
        appointments = supabase_client.table("appointments").select("*").eq("paziente_id", patient_id).execute()
        if appointments.data:
            export["appointments"] = appointments.data

    except Exception as e:
        logger.error(f"Errore durante l'esportazione dati GDPR: {e}")
        export["error"] = str(e)

    return export


def get_privacy_policy_info() -> Dict[str, Any]:
    """Return privacy policy metadata."""
    return {
        "controller": "MedicoAssist.it",
        "dpo_email": os.getenv("DPO_EMAIL", "privacy@medicoassist.it"),
        "legal_basis": [
            "Art. 6(1)(b) GDPR — Esecuzione del contratto",
            "Art. 6(1)(c) GDPR — Obbligo legale",
            "Art. 9(2)(h) GDPR — Finalità di cura della salute",
        ],
        "retention_policies": RETENTION_POLICIES,
        "data_subject_rights": [
            "Diritto di accesso (Art. 15)",
            "Diritto di rettifica (Art. 16)",
            "Diritto alla cancellazione (Art. 17)",
            "Diritto alla portabilità dei dati (Art. 20)",
            "Diritto di opposizione (Art. 21)",
        ],
        "authority": "Garante per la Protezione dei Dati Personali",
        "authority_url": "https://www.garanteprivacy.it",
    }
