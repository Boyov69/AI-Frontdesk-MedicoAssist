"""
MedicoAssist.it — Vonage Voice Service
Handles Vonage Voice API initialization, phone number management,
and call control for Italian phone numbers (+39).
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class VonageService:
    """Vonage Voice API service for MedicoAssist.it"""

    def __init__(self):
        self.api_key = os.getenv("VONAGE_API_KEY")
        self.api_secret = os.getenv("VONAGE_API_SECRET")
        self.application_id = os.getenv("VONAGE_APPLICATION_ID")
        self.private_key_path = os.getenv("VONAGE_PRIVATE_KEY_PATH")
        self.webhook_base_url = os.getenv("VONAGE_WEBHOOK_BASE_URL", "")
        self.client = None
        self._initialized = False

    def initialize(self):
        """Initialize the Vonage client."""
        if self._initialized:
            return True

        if not self.api_key or not self.api_secret:
            logger.warning("[VONAGE] API key/secret non configurati — servizio disabilitato")
            return False

        try:
            import vonage
            self.client = vonage.Client(
                key=self.api_key,
                secret=self.api_secret,
                application_id=self.application_id,
            )
            self._initialized = True
            logger.info("[VONAGE] ✅ Client inizializzato")
            return True
        except ImportError:
            logger.warning("[VONAGE] ⚠️ Modulo vonage non installato")
            return False
        except Exception as e:
            logger.error(f"[VONAGE] ❌ Errore inizializzazione: {e}")
            return False

    # ================================================================
    # NCCO (Nexmo Call Control Objects) — Italian
    # ================================================================

    def build_greeting_ncco(self, practice_name: str = "MedicoAssist") -> List[Dict[str, Any]]:
        """Build Italian greeting NCCO for inbound calls."""
        return [
            {
                "action": "talk",
                "text": f"Buongiorno, benvenuto allo studio {practice_name}. "
                        f"Sono Anna, l'assistente virtuale. Come posso aiutarla?",
                "language": "it-IT",
                "style": 0,
                "bargeIn": True,
            },
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "websocket",
                        "uri": f"{self.webhook_base_url}/api/vonage/ws",
                        "content-type": "audio/l16;rate=16000",
                    }
                ],
            },
        ]

    def build_transfer_ncco(self, phone_number: str) -> List[Dict[str, Any]]:
        """Build NCCO to transfer to a human operator."""
        return [
            {
                "action": "talk",
                "text": "La metto in contatto con un operatore. Attenda in linea, per favore.",
                "language": "it-IT",
                "style": 0,
            },
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "phone",
                        "number": phone_number,
                    }
                ],
                "from": os.getenv("VONAGE_FROM_NUMBER", ""),
                "timeout": 30,
            },
        ]

    def build_goodbye_ncco(self) -> List[Dict[str, Any]]:
        """Build goodbye NCCO."""
        return [
            {
                "action": "talk",
                "text": "La ringrazio per aver chiamato. Arrivederci e buona giornata!",
                "language": "it-IT",
                "style": 0,
            },
        ]

    # ================================================================
    # Call Control
    # ================================================================

    def create_outbound_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        ncco: Optional[List[Dict]] = None,
    ) -> Optional[str]:
        """Create an outbound call. Returns call UUID."""
        if not self._initialized:
            logger.error("[VONAGE] Servizio non inizializzato")
            return None

        from_num = from_number or os.getenv("VONAGE_FROM_NUMBER", "")
        if not from_num:
            logger.error("[VONAGE] Numero mittente non configurato")
            return None

        try:
            response = self.client.voice.create_call({
                "to": [{"type": "phone", "number": to_number}],
                "from": {"type": "phone", "number": from_num},
                "ncco": ncco or self.build_greeting_ncco(),
            })
            call_uuid = response.get("uuid")
            logger.info(f"[VONAGE] Chiamata avviata: {call_uuid} → {to_number}")
            return call_uuid
        except Exception as e:
            logger.error(f"[VONAGE] Errore creazione chiamata: {e}")
            return None

    def hangup_call(self, call_uuid: str) -> bool:
        """Hang up an active call."""
        if not self._initialized:
            return False

        try:
            self.client.voice.update_call(call_uuid, action="hangup")
            logger.info(f"[VONAGE] Chiamata terminata: {call_uuid}")
            return True
        except Exception as e:
            logger.error(f"[VONAGE] Errore chiusura chiamata: {e}")
            return False

    def transfer_call(self, call_uuid: str, transfer_number: str) -> bool:
        """Transfer a call to another number."""
        if not self._initialized:
            return False

        try:
            ncco = self.build_transfer_ncco(transfer_number)
            self.client.voice.update_call(
                call_uuid,
                action="transfer",
                destination={"type": "ncco", "ncco": ncco},
            )
            logger.info(f"[VONAGE] Chiamata trasferita: {call_uuid} → {transfer_number}")
            return True
        except Exception as e:
            logger.error(f"[VONAGE] Errore trasferimento: {e}")
            return False

    # ================================================================
    # Status
    # ================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "initialized": self._initialized,
            "api_key_configured": bool(self.api_key),
            "application_id": self.application_id or "non configurato",
            "webhook_url": self.webhook_base_url or "non configurato",
        }


# Global singleton
vonage_service = VonageService()
