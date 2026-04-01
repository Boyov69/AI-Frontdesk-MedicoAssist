"""
MedicoAssist.it — Voice Service
Manages active voice calls, tracks call state, and integrates with Vonage + Gemini.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VoiceService:
    """Voice call management service."""

    def __init__(self):
        self.active_calls: Dict[str, Dict[str, Any]] = {}

    def register_call(
        self,
        call_uuid: str,
        caller_number: str,
        practice_id: str = "",
        direction: str = "inbound",
    ) -> Dict[str, Any]:
        """Register a new active call."""
        call_state = {
            "uuid": call_uuid,
            "caller": caller_number,
            "practice_id": practice_id,
            "direction": direction,
            "status": "ringing",
            "start_time": datetime.utcnow().isoformat(),
            "ai_handled": True,
            "transferred": False,
            "intent_detected": None,
            "paziente_id": None,
        }
        self.active_calls[call_uuid] = call_state
        logger.info(f"[VOICE] 📞 Chiamata registrata: {call_uuid} da {caller_number}")
        return call_state

    def update_call_status(self, call_uuid: str, status: str, **kwargs):
        """Update call status."""
        if call_uuid in self.active_calls:
            self.active_calls[call_uuid]["status"] = status
            self.active_calls[call_uuid].update(kwargs)

    def mark_transferred(self, call_uuid: str, transfer_to: str):
        """Mark a call as transferred to human."""
        if call_uuid in self.active_calls:
            self.active_calls[call_uuid]["transferred"] = True
            self.active_calls[call_uuid]["ai_handled"] = False
            self.active_calls[call_uuid]["transfer_to"] = transfer_to
            logger.info(f"[VOICE] 🔄 Chiamata {call_uuid} trasferita a {transfer_to}")

    def end_call(self, call_uuid: str) -> Optional[Dict[str, Any]]:
        """End a call and return its state."""
        call_state = self.active_calls.pop(call_uuid, None)
        if call_state:
            call_state["end_time"] = datetime.utcnow().isoformat()
            call_state["status"] = "completed"

            # Calculate duration
            start = datetime.fromisoformat(call_state["start_time"])
            duration = (datetime.utcnow() - start).total_seconds()
            call_state["duration_seconds"] = round(duration)

            logger.info(f"[VOICE] ✅ Chiamata {call_uuid} terminata ({duration:.0f}s)")

            # Log to Supabase
            self._log_to_supabase(call_state)

        return call_state

    def _log_to_supabase(self, call_state: Dict[str, Any]):
        """Log completed call to Supabase."""
        try:
            from services.supabase_service import supabase_service
            supabase_service.log_voice_call({
                "call_uuid": call_state.get("uuid"),
                "caller_number": call_state.get("caller"),
                "practice_id": call_state.get("practice_id"),
                "direction": call_state.get("direction"),
                "ai_handled": call_state.get("ai_handled"),
                "transferred": call_state.get("transferred"),
                "call_duration": call_state.get("duration_seconds", 0),
                "intent": call_state.get("intent_detected"),
            })
        except Exception as e:
            logger.error(f"[VOICE] Errore log Supabase: {e}")

    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get all active calls."""
        return list(self.active_calls.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get voice service statistics."""
        return {
            "active_calls": len(self.active_calls),
            "service_status": "attivo",
        }


# Global singleton
voice_service = VoiceService()
