"""
MedicoAssist.it — Core Configuration
Central settings, security utilities, and default practice configuration.
"""

import os
from datetime import timedelta
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

# ============================================================
# JWT Configuration
# ============================================================
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_only_medicoassist_change_in_production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))

security = HTTPBearer()


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


# ============================================================
# Default Practice (for development/testing)
# ============================================================
DEFAULT_PRACTICE = {
    "id": "practice_medicoassist_default",
    "nome": "Studio Fisioterapico Demo",
    "indirizzo": "Via Roma, 42",
    "citta": "Milano",
    "provincia": "MI",
    "regione": "Lombardia",
    "cap": "20121",
    "telefono": "+39 02 1234 5678",
    "email": "info@studiodemo.it",
    "partita_iva": "IT12345678901",
    "ssn_convenzionato": True,
    "asl_convenzione": "ASL Milano",
    "timezone": "Europe/Rome",
    "lingua": "it",
    "orari_apertura": {
        "lunedì": {"apertura": "08:00", "chiusura": "19:00"},
        "martedì": {"apertura": "08:00", "chiusura": "19:00"},
        "mercoledì": {"apertura": "08:00", "chiusura": "19:00"},
        "giovedì": {"apertura": "08:00", "chiusura": "19:00"},
        "venerdì": {"apertura": "08:00", "chiusura": "18:00"},
        "sabato": {"apertura": "09:00", "chiusura": "13:00"},
        "domenica": None,
    },
    "ai_assistant": {
        "nome": "Anna",
        "lingua": "it-IT",
        "voce": "it-IT-ElsaNeural",
    },
}

# ============================================================
# App Configuration
# ============================================================
APP_CONFIG = {
    "name": "MedicoAssist.it",
    "version": "1.0.0",
    "locale": "it-IT",
    "timezone": "Europe/Rome",
    "country": "IT",
    "currency": "EUR",
    "healthcare_system": "SSN",
    "patient_id_type": "Codice Fiscale",
}
