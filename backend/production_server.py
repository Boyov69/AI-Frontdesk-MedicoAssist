"""
MedicoAssist.it Production Server
App factory — imports, service init, CORS, router registration.
All endpoint logic lives in routes/*.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import re
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# SENTRY ERROR TRACKING
# ============================================================
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    SENTRY_DSN = os.getenv("SENTRY_DSN")

    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            enable_tracing=True,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development"),
            release="medicoassist@1.0.0",
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
            ],
            before_send=lambda event, hint: _filter_sensitive_data(event),
        )
        print("[SENTRY] ✅ Error tracking initialized")
        print(f"[SENTRY]    Environment: {os.getenv('ENVIRONMENT', 'development')}")
    else:
        print("[SENTRY] ⚠️ SENTRY_DSN not set - error tracking disabled")
except ImportError:
    print("[SENTRY] ⚠️ sentry-sdk not installed - error tracking disabled")

def _filter_sensitive_data(event):
    """Remove sensitive data before sending to Sentry"""
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            headers = request["headers"]
            if isinstance(headers, dict):
                headers.pop("authorization", None)
                headers.pop("x-api-key", None)
    return event

# Validate environment variables at startup
try:
    from config.env_validator import validate_environment, get_config_status
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    validate_environment(strict=is_production)
except ImportError:
    print("[WARNING] Environment validator not found, skipping validation")
except SystemExit:
    raise

# ============================================================
# SERVICE INITIALIZATION
# ============================================================
from database import get_supabase_client

# Vonage telephony (Italian +39 numbers)
vonage_api_key = os.getenv('VONAGE_API_KEY')
vonage_api_secret = os.getenv('VONAGE_API_SECRET')
vonage_application_id = os.getenv('VONAGE_APPLICATION_ID')
if vonage_api_key and vonage_api_secret:
    print(f"[OK] Vonage initialized (Application: {vonage_application_id})")
else:
    print("[WARN] Vonage credentials not found in .env")

# Optional: Stripe payments
try:
    import stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if stripe.api_key:
        print("[OK] Stripe payment service initialized")
    else:
        print("[WARN] Stripe secret key not set")
except ImportError:
    print("[WARN] stripe package not installed")

print("[OK] MedicoAssist services initialized")

# ============================================================
# INFRASTRUCTURE HARDENING
# ============================================================
async def keep_db_alive():
    """DB Keep-Alive: lightweight query every 10 min to prevent idle disconnects."""
    print("[SYSTEM] 💓 Database Keep-Alive service avviato")
    while True:
        try:
            await asyncio.sleep(600)
            supabase = get_supabase_client()
            if supabase:
                response = supabase.table("practices").select("id").limit(1).execute()
                print("[SYSTEM] 💓 DB Ping riuscito - Connessione attiva")
        except Exception as e:
            print(f"[SYSTEM] ⚠️ DB Ping fallito: {e}")

@asynccontextmanager
async def lifespan(app):
    """FastAPI Lifespan Manager — startup/shutdown tasks."""
    print("[SYSTEM] 🚀 MedicoAssist server in avvio...")
    keep_alive_task = asyncio.create_task(keep_db_alive())

    print("[SYSTEM] ✅ Infrastruttura attiva:")
    print("[SYSTEM]    - DB Keep-Alive: ogni 10 minuti")
    print("[SYSTEM]    - Timezone: Europe/Rome")
    print("[SYSTEM]    - Lingua: it-IT")

    yield  # Server is running

    print("[SYSTEM] 🛑 Server in arresto...")
    keep_alive_task.cancel()
    try:
        await keep_alive_task
    except asyncio.CancelledError:
        pass
    print("[SYSTEM] ✅ Cleanup completato")

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="MedicoAssist.it API",
    description="AI-Powered Virtual Receptionist per Fisioterapisti in Italia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register centralized error handlers
try:
    from middleware.error_handlers import register_error_handlers
    register_error_handlers(app)
except ImportError:
    print("[WARN] Error handlers module not found, using defaults")

# CORS — whitelist + Vercel preview pattern
ALLOWED_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:3001", "http://127.0.0.1:3001",
    "http://localhost:8001", "http://127.0.0.1:8001",
    "https://www.medicoassist.it", "https://medicoassist.it",
    "https://www.fisioterapiassist.it", "https://fisioterapiassist.it",
    "null",
]

VERCEL_PATTERN = re.compile(
    r'^https://(medicoassist|fisioterapiassist)[a-z0-9-]*\.vercel\.app$'
)

def is_allowed_origin(origin: str) -> bool:
    if origin in ALLOWED_ORIGINS:
        return True
    if VERCEL_PATTERN.match(origin):
        return True
    extra_origins = os.getenv("ALLOWED_ORIGINS", "")
    if extra_origins and origin in extra_origins.split(","):
        return True
    return False

class CustomCORSMiddleware(CORSMiddleware):
    def is_allowed_origin(self, origin: str) -> bool:
        return is_allowed_origin(origin)

app.add_middleware(
    CustomCORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r'^https://(medicoassist|fisioterapiassist)[a-z0-9-]*\.vercel\.app$',
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# ============================================================
# ROUTER REGISTRATION
# ============================================================

# Route registrations (graceful fallback if modules missing)
def _safe_include_router(app, module_path, router_attr="router", **kwargs):
    """Safely include a router, logging a warning if the module is missing."""
    try:
        import importlib
        module = importlib.import_module(module_path)
        router = getattr(module, router_attr)
        app.include_router(router, **kwargs)
        print(f"[OK] Router loaded: {module_path}")
    except (ImportError, AttributeError) as e:
        print(f"[WARN] Could not load router {module_path}: {e}")

_safe_include_router(app, "routes.health", tags=["Health & Root"])
_safe_include_router(app, "routes.auth", tags=["Authentication"])
_safe_include_router(app, "routes.patients", tags=["Pazienti"])
_safe_include_router(app, "routes.appointments", tags=["Appuntamenti"])
_safe_include_router(app, "routes.practices", tags=["Studi"])
_safe_include_router(app, "routes.voice", tags=["Voce"])
_safe_include_router(app, "routes.conversations", tags=["Conversazioni"])
_safe_include_router(app, "routes.payments", tags=["Pagamenti"])
_safe_include_router(app, "routes.usage", tags=["Utilizzo"])
_safe_include_router(app, "routes.contact", tags=["Contatti"])
_safe_include_router(app, "routes.users", tags=["Utenti"])

# Vonage endpoints (Italian telephony)
try:
    from api.vonage_endpoints import router as vonage_router
    app.include_router(vonage_router)
    print("[OK] Vonage API endpoints loaded")
except Exception as e:
    print(f"[WARN] Could not load Vonage endpoints: {e}")


# ============================================================
# HEALTH CHECK (inline fallback)
# ============================================================
@app.get("/")
def root():
    return {
        "status": "online",
        "app": "MedicoAssist.it",
        "version": "1.0.0",
        "locale": "it-IT",
        "timezone": "Europe/Rome"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "MedicoAssist.it",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"Avvio MedicoAssist.it Production Server sulla porta {port}")
    print(f"Frontend connesso a: http://localhost:{port}")
    print(f"Documentazione API: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
