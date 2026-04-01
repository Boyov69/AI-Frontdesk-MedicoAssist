"""
MedicoAssist.it — Core Dependencies
FastAPI dependency injection functions.
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.config import security, verify_token


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user with practice isolation."""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        practice_id = payload.get("practice_id")

        if user_id is None or practice_id is None:
            raise HTTPException(status_code=401, detail="Token di autenticazione non valido")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "practice_id": practice_id,
            "ruolo": payload.get("ruolo", "fisioterapista"),
            "is_admin": payload.get("is_admin", False),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")
