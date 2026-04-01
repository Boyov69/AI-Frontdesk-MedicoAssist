"""MedicoAssist.it — Supabase Database Client"""

from supabase import create_client, Client
import os

# Supabase settings from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client (lazy)
_supabase: Client = None
_supabase_admin: Client = None

def get_supabase_client() -> Client:
    """Returns the Supabase client (anon key)."""
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

def get_supabase_admin() -> Client:
    """Returns the Supabase admin client (service role key)."""
    global _supabase_admin
    if _supabase_admin is None and SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin
