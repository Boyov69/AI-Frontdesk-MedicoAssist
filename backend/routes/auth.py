"""MedicoAssist.it — Auth Routes"""

from fastapi import APIRouter
from auth import router as auth_router

# Re-export the auth router from auth.py
router = auth_router
