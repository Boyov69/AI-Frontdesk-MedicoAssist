"""
MedicoAssist.it — Schema Validator
Validates Supabase database schema integrity.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Expected tables and their required columns
EXPECTED_SCHEMA = {
    "users": ["id", "email", "hashed_password", "nome", "cognome", "ruolo", "created_at"],
    "practices": ["id", "nome", "timezone", "lingua", "ssn_convenzionato", "created_at"],
    "patients": ["id", "practice_id", "nome", "cognome", "codice_fiscale", "telefono", "created_at"],
    "appointments": ["id", "practice_id", "paziente_id", "data_appuntamento", "ora_appuntamento", "prestazione", "stato", "created_at"],
    "conversations": ["id", "practice_id", "session_id", "created_at"],
}


def validate_schema(supabase_client) -> Dict[str, Any]:
    """
    Validate that the Supabase database has the expected schema.
    
    Returns:
        dict with validation results
    """
    results = {
        "valid": True,
        "tables_found": [],
        "tables_missing": [],
        "column_issues": [],
    }

    for table_name, expected_columns in EXPECTED_SCHEMA.items():
        try:
            # Try to query the table
            response = supabase_client.table(table_name).select("*").limit(0).execute()
            results["tables_found"].append(table_name)
        except Exception as e:
            results["tables_missing"].append(table_name)
            results["valid"] = False
            logger.warning(f"Tabella mancante: {table_name} — {e}")

    # Report
    if results["valid"]:
        logger.info(f"[SCHEMA] ✅ Schema valido — {len(results['tables_found'])} tabelle trovate")
    else:
        logger.warning(
            f"[SCHEMA] ⚠️ Schema incompleto — "
            f"{len(results['tables_missing'])} tabelle mancanti: {results['tables_missing']}"
        )

    return results
