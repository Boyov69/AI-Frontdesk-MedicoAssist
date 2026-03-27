"""
Tests per ItalianHealthcareValidator e AppointmentManager.
Copre: validazione CF, TS, NRE, esenzioni, prenotazione appuntamenti.
"""

import pytest
from datetime import date, time

from backend.services.appointment_tools import (
    ItalianHealthcareValidator,
    AppointmentManager,
    PRESTAZIONI_FISIOTERAPICHE,
    TICKET_BASE_EUR,
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return ItalianHealthcareValidator()


@pytest.fixture
def manager():
    return AppointmentManager()


# ---------------------------------------------------------------------------
# Test ItalianHealthcareValidator — Codice Fiscale
# ---------------------------------------------------------------------------

class TestCodiceFiscaleValidation:
    """Verifica la validazione del Codice Fiscale."""

    # CF reale di test (formato standard, check digit corretto)
    VALID_CF = "RSSMRA85M01H501Q"  # Test CF standard (Romano Mario)
    VALID_CF_FEMALE = "VRDLRA95R41H501H"  # Femmina (giorno > 40)

    def test_valid_cf_returns_true(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True

    def test_valid_cf_normalizes_uppercase(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF.lower())
        assert result["valid"] is True
        assert result["cf_normalizzato"] == self.VALID_CF

    def test_valid_cf_extracts_sesso_maschio(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True
        assert result["sesso"] == "M"

    def test_valid_cf_extracts_sesso_femmina(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF_FEMALE)
        assert result["valid"] is True
        assert result["sesso"] == "F"

    def test_valid_cf_extracts_birth_year(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True
        assert result["anno_nascita"] == 1985

    def test_valid_cf_extracts_birth_month(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True
        assert result["mese_nascita"] == 8  # M = agosto

    def test_valid_cf_extracts_birth_day(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True
        assert result["giorno_nascita"] == 1

    def test_valid_cf_extracts_codice_comune(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF)
        assert result["valid"] is True
        assert result["codice_comune"] == "H501"  # Roma

    def test_empty_cf_returns_false(self, validator):
        result = validator.validate_codice_fiscale("")
        assert result["valid"] is False
        assert "error" in result

    def test_none_cf_returns_false(self, validator):
        result = validator.validate_codice_fiscale(None)
        assert result["valid"] is False

    def test_short_cf_returns_false(self, validator):
        result = validator.validate_codice_fiscale("RSSMRA85M01")
        assert result["valid"] is False

    def test_wrong_check_digit_returns_false(self, validator):
        # Modifica l'ultimo carattere
        wrong_cf = self.VALID_CF[:-1] + "X"
        result = validator.validate_codice_fiscale(wrong_cf)
        assert result["valid"] is False
        assert "check digit" in result["error"].lower()

    def test_invalid_format_returns_false(self, validator):
        result = validator.validate_codice_fiscale("1234567890123456")
        assert result["valid"] is False

    def test_cf_with_spaces_strips_whitespace(self, validator):
        result = validator.validate_codice_fiscale(f"  {self.VALID_CF}  ")
        assert result["valid"] is True

    def test_female_cf_birth_day_normalized(self, validator):
        result = validator.validate_codice_fiscale(self.VALID_CF_FEMALE)
        assert result["valid"] is True
        # Giorno deve essere ≤ 31 (sottratto 40)
        assert 1 <= result["giorno_nascita"] <= 31


# ---------------------------------------------------------------------------
# Test ItalianHealthcareValidator — Tessera Sanitaria
# ---------------------------------------------------------------------------

class TestTesseraSanitaria:

    def test_valid_ts_20_digits(self, validator):
        result = validator.validate_tessera_sanitaria("12345678901234567890")
        assert result["valid"] is True
        assert result["tessera"] == "12345678901234567890"

    def test_ts_strips_spaces(self, validator):
        result = validator.validate_tessera_sanitaria("  12345678901234567890  ")
        assert result["valid"] is True

    def test_ts_too_short_returns_false(self, validator):
        result = validator.validate_tessera_sanitaria("1234567890")
        assert result["valid"] is False

    def test_ts_with_letters_returns_false(self, validator):
        result = validator.validate_tessera_sanitaria("1234567890123456789A")
        assert result["valid"] is False

    def test_empty_ts_returns_false(self, validator):
        result = validator.validate_tessera_sanitaria("")
        assert result["valid"] is False

    def test_valid_ts_extracts_asl(self, validator):
        result = validator.validate_tessera_sanitaria("12345678901234567890")
        assert result["valid"] is True
        assert "asl_emittente" in result
        assert "regione_emittente" in result


# ---------------------------------------------------------------------------
# Test ItalianHealthcareValidator — NRE
# ---------------------------------------------------------------------------

class TestNRE:

    def test_valid_nre(self, validator):
        result = validator.validate_nre("RM1234567890123")
        assert result["valid"] is True
        assert result["nre"] == "RM1234567890123"
        assert result["regione"] == "RM"

    def test_nre_normalizes_to_uppercase(self, validator):
        result = validator.validate_nre("rm1234567890123")
        assert result["valid"] is True

    def test_invalid_nre_too_short(self, validator):
        result = validator.validate_nre("RM12345")
        assert result["valid"] is False

    def test_invalid_nre_starts_with_digits(self, validator):
        result = validator.validate_nre("121234567890123")
        assert result["valid"] is False

    def test_empty_nre_returns_false(self, validator):
        result = validator.validate_nre("")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Test ItalianHealthcareValidator — Esenzione Ticket
# ---------------------------------------------------------------------------

class TestEsenzione:

    def test_valid_esenzione_patologia(self, validator):
        result = validator.validate_esenzione("E01")
        assert result["valid"] is True
        assert "patologia" in result["tipo"].lower()

    def test_valid_esenzione_reddito(self, validator):
        result = validator.validate_esenzione("R99")
        assert result["valid"] is True
        assert "reddito" in result["tipo"].lower()

    def test_valid_esenzione_gravidanza(self, validator):
        result = validator.validate_esenzione("G01")
        assert result["valid"] is True
        assert "gravidanza" in result["tipo"].lower()

    def test_invalid_esenzione_format(self, validator):
        result = validator.validate_esenzione("INVALID")
        assert result["valid"] is False

    def test_esenzione_normalizes_uppercase(self, validator):
        result = validator.validate_esenzione("e01")
        assert result["valid"] is True
        assert result["codice"] == "E01"

    def test_empty_esenzione_returns_false(self, validator):
        result = validator.validate_esenzione("")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Test AppointmentManager
# ---------------------------------------------------------------------------

class TestAppointmentManager:

    VALID_PATIENT = {
        "codice_fiscale": "RSSMRA85M01H501Q",
        "nome": "Mario",
        "cognome": "Rossi",
        "telefono": "+39 06 12345678",
        "email": "mario.rossi@example.it",
        "prestazione_codice": "FKT_001",
        "data": "2026-05-12",
        "ora": "09:00",
        "fisioterapista": "Dr. Bianchi",
    }

    def test_validate_patient_valid_cf(self, manager):
        result = manager.validate_patient({"codice_fiscale": "RSSMRA85M01H501Q"})
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_patient_invalid_cf(self, manager):
        result = manager.validate_patient({"codice_fiscale": "INVALID"})
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_patient_with_valid_nre(self, manager):
        result = manager.validate_patient({
            "codice_fiscale": "RSSMRA85M01H501Q",
            "nre": "RM1234567890123",
        })
        assert result["valid"] is True
        assert "nre" in result["validated_data"]

    def test_validate_patient_invalid_nre_raises_error(self, manager):
        result = manager.validate_patient({
            "codice_fiscale": "RSSMRA85M01H501Q",
            "nre": "INVALID_NRE",
        })
        assert result["valid"] is False

    def test_validate_patient_with_esenzione(self, manager):
        result = manager.validate_patient({
            "codice_fiscale": "RSSMRA85M01H501Q",
            "esenzione": "E01",
        })
        assert result["valid"] is True
        assert "esenzione" in result["validated_data"]

    def test_book_appointment_success(self, manager):
        result = manager.book_appointment(self.VALID_PATIENT.copy())
        assert result["success"] is True
        assert result["appointment"] is not None
        assert result["appointment"]["paziente_cf"] == "RSSMRA85M01H501Q"

    def test_book_appointment_invalid_cf_fails(self, manager):
        data = self.VALID_PATIENT.copy()
        data["codice_fiscale"] = "INVALID"
        result = manager.book_appointment(data)
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_book_appointment_duplicate_slot_fails(self, manager):
        """Due prenotazioni nello stesso slot devono fallire."""
        data = self.VALID_PATIENT.copy()
        result1 = manager.book_appointment(data)
        assert result1["success"] is True

        # Secondo paziente stesso slot (CF diverso)
        data2 = self.VALID_PATIENT.copy()
        data2["codice_fiscale"] = "VRDLRA95R41H501H"
        data2["nome"] = "Laura"
        data2["cognome"] = "Verdi"
        result2 = manager.book_appointment(data2)
        assert result2["success"] is False

    def test_get_patient_appointments(self, manager):
        manager.book_appointment(self.VALID_PATIENT.copy())
        result = manager.get_patient_appointments("RSSMRA85M01H501Q")
        assert result["valid"] is True
        assert result["totale"] >= 1

    def test_cancel_appointment_valid(self, manager):
        booked = manager.book_appointment(self.VALID_PATIENT.copy())
        assert booked["success"] is True

        app_id = booked["appointment"]["id"]
        cancel_result = manager.cancel_appointment(app_id, "RSSMRA85M01H501Q")
        assert cancel_result["success"] is True

    def test_cancel_appointment_wrong_cf_fails(self, manager):
        booked = manager.book_appointment(self.VALID_PATIENT.copy())
        app_id = booked["appointment"]["id"]

        cancel_result = manager.cancel_appointment(app_id, "VRDLRA95R41H501H")
        assert cancel_result["success"] is False

    def test_get_available_slots_returns_list(self, manager):
        slots = manager.get_available_slots(
            target_date=date(2026, 5, 12),  # Lunedì
            prestazione_codice="FKT_001",
        )
        assert isinstance(slots, list)
        assert len(slots) > 0

    def test_get_available_slots_sunday_returns_empty(self, manager):
        # Domenica = chiuso
        slots = manager.get_available_slots(
            target_date=date(2026, 5, 10),  # Domenica
            prestazione_codice="FKT_001",
        )
        assert slots == []

    def test_calculate_ticket_standard(self, manager):
        result = manager.calculate_ticket("FKT_001")
        assert result["importo_eur"] == TICKET_BASE_EUR
        assert result["esente"] is False

    def test_calculate_ticket_with_esenzione(self, manager):
        result = manager.calculate_ticket("FKT_001", esenzione="E01")
        assert result["importo_eur"] == 0.0
        assert result["esente"] is True

    def test_appointment_has_correct_duration(self, manager):
        result = manager.book_appointment(self.VALID_PATIENT.copy())
        assert result["success"] is True
        assert result["appointment"]["durata_minuti"] == 45  # FKT_001

    def test_appointment_ora_fine_calculated(self, manager):
        result = manager.book_appointment(self.VALID_PATIENT.copy())
        assert result["success"] is True
        assert result["appointment"]["ora_fine"] == "09:45"  # 09:00 + 45 min


# ---------------------------------------------------------------------------
# Test Prestazioni fisioterapiche
# ---------------------------------------------------------------------------

class TestPrestazioni:

    def test_all_prestazioni_have_names(self):
        assert len(PRESTAZIONI_FISIOTERAPICHE) == 10
        for code, name in PRESTAZIONI_FISIOTERAPICHE.items():
            assert code.startswith("FKT_")
            assert len(name) > 0

    def test_prestazione_codes_sequential(self):
        codes = list(PRESTAZIONI_FISIOTERAPICHE.keys())
        assert "FKT_001" in codes
        assert "FKT_010" in codes
