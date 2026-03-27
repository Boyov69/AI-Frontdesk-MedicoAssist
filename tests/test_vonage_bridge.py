"""
Tests per VonageRealtimeBridge — integrazione Vonage + CF logic italiana.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from backend.services.vonage_realtime_bridge import (
    VonageRealtimeBridge,
    CallState,
    MAX_CONSECUTIVE_ERRORS,
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def settings():
    return {
        "gemini_api_key": "test-gemini-key",
        "vonage_api_key": "test-vonage-key",
        "vonage_api_secret": "test-secret",
        "vonage_application_id": "test-app-id",
        "vonage_number": "+39 02 12345678",
        "websocket_base_url": "wss://test.fisioterapiassist.it",
        "ticket_base_eur": 36.15,
    }


@pytest.fixture
def bridge(settings):
    return VonageRealtimeBridge(settings)


@pytest.fixture
def call_state():
    return CallState(call_uuid="test-uuid-001", from_number="+39 333 1234567")


# ---------------------------------------------------------------------------
# Test CallState
# ---------------------------------------------------------------------------

class TestCallState:

    def test_initial_state(self, call_state):
        assert call_state.stato == CallState.INIZIATA
        assert call_state.paziente_cf is None
        assert call_state.errori_consecutivi == 0

    def test_session_id_generated(self, call_state):
        assert call_state.session_id is not None
        assert len(call_state.session_id) > 0

    def test_durata_secondi_positive(self, call_state):
        assert call_state.durata_secondi >= 0

    def test_registra_attivita_updates_timestamp(self, call_state):
        old_ts = call_state.ultima_attivita
        import time; time.sleep(0.01)
        call_state.registra_attivita()
        assert call_state.ultima_attivita >= old_ts

    def test_to_dict_contains_required_keys(self, call_state):
        d = call_state.to_dict()
        assert "call_uuid" in d
        assert "stato" in d
        assert "from_number" in d
        assert "session_id" in d
        assert "durata_secondi" in d


# ---------------------------------------------------------------------------
# Test VonageRealtimeBridge — Inbound call handling
# ---------------------------------------------------------------------------

class TestHandleInboundCall:

    def test_handle_inbound_creates_call_state(self, bridge):
        webhook_data = {"uuid": "call-001", "from": "+39 333 9876543"}
        bridge.handle_inbound_call(webhook_data)
        state = bridge.get_call_state("call-001")
        assert state is not None
        assert state["from_number"] == "+39 333 9876543"

    def test_handle_inbound_returns_ncco(self, bridge):
        webhook_data = {"uuid": "call-002", "from": "+39 333 1111111"}
        ncco = bridge.handle_inbound_call(webhook_data)
        assert isinstance(ncco, list)
        assert len(ncco) >= 2

    def test_ncco_has_talk_action(self, bridge):
        ncco = bridge.handle_inbound_call({"uuid": "call-003", "from": "+39 333 2222222"})
        actions = [item["action"] for item in ncco]
        assert "talk" in actions

    def test_ncco_talk_in_italian(self, bridge):
        ncco = bridge.handle_inbound_call({"uuid": "call-004", "from": "+39 333 3333333"})
        talk_items = [item for item in ncco if item.get("action") == "talk"]
        assert len(talk_items) > 0
        assert talk_items[0].get("language") == "it-IT"

    def test_ncco_has_connect_action(self, bridge):
        ncco = bridge.handle_inbound_call({"uuid": "call-005", "from": "+39 333 4444444"})
        actions = [item["action"] for item in ncco]
        assert "connect" in actions

    def test_active_calls_count_increases(self, bridge):
        initial = bridge.get_active_calls_count()
        bridge.handle_inbound_call({"uuid": "call-006", "from": "+39 333 5555555"})
        assert bridge.get_active_calls_count() == initial + 1

    def test_handle_inbound_generates_uuid_if_missing(self, bridge):
        webhook_data = {"from": "+39 333 6666666"}  # no uuid
        ncco = bridge.handle_inbound_call(webhook_data)
        assert isinstance(ncco, list)


# ---------------------------------------------------------------------------
# Test VonageRealtimeBridge — Call status handling
# ---------------------------------------------------------------------------

class TestHandleCallStatus:

    def test_completed_call_removed(self, bridge):
        bridge.handle_inbound_call({"uuid": "call-status-001", "from": "+39 333 7777777"})
        bridge.handle_call_status({"uuid": "call-status-001", "status": "completed"})
        assert bridge.get_call_state("call-status-001") is None

    def test_failed_call_removed(self, bridge):
        bridge.handle_inbound_call({"uuid": "call-status-002", "from": "+39 333 8888888"})
        bridge.handle_call_status({"uuid": "call-status-002", "status": "failed"})
        assert bridge.get_call_state("call-status-002") is None

    def test_unknown_uuid_status_no_error(self, bridge):
        # Non deve sollevare eccezioni
        bridge.handle_call_status({"uuid": "nonexistent-uuid", "status": "completed"})


# ---------------------------------------------------------------------------
# Test VonageRealtimeBridge — Transcript processing
# ---------------------------------------------------------------------------

class TestProcessTranscript:

    @pytest.mark.asyncio
    async def test_prenotazione_intent(self, bridge):
        bridge.handle_inbound_call({"uuid": "trans-001", "from": "+39 333 9999999"})
        result = await bridge.process_transcript("trans-001", "Vorrei prenotare un appuntamento")
        assert result.get("action") == "richiedi_cf"

    @pytest.mark.asyncio
    async def test_cf_phase_valid_cf(self, bridge):
        """Test che la fase CF riconosca un CF valido."""
        bridge.handle_inbound_call({"uuid": "trans-002", "from": "+39 333 1234567"})

        # Prima: trigger raccolta CF
        await bridge.process_transcript("trans-002", "Voglio prenotare fisioterapia")

        # Poi: fornisce CF valido
        result = await bridge.process_transcript("trans-002", "RSSMRA85M01H501Q")
        assert result.get("action") == "cf_acquisito"
        state = bridge.get_call_state("trans-002")
        assert state["paziente_cf"] is not None

    @pytest.mark.asyncio
    async def test_cf_phase_escalation_after_max_errors(self, bridge):
        """Dopo MAX_CONSECUTIVE_ERRORS tentativi falliti deve escalare."""
        bridge.handle_inbound_call({"uuid": "trans-003", "from": "+39 333 0000000"})

        # Trigger raccolta CF
        await bridge.process_transcript("trans-003", "Voglio prenotare")

        # Tenta MAX_CONSECUTIVE_ERRORS volte con testo non valido
        for _ in range(MAX_CONSECUTIVE_ERRORS):
            result = await bridge.process_transcript("trans-003", "parole senza cf")

        assert result.get("action") == "escalation_operatore"

    @pytest.mark.asyncio
    async def test_process_nonexistent_call_returns_empty(self, bridge):
        result = await bridge.process_transcript("nonexistent-call", "test")
        assert result == {}


# ---------------------------------------------------------------------------
# Test VonageRealtimeBridge — Webhook signature verification
# ---------------------------------------------------------------------------

class TestWebhookSignature:

    def test_verify_signature_no_secret_returns_true(self, settings):
        settings_no_secret = {**settings, "vonage_api_secret": ""}
        bridge = VonageRealtimeBridge(settings_no_secret)
        result = bridge.verify_vonage_signature(b"payload", "any-sig")
        assert result is True

    def test_verify_signature_correct(self, bridge):
        import hmac
        import hashlib
        payload = b'{"test": "data"}'
        secret = "test-secret"
        expected_sig = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        result = bridge.verify_vonage_signature(payload, expected_sig)
        assert result is True

    def test_verify_signature_wrong_returns_false(self, bridge):
        payload = b'{"test": "data"}'
        result = bridge.verify_vonage_signature(payload, "wrong-signature")
        assert result is False
