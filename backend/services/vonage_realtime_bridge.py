"""
vonage_realtime_bridge.py — FisioterapiAssist.it
Bridge tra Vonage Voice API e Gemini Live API per chiamate vocali in tempo reale.
Gestisce il flusso audio e l'integrazione con il sistema sanitario italiano (CF logic).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Callable

from backend.api.gemini_native import GeminiNativeClient, CodiceFiscaleExtractor
from backend.api.gemini_prompts import build_system_prompt
from backend.services.appointment_tools import AppointmentManager, ItalianHealthcareValidator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Costanti Vonage
# ---------------------------------------------------------------------------

VONAGE_SAMPLE_RATE = 16000      # Hz (Linear16 PCM)
VONAGE_CHANNELS = 1             # Mono
VONAGE_FRAME_MS = 20            # ms per frame audio
VONAGE_ENCODING = "linear16"    # Formato audio

# Timeout chiamata (secondi)
CALL_TIMEOUT_SECONDS = 600      # 10 minuti

# Numero massimo di errori consecutivi prima dell'escalation
MAX_CONSECUTIVE_ERRORS = 3


# ---------------------------------------------------------------------------
# Modello dati chiamata
# ---------------------------------------------------------------------------

class CallState:
    """Stato di una chiamata Vonage attiva."""

    INIZIATA = "iniziata"
    IN_CORSO = "in_corso"
    RACCOLTA_CF = "raccolta_cf"
    RACCOLTA_DATI = "raccolta_dati"
    CONFERMA = "conferma"
    ESCALATION = "escalation"
    TERMINATA = "terminata"
    ERRORE = "errore"

    def __init__(self, call_uuid: str, from_number: str) -> None:
        self.call_uuid = call_uuid
        self.from_number = from_number
        self.stato = self.INIZIATA
        self.session_id = str(uuid.uuid4())
        self.paziente_cf: str | None = None
        self.paziente_nome: str | None = None
        self.dati_appuntamento: dict[str, Any] = {}
        self.errori_consecutivi = 0
        self.inizio_chiamata = time.time()
        self.ultima_attivita = time.time()
        self.transcript_buffer: list[str] = []

    @property
    def durata_secondi(self) -> float:
        return time.time() - self.inizio_chiamata

    def registra_attivita(self) -> None:
        self.ultima_attivita = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_uuid": self.call_uuid,
            "from_number": self.from_number,
            "stato": self.stato,
            "session_id": self.session_id,
            "paziente_cf": self.paziente_cf,
            "durata_secondi": round(self.durata_secondi, 1),
        }


# ---------------------------------------------------------------------------
# Bridge principale
# ---------------------------------------------------------------------------

class VonageRealtimeBridge:
    """
    Bridge tra Vonage Voice API e Gemini Live API.

    Flusso:
    1. Vonage riceve la chiamata → webhook → avvia websocket audio
    2. Bridge riceve audio PCM → invia a Gemini Live
    3. Gemini trascrive + risponde → Bridge invia audio TTS a Vonage
    4. Durante la conversazione: estrae CF, raccoglie dati, prenota

    Specifico per il mercato italiano:
    - Prompt e risposte in italiano
    - Validazione Codice Fiscale (CF) in real-time
    - Integrazione con AppointmentManager per SSN italiano
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings
        self.validator = ItalianHealthcareValidator()
        self.cf_extractor = CodiceFiscaleExtractor()
        self.appointment_manager = AppointmentManager(settings)

        # Client Gemini
        self.gemini_client = GeminiNativeClient(
            api_key=settings.get("gemini_api_key", ""),
            settings=settings,
        )

        # Chiavi Vonage
        self.vonage_api_key = settings.get("vonage_api_key", "")
        self.vonage_api_secret = settings.get("vonage_api_secret", "")
        self.vonage_application_id = settings.get("vonage_application_id", "")
        self.vonage_number = settings.get("vonage_number", "")

        # Stato chiamate attive
        self._active_calls: dict[str, CallState] = {}

        # Callbacks
        self._on_call_end: Callable[[CallState], None] | None = None

    # ------------------------------------------------------------------
    # Gestione chiamate in entrata
    # ------------------------------------------------------------------

    def handle_inbound_call(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Gestisce il webhook Vonage per chiamata in entrata.
        Restituisce il NCCO (Nexmo Call Control Object) per rispondere.

        Returns:
            NCCO con istruzioni per Vonage: risposta vocale + websocket
        """
        call_uuid = webhook_data.get("uuid", str(uuid.uuid4()))
        from_number = webhook_data.get("from", "sconosciuto")

        logger.info("Chiamata in entrata: %s da %s", call_uuid, from_number)

        # Crea stato chiamata
        call_state = CallState(call_uuid=call_uuid, from_number=from_number)
        self._active_calls[call_uuid] = call_state

        # Crea sessione Gemini
        self.gemini_client.create_session(call_state.session_id)

        # NCCO italiano
        websocket_url = f"{self.settings.get('websocket_base_url', '')}/audio/{call_uuid}"

        ncco = [
            {
                "action": "talk",
                "text": (
                    "Buongiorno, sono Anna, la receptionist virtuale. "
                    "Come posso aiutarla oggi?"
                ),
                "language": "it-IT",
                "style": 0,
                "bargeIn": True,
            },
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "websocket",
                        "uri": websocket_url,
                        "content-type": f"audio/l16;rate={VONAGE_SAMPLE_RATE}",
                        "headers": {
                            "call_uuid": call_uuid,
                            "session_id": call_state.session_id,
                        },
                    }
                ],
                "from": self.vonage_number,
            },
        ]

        return ncco

    def handle_call_status(self, webhook_data: dict[str, Any]) -> None:
        """Gestisce aggiornamenti di stato della chiamata (evento Vonage)."""
        call_uuid = webhook_data.get("uuid", "")
        status = webhook_data.get("status", "")

        call_state = self._active_calls.get(call_uuid)
        if not call_state:
            return

        logger.debug("Stato chiamata %s: %s", call_uuid, status)

        if status in ("completed", "failed", "busy", "rejected", "cancelled"):
            self._terminate_call(call_uuid, status)

    # ------------------------------------------------------------------
    # Elaborazione audio real-time
    # ------------------------------------------------------------------

    async def process_audio_chunk(
        self, call_uuid: str, audio_data: bytes
    ) -> bytes | None:
        """
        Elabora un chunk audio PCM ricevuto da Vonage.

        Args:
            call_uuid: identificatore chiamata
            audio_data: frame audio PCM Linear16

        Returns:
            Audio PCM di risposta da inviare a Vonage, oppure None
        """
        call_state = self._active_calls.get(call_uuid)
        if not call_state:
            logger.warning("Chiamata non trovata: %s", call_uuid)
            return None

        call_state.registra_attivita()

        # Timeout chiamata
        if call_state.durata_secondi > CALL_TIMEOUT_SECONDS:
            logger.info("Timeout chiamata %s", call_uuid)
            self._terminate_call(call_uuid, "timeout")
            return self._generate_farewell_audio()

        return None

    async def process_transcript(
        self, call_uuid: str, transcript: str, is_final: bool = True
    ) -> dict[str, Any]:
        """
        Elabora una trascrizione ricevuta (da Vonage ASR o Gemini Live).

        Priorità di elaborazione:
        1. Se in fase raccolta CF → tenta estrazione CF
        2. Altrimenti → passa a Gemini per intent detection e risposta

        Returns:
            dict con response_text e action
        """
        call_state = self._active_calls.get(call_uuid)
        if not call_state or not is_final:
            return {}

        call_state.registra_attivita()
        call_state.transcript_buffer.append(transcript)

        # Fase raccolta CF
        if call_state.stato == CallState.RACCOLTA_CF:
            return await self._handle_cf_phase(call_state, transcript)

        # Elaborazione Gemini
        result = self.gemini_client.process_transcript(
            session_id=call_state.session_id,
            transcript=transcript,
        )

        # Aggiorna stato chiamata in base all'azione Gemini
        action = result.get("action")
        if action == "richiedi_cf":
            call_state.stato = CallState.RACCOLTA_CF
        elif action == "escalation_operatore":
            call_state.stato = CallState.ESCALATION
        elif action == "cf_acquisito":
            call_state.stato = CallState.RACCOLTA_DATI
            call_state.paziente_cf = result.get("extracted_cf")

        return result

    # ------------------------------------------------------------------
    # Fase raccolta Codice Fiscale (logica specifica IT)
    # ------------------------------------------------------------------

    async def _handle_cf_phase(
        self, call_state: CallState, transcript: str
    ) -> dict[str, Any]:
        """
        Gestione specializzata della fase di raccolta CF in chiamata.

        Incorpora la logica specifica del sistema sanitario italiano:
        - Tentativi multipli con feedback progressivo
        - Suggerimento alfabeto fonetico italiano
        - Escalation dopo MAX_CONSECUTIVE_ERRORS tentativi
        """
        match_result = self.gemini_client.match_patient_by_cf(
            transcript=transcript,
            session_id=call_state.session_id,
        )

        if match_result["found"]:
            cf = match_result["cf"]
            call_state.paziente_cf = cf
            call_state.stato = CallState.RACCOLTA_DATI
            call_state.errori_consecutivi = 0

            logger.info(
                "CF acquisito per chiamata %s: %s***",
                call_state.call_uuid,
                cf[:4],
            )

            return {
                "response_text": (
                    "Grazie, ho registrato il suo Codice Fiscale. "
                    "Ora mi può dire che tipo di trattamento fisioterapico necessita?"
                ),
                "action": "cf_acquisito",
                "extracted_cf": cf,
                "session_state": CallState.RACCOLTA_DATI,
            }

        # CF non trovato
        call_state.errori_consecutivi += 1

        if call_state.errori_consecutivi >= MAX_CONSECUTIVE_ERRORS:
            call_state.stato = CallState.ESCALATION
            logger.warning(
                "Escalation per CF non riconosciuto: chiamata %s",
                call_state.call_uuid,
            )
            return {
                "response_text": (
                    "Mi dispiace, ho difficoltà a riconoscere il Codice Fiscale. "
                    "La passo a un operatore. Rimanga in linea."
                ),
                "action": "escalation_operatore",
                "extracted_cf": None,
                "session_state": CallState.ESCALATION,
            }

        # Suggerimento fonetico progressivo
        tentativo = call_state.errori_consecutivi
        if tentativo == 1:
            hint = (
                "Può sillabare il Codice Fiscale lentamente? "
                "Ad esempio: 'erre, esse, esse, ti...'"
            )
        else:
            hint = (
                "Proviamo ancora. Pronunci ogni lettera separatamente usando "
                "l'alfabeto fonetico: 'acca' per H, 'erre' per R, 'esse' per S... "
                "oppure ogni lettera come 'A di Ancona, B di Bologna'."
            )

        return {
            "response_text": hint,
            "action": "richiedi_cf_retry",
            "extracted_cf": None,
            "session_state": CallState.RACCOLTA_CF,
        }

    # ------------------------------------------------------------------
    # Prenotazione appuntamento via chiamata
    # ------------------------------------------------------------------

    async def book_appointment_from_call(
        self, call_uuid: str, appointment_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Prenota un appuntamento raccogliendo i dati durante la chiamata.

        Il CF deve essere già stato validato nella fase precedente.
        """
        call_state = self._active_calls.get(call_uuid)
        if not call_state or not call_state.paziente_cf:
            return {
                "success": False,
                "response_text": "Non ho i suoi dati completi. Può richiamare?",
            }

        # Aggiunge CF già validato
        appointment_data["codice_fiscale"] = call_state.paziente_cf

        result = self.appointment_manager.book_appointment(appointment_data)

        if result["success"]:
            app = result["appointment"]
            response = (
                f"Perfetto! Ho prenotato {app['prestazione_descrizione']} "
                f"per {app['data']} alle {app['ora_inizio']}. "
                f"Le invieremo una conferma per email. "
                f"Ricordi di portare la tessera sanitaria. "
                f"Ha bisogno di altro?"
            )
            call_state.stato = CallState.CONFERMA
        else:
            errors = "; ".join(result.get("errors", []))
            response = (
                f"Mi dispiace, non è stato possibile completare la prenotazione: {errors}. "
                f"Vuole provare con un altro orario?"
            )

        return {
            "success": result["success"],
            "response_text": response,
            "appointment": result.get("appointment"),
            "errors": result.get("errors", []),
        }

    # ------------------------------------------------------------------
    # Webhook security (HMAC Vonage)
    # ------------------------------------------------------------------

    def verify_vonage_signature(
        self, payload: bytes, signature_header: str
    ) -> bool:
        """
        Verifica la firma HMAC-SHA256 del webhook Vonage.

        Previene richieste non autorizzate (falsificazione webhook).
        """
        if not self.vonage_api_secret:
            logger.warning("Secret Vonage non configurato; skip verifica firma")
            return True

        try:
            expected = hmac.new(
                self.vonage_api_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, signature_header.lower())
        except Exception as exc:
            logger.error("Errore verifica firma Vonage: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _terminate_call(self, call_uuid: str, reason: str) -> None:
        """Termina una chiamata e libera le risorse."""
        call_state = self._active_calls.pop(call_uuid, None)
        if not call_state:
            return

        call_state.stato = CallState.TERMINATA
        logger.info(
            "Chiamata %s terminata: %s (durata: %.0f s)",
            call_uuid,
            reason,
            call_state.durata_secondi,
        )

        # Chiudi sessione Gemini
        self.gemini_client.close_session(call_state.session_id)

        # Callback opzionale
        if self._on_call_end:
            self._on_call_end(call_state)

    def _generate_farewell_audio(self) -> bytes:
        """
        Genera un placeholder audio per il messaggio di addio.
        In produzione, questo chiamerebbe il TTS di Vonage o Google.
        """
        # Placeholder: silenzio PCM
        sample_count = VONAGE_SAMPLE_RATE * 1  # 1 secondo di silenzio
        return bytes(sample_count * 2)  # 16-bit samples = 2 bytes each

    def get_active_calls_count(self) -> int:
        """Restituisce il numero di chiamate attive."""
        return len(self._active_calls)

    def get_call_state(self, call_uuid: str) -> dict[str, Any] | None:
        """Restituisce lo stato di una chiamata attiva."""
        call_state = self._active_calls.get(call_uuid)
        return call_state.to_dict() if call_state else None
