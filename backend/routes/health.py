"""MedicoAssist.it — Health Check Route"""

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


@router.get("/")
def root():
    return {
        "status": "online",
        "app": "MedicoAssist.it",
        "version": "1.0.0",
        "locale": "it-IT",
        "timezone": "Europe/Rome",
    }
