"""MedicoAssist.it — JWT Authentication Module"""

import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import get_supabase_admin

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    logger.warning(
        "JWT_SECRET_KEY non impostata. Impostarla nelle variabili d'ambiente."
    )
    SECRET_KEY = "dev_only_medicoassist_change_in_production"

if len(SECRET_KEY) < 32:
    logger.warning("JWT_SECRET_KEY dovrebbe essere almeno 32 caratteri")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user data from Supabase."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    supabase = get_supabase_admin()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database non disponibile"
        )

    response = supabase.table("users").select("*").eq("email", email).single().execute()
    if not response.data:
        raise credentials_exception
    return response.data

def get_current_active_user(current_user=Depends(get_current_user)):
    return current_user


@router.post("/login")
def login(email: str, password: str):
    """Authenticate user and return JWT token."""
    supabase = get_supabase_admin()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database non disponibile"
        )

    response = supabase.table("users").select("*").eq("email", email).single().execute()
    user = response.data
    if not user or not verify_password(password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(email: str, password: str, nome: str = "", cognome: str = ""):
    """Register a new user."""
    supabase = get_supabase_admin()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database non disponibile"
        )

    # Check if user already exists
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email già registrata")

    hashed_password = get_password_hash(password)
    new_user = supabase.table("users").insert({
        "email": email,
        "hashed_password": hashed_password,
        "nome": nome,
        "cognome": cognome,
        "ruolo": "fisioterapista",
    }).execute()

    if not new_user.data:
        raise HTTPException(status_code=500, detail="Errore durante la registrazione")

    return {"message": "Registrazione completata", "user_id": new_user.data[0]["id"]}
