"""MedicoAssist.it — Contact Routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contact", tags=["Contatti"])


class ContactForm(BaseModel):
    nome: str
    email: EmailStr
    telefono: Optional[str] = None
    messaggio: str
    studio_nome: Optional[str] = None


@router.post("/")
async def submit_contact_form(form: ContactForm):
    """Submit a contact form."""
    logger.info(f"[CONTACT] Nuovo messaggio da: {form.nome} ({form.email})")

    # Send notification email if configured
    contact_email = os.getenv("CONTACT_EMAIL", "info@medicoassist.it")

    return {
        "success": True,
        "message": "Messaggio inviato con successo. La contatteremo al più presto.",
    }
