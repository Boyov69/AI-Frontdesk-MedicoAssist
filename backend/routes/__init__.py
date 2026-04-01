"""MedicoAssist.it — Health Check & Root Routes"""

from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/api/health")
def health():
    return {
        "status": "healthy",
        "app": "MedicoAssist.it",
        "version": "1.0.0",
        "locale": "it-IT",
        "timezone": "Europe/Rome",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/api/info")
def info():
    return {
        "app": "MedicoAssist.it",
        "description": "AI-Powered Virtual Receptionist per Fisioterapisti in Italia",
        "version": "1.0.0",
        "locale": "it-IT",
        "timezone": "Europe/Rome",
        "healthcare": {
            "system": "SSN (Servizio Sanitario Nazionale)",
            "patient_id": "Codice Fiscale (CF)",
            "prescription": "Ricetta Dematerializzata (NRE)",
            "privacy": "GDPR + GARANTE (D.Lgs. 196/2003)",
        },
    }
