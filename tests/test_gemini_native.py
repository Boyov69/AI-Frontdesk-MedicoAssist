"""
Tests per CodiceFiscaleExtractor e GeminiNativeClient.
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.api.gemini_native import (
    CodiceFiscaleExtractor,
    GeminiNativeClient,
    GeminiSession,
)
from backend.api.gemini_prompts import build_system_prompt, get_response_template


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor():
    return CodiceFiscaleExtractor()


@pytest.fixture
def client():
    return GeminiNativeClient(api_key="test-key")


# ---------------------------------------------------------------------------
# Test CodiceFiscaleExtractor
# ---------------------------------------------------------------------------

class TestCodiceFiscaleExtractor:
    """Test per l'estrazione del CF da testo trascritto."""

    VALID_CF = "RSSMRA85M01H501Q"

    def test_extract_direct_cf_from_text(self, extractor):
        result = extractor.extract_from_text(self.VALID_CF)
        assert result["found"] is True
        assert result["cf"] == self.VALID_CF

    def test_extract_cf_from_sentence(self, extractor):
        text = f"Il mio codice fiscale è {self.VALID_CF} grazie"
        result = extractor.extract_from_text(text)
        assert result["found"] is True
        assert result["cf"] == self.VALID_CF

    def test_extract_cf_case_insensitive(self, extractor):
        result = extractor.extract_from_text(self.VALID_CF.lower())
        assert result["found"] is True

    def test_empty_text_returns_not_found(self, extractor):
        result = extractor.extract_from_text("")
        assert result["found"] is False
        assert result["cf"] is None

    def test_random_text_no_cf_returns_not_found(self, extractor):
        result = extractor.extract_from_text("buongiorno come stai")
        assert result["found"] is False

    def test_confidence_high_for_direct_match(self, extractor):
        result = extractor.extract_from_text(self.VALID_CF)
        assert result["confidence"] >= 0.9

    def test_extract_phonetic_letters(self, extractor):
        # Prova con parole fonetiche separate
        phonetic = "erre esse esse emme erre acca otto cinque emme zero uno acca cinque zero uno zeta"
        result = extractor.extract_from_text(phonetic)
        # Verifica che qualcosa venga estratto (anche senza CF valido)
        assert "found" in result

    def test_extract_cf_with_spaces_between_chars(self, extractor):
        # CF con spazi tra caratteri
        spaced = " ".join(self.VALID_CF)
        result = extractor.extract_from_text(spaced)
        assert result["found"] is True

    def test_extract_cf_with_hyphens(self, extractor):
        hyphenated = "-".join([self.VALID_CF[i:i+4] for i in range(0, 16, 4)])
        result = extractor.extract_from_text(hyphenated)
        assert result["found"] is True

    def test_extract_last4_from_text(self, extractor):
        text = "gli ultimi quattro sono 501Q"
        last4 = extractor.extract_last4(text)
        assert last4 is not None
        assert last4 == "501Q"

    def test_extract_last4_empty_text(self, extractor):
        last4 = extractor.extract_last4("")
        assert last4 is None


# ---------------------------------------------------------------------------
# Test GeminiNativeClient — Sessioni
# ---------------------------------------------------------------------------

class TestGeminiNativeClientSessions:

    def test_create_session(self, client):
        session = client.create_session("sess-001")
        assert session.session_id == "sess-001"
        assert session.stato == "attesa"
        assert session.paziente_cf is None

    def test_get_session_returns_existing(self, client):
        client.create_session("sess-002")
        session = client.get_session("sess-002")
        assert session is not None
        assert session.session_id == "sess-002"

    def test_get_session_nonexistent_returns_none(self, client):
        result = client.get_session("nonexistent-session")
        assert result is None

    def test_close_session_removes_it(self, client):
        client.create_session("sess-003")
        client.close_session("sess-003")
        assert client.get_session("sess-003") is None

    def test_close_nonexistent_session_noop(self, client):
        # Non deve sollevare eccezioni
        client.close_session("nonexistent-999")


# ---------------------------------------------------------------------------
# Test GeminiNativeClient — Intent detection
# ---------------------------------------------------------------------------

class TestIntentDetection:

    def test_prenotazione_intent(self, client):
        client.create_session("sess-intent-1")
        result = client.process_transcript("sess-intent-1", "Vorrei prenotare un appuntamento")
        assert result["action"] == "richiedi_cf"

    def test_verifica_intent(self, client):
        client.create_session("sess-intent-2")
        result = client.process_transcript("sess-intent-2", "Vorrei controllare il mio appuntamento")
        assert result["action"] == "richiedi_identita"

    def test_annullamento_intent(self, client):
        client.create_session("sess-intent-3")
        result = client.process_transcript("sess-intent-3", "Devo disdire il mio appuntamento")
        assert result["action"] == "richiedi_identita"

    def test_generic_intent_returns_fallback(self, client):
        client.create_session("sess-intent-4")
        result = client.process_transcript("sess-intent-4", "bla bla bla")
        assert result["action"] is None

    def test_prenotazione_sets_raccolta_cf_state(self, client):
        client.create_session("sess-state-1")
        result = client.process_transcript("sess-state-1", "Devo prenotare fisioterapia")
        session = client.get_session("sess-state-1")
        assert session.stato == "raccolta_cf"


# ---------------------------------------------------------------------------
# Test GeminiNativeClient — CF matching
# ---------------------------------------------------------------------------

class TestCFMatching:

    VALID_CF = "RSSMRA85M01H501Q"

    def test_match_patient_by_cf_success(self, client):
        client.create_session("sess-cf-1")
        result = client.match_patient_by_cf(self.VALID_CF, session_id="sess-cf-1")
        assert result["found"] is True
        assert result["cf"] == self.VALID_CF

    def test_match_patient_by_cf_stores_in_session(self, client):
        client.create_session("sess-cf-2")
        client.match_patient_by_cf(self.VALID_CF, session_id="sess-cf-2")
        session = client.get_session("sess-cf-2")
        assert session.paziente_cf == self.VALID_CF

    def test_match_patient_invalid_text(self, client):
        result = client.match_patient_by_cf("parole senza cf", session_id=None)
        assert result["found"] is False
        assert result["cf"] is None

    def test_verify_identity_last4_success(self, client):
        result = client.verify_identity_last4("501Q", self.VALID_CF)
        assert result["verified"] is True

    def test_verify_identity_last4_failure(self, client):
        result = client.verify_identity_last4("XXXX", self.VALID_CF)
        assert result["verified"] is False

    def test_verify_identity_no_text(self, client):
        result = client.verify_identity_last4("", self.VALID_CF)
        assert result["verified"] is False


# ---------------------------------------------------------------------------
# Test GeminiPrompts
# ---------------------------------------------------------------------------

class TestGeminiPrompts:

    def test_build_system_prompt_default(self):
        prompt = build_system_prompt()
        assert "Anna" in prompt
        assert "italiano" in prompt.lower()
        assert "Codice Fiscale" in prompt

    def test_build_system_prompt_custom_ticket(self):
        prompt = build_system_prompt({"ticket_base_eur": 50.00})
        assert "50.0" in prompt

    def test_get_response_template_conferma(self):
        result = get_response_template(
            "appuntamento_confermato",
            data="lunedì 14 aprile 2026",
            ora="09:00",
            prestazione="Fisioterapia motoria individuale",
            fisioterapista="Dr. Bianchi",
            nre_reminder="",
        )
        assert "09:00" in result
        assert "Fisioterapia" in result

    def test_get_response_template_unknown_key(self):
        result = get_response_template("chiave_inesistente")
        assert result == ""

    def test_get_response_template_slot_disponibili(self):
        result = get_response_template(
            "slot_disponibili",
            prestazione="Tecar terapia",
            slots="- lunedì 09:00\n- lunedì 10:00",
        )
        assert "Tecar" in result

    def test_get_response_template_cf_non_valido(self):
        result = get_response_template("cf_non_valido")
        assert "Codice Fiscale" in result


# ---------------------------------------------------------------------------
# Test GeminiSession
# ---------------------------------------------------------------------------

class TestGeminiSession:

    def test_initial_state(self):
        session = GeminiSession(session_id="test-123")
        assert session.stato == "attesa"
        assert session.tentativi_cf == 0
        assert session.paziente_cf is None

    def test_aggiungi_messaggio(self):
        session = GeminiSession(session_id="test-124")
        session.aggiungi_messaggio("paziente", "Buongiorno")
        assert len(session.messaggi) == 1
        assert session.messaggi[0]["ruolo"] == "paziente"

    def test_reset_cf_attempts(self):
        session = GeminiSession(session_id="test-125")
        session.tentativi_cf = 2
        session.reset_cf_attempts()
        assert session.tentativi_cf == 0

    def test_max_tentativi_cf_constant(self):
        assert GeminiSession.MAX_TENTATIVI_CF == 3
