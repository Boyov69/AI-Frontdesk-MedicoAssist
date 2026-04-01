"""
MedicoAssist.it — Environment Variable Validator
Validates required environment variables at startup.
"""

import os
import sys

# Required env vars for a working deployment
REQUIRED_VARS = {
    "SUPABASE_URL": "Supabase project URL",
    "SUPABASE_KEY": "Supabase anon key",
    "GEMINI_API_KEY": "Google Gemini API key",
}

# Optional but recommended
RECOMMENDED_VARS = {
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key (admin operations)",
    "JWT_SECRET_KEY": "JWT signing secret (MUST be set in production)",
    "SENTRY_DSN": "Sentry error tracking DSN",
    "VONAGE_API_KEY": "Vonage telephony API key",
    "VONAGE_API_SECRET": "Vonage telephony API secret",
    "STRIPE_SECRET_KEY": "Stripe payment secret key",
    "SMTP_HOST": "SMTP server for email",
}

# Production-only required
PRODUCTION_REQUIRED = {
    "JWT_SECRET_KEY": "JWT signing secret",
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key",
}


def validate_environment(strict: bool = False) -> dict:
    """
    Validate environment variables at startup.
    
    Args:
        strict: If True (production), missing required vars cause exit.
    
    Returns:
        dict with validation results
    """
    missing_required = []
    missing_recommended = []
    missing_production = []

    for var, desc in REQUIRED_VARS.items():
        if not os.getenv(var):
            missing_required.append(f"  ❌ {var}: {desc}")

    for var, desc in RECOMMENDED_VARS.items():
        if not os.getenv(var):
            missing_recommended.append(f"  ⚠️ {var}: {desc}")

    if strict:
        for var, desc in PRODUCTION_REQUIRED.items():
            if not os.getenv(var):
                missing_production.append(f"  🔴 {var}: {desc}")

    # Report
    if missing_required:
        print("[ENV] ❌ Variabili d'ambiente obbligatorie mancanti:")
        for msg in missing_required:
            print(msg)
        if strict:
            print("[ENV] 🛑 Impossibile avviare in modalità produzione senza le variabili obbligatorie.")
            sys.exit(1)

    if missing_production:
        print("[ENV] 🔴 Variabili obbligatorie per la produzione:")
        for msg in missing_production:
            print(msg)
        if strict:
            sys.exit(1)

    if missing_recommended:
        print("[ENV] ⚠️ Variabili consigliate non impostate:")
        for msg in missing_recommended:
            print(msg)

    if not missing_required and not missing_production:
        print("[ENV] ✅ Tutte le variabili d'ambiente richieste sono presenti")

    return {
        "missing_required": len(missing_required),
        "missing_recommended": len(missing_recommended),
        "missing_production": len(missing_production),
    }


def get_config_status() -> dict:
    """Get current configuration status for health endpoint."""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "vonage_configured": bool(os.getenv("VONAGE_API_KEY")),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "smtp_configured": bool(os.getenv("SMTP_HOST")),
        "sentry_configured": bool(os.getenv("SENTRY_DSN")),
        "jwt_configured": bool(os.getenv("JWT_SECRET_KEY")),
    }
