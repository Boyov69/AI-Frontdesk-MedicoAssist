"""
MedicoAssist.it — Italian Phone Number Utilities
Handles normalization of Italian phone numbers to E.164 format.
"""


def normalize_italian_phone(phone: str) -> str:
    """
    Normalize Italian phone number to E.164 format (+39...)

    Handles:
    - 347 123 4567 -> +393471234567
    - +39 347 123 4567 -> +393471234567
    - 0039 347 123 4567 -> +393471234567
    - 06 1234567 -> +3961234567 (landline)
    - 3471234567 -> +393471234567
    """
    # Remove all spaces, dashes, parentheses
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Remove leading 0039 (international format without +)
    if cleaned.startswith("0039"):
        cleaned = cleaned[2:]  # Remove "00", keep "39"
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned

    # Convert 0... (Italian landline) to +39 0...
    elif cleaned.startswith("0") and not cleaned.startswith("00"):
        cleaned = "+39" + cleaned

    # Convert 3... (Italian mobile without prefix) to +39 3...
    elif cleaned.startswith("3") and len(cleaned) == 10:
        cleaned = "+39" + cleaned

    # Add + if only digits
    elif cleaned.isdigit() and not cleaned.startswith("+"):
        if len(cleaned) == 10:  # Italian mobile without prefix (3xx xxx xxxx)
            cleaned = "+39" + cleaned
        elif cleaned.startswith("39") and len(cleaned) >= 11:
            cleaned = "+" + cleaned

    # Ensure + is present
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    return cleaned


def is_italian_mobile(phone: str) -> bool:
    """Check if a phone number is an Italian mobile number."""
    normalized = normalize_italian_phone(phone)
    # Italian mobile numbers start with +39 3xx
    return normalized.startswith("+393") and len(normalized) == 13


def is_italian_landline(phone: str) -> bool:
    """Check if a phone number is an Italian landline number."""
    normalized = normalize_italian_phone(phone)
    # Italian landlines start with +39 0x
    return normalized.startswith("+390") and 10 <= len(normalized) <= 13
