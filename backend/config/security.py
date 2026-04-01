"""
MedicoAssist.it — Security Configuration
API key validation, encryption, and security utilities.
"""

import os
import hmac
import hashlib
import logging
import secrets
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# API Key Validation
# ============================================================
def get_valid_api_keys() -> list:
    """Get list of valid API keys from environment."""
    keys_str = os.getenv("VALID_API_KEYS", "")
    if not keys_str:
        return []
    return [k.strip() for k in keys_str.split(",") if k.strip()]


def validate_api_key(api_key: str) -> bool:
    """Validate an API key against the configured valid keys."""
    valid_keys = get_valid_api_keys()
    if not valid_keys:
        logger.warning("Nessuna API key configurata — accesso API non protetto")
        return True  # Allow all if no keys configured
    return api_key in valid_keys


def generate_api_key(prefix: str = "ma") -> str:
    """Generate a new API key with a prefix."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"


# ============================================================
# Encryption Utilities
# ============================================================
def get_encryption_key() -> Optional[bytes]:
    """Get the Fernet encryption key from environment."""
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return key.encode()
    return None


def encrypt_sensitive_field(value: str) -> str:
    """Encrypt a sensitive field value."""
    key = get_encryption_key()
    if not key:
        logger.warning("ENCRYPTION_KEY non impostata — dati non crittografati")
        return value
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
    except ImportError:
        logger.warning("cryptography non installato — crittografia disabilitata")
        return value
    except Exception as e:
        logger.error(f"Errore durante la crittografia: {e}")
        return value


def decrypt_sensitive_field(encrypted_value: str) -> str:
    """Decrypt a sensitive field value."""
    key = get_encryption_key()
    if not key:
        return encrypted_value
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    except ImportError:
        return encrypted_value
    except Exception as e:
        logger.error(f"Errore durante la decrittografia: {e}")
        return encrypted_value


# ============================================================
# Webhook Signature Verification
# ============================================================
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC webhook signature (Stripe, Vonage, etc.)."""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ============================================================
# Security Headers
# ============================================================
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
}


# ============================================================
# Session Security
# ============================================================
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))

def is_session_expired(last_activity: datetime) -> bool:
    """Check if a session has expired based on last activity."""
    if not last_activity:
        return True
    elapsed = (datetime.utcnow() - last_activity).total_seconds() / 60
    return elapsed > SESSION_TIMEOUT_MINUTES


# ============================================================
# Input Sanitization
# ============================================================
def sanitize_input(value: str, max_length: int = 10000) -> str:
    """Basic input sanitization to prevent injection attacks."""
    if not value:
        return ""
    # Truncate
    value = value[:max_length]
    # Remove null bytes
    value = value.replace("\x00", "")
    return value.strip()


def validate_email_format(email: str) -> bool:
    """Basic email format validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_format(phone: str) -> bool:
    """Validate Italian phone number format (+39...)."""
    import re
    cleaned = phone.replace(" ", "").replace("-", "")
    # Italian mobile: +39 3xx xxx xxxx or landline: +39 0xx xxx xxxx
    pattern = r'^\+39[0-9]{9,10}$'
    return bool(re.match(pattern, cleaned))
