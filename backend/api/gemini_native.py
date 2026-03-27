"""
gemini_native.py — FisioterapiAssist.it
Integrazione Gemini Live API con matching del Codice Fiscale (CF) italiano.
Gestisce il riconoscimento vocale del CF, la normalizzazione e la verifica.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.services.appointment_tools import ItalianHealthcareValidator
from backend.api.gemini_prompts import build_system_prompt, ANNA_FALLBACK_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Costanti per il riconoscimento vocale del Codice Fiscale
# ---------------------------------------------------------------------------

# Mapping fonetico italiano → carattere (come il paziente può pronunciare il CF)
CF_PHONETIC_MAP: dict[str, str] = {
    # Lettere (alfabeto fonetico italiano e comune)
    "acca": "H", "bi": "B", "ci": "C", "di": "D", "e": "E",
    "effe": "F", "gi": "G", "i": "I", "elle": "L", "emme": "M",
    "enne": "N", "o": "O", "pi": "P", "qu": "Q", "erre": "R",
    "esse": "S", "ti": "T", "u": "U", "vu": "V", "zeta": "Z",
    "a": "A", "k": "K", "j": "J", "w": "W", "x": "X", "y": "Y",
    # Numeri pronunciati come parole
    "zero": "0", "uno": "1", "due": "2", "tre": "3", "quattro": "4",
    "cinque": "5", "sei": "6", "sette": "7", "otto": "8", "nove": "9",
}

# Regex per estrarre sequenze candidate a essere un CF dal testo trascritto
CF_CANDIDATE_PATTERN = re.compile(
    r"[A-Z]{2,6}[0-9]{2}[ABCDEHLMPRST][0-9]{2}[A-Z][0-9]{3}[A-Z]",
    re.IGNORECASE,
)

# Regex per estrarre gli ultimi 4 caratteri del CF (usati per conferma identità)
CF_LAST4_PATTERN = re.compile(r"\b[A-Z0-9]{4}\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Modello dati per le sessioni Gemini Live
# ---------------------------------------------------------------------------

@dataclass
class GeminiSession:
    """Rappresenta una sessione attiva con Gemini Live API."""

    session_id: str
    paziente_cf: str | None = None
    paziente_nome: str | None = None
    stato: str = "attesa"          # attesa | raccolta_dati | conferma | completato
    dati_appuntamento: dict[str, Any] = field(default_factory=dict)
    tentativi_cf: int = 0
    messaggi: list[dict[str, str]] = field(default_factory=list)

    MAX_TENTATIVI_CF = 3

    def aggiungi_messaggio(self, ruolo: str, testo: str) -> None:
        self.messaggi.append({"ruolo": ruolo, "testo": testo})

    def reset_cf_attempts(self) -> None:
        self.tentativi_cf = 0


# ---------------------------------------------------------------------------
# Estrattore Codice Fiscale da testo parlato
# ---------------------------------------------------------------------------

class CodiceFiscaleExtractor:
    """
    Estrae e normalizza il Codice Fiscale da testo trascritto da voce.

    Gestisce:
    - CF dettato carattere per carattere ("A, B, C, D, ...")
    - CF dettato foneticamente ("acca, uno, erre, ...")
    - CF scritto direttamente nel testo
    - Varianti con spazi, trattini, punti
    """

    def __init__(self) -> None:
        self.validator = ItalianHealthcareValidator()

    def extract_from_text(self, text: str) -> dict[str, Any]:
        """
        Tenta di estrarre un Codice Fiscale dal testo trascritto.

        Returns:
            dict con chiavi: found (bool), cf (str|None), confidence (float),
                             validation (dict|None)
        """
        if not text:
            return {"found": False, "cf": None, "confidence": 0.0, "validation": None}

        text_upper = text.strip().upper()

        # 1. Cerca CF esplicito nel testo (sequenza diretta)
        direct_match = self._find_direct_cf(text_upper)
        if direct_match:
            validation = self.validator.validate_codice_fiscale(direct_match)
            return {
                "found": validation["valid"],
                "cf": direct_match if validation["valid"] else None,
                "confidence": 0.95 if validation["valid"] else 0.3,
                "validation": validation,
            }

        # 2. Prova decodifica fonetica
        phonetic_cf = self._decode_phonetic(text_upper)
        if phonetic_cf and len(phonetic_cf) >= 10:
            validation = self.validator.validate_codice_fiscale(phonetic_cf)
            return {
                "found": validation["valid"],
                "cf": phonetic_cf if validation["valid"] else None,
                "confidence": 0.75 if validation["valid"] else 0.2,
                "validation": validation,
            }

        # 3. Prova estrazione con rimozione spazi/separatori
        cleaned = re.sub(r"[\s\-\.\,]", "", text_upper)
        cleaned_match = self._find_direct_cf(cleaned)
        if cleaned_match:
            validation = self.validator.validate_codice_fiscale(cleaned_match)
            return {
                "found": validation["valid"],
                "cf": cleaned_match if validation["valid"] else None,
                "confidence": 0.85 if validation["valid"] else 0.25,
                "validation": validation,
            }

        return {"found": False, "cf": None, "confidence": 0.0, "validation": None}

    def extract_last4(self, text: str) -> str | None:
        """
        Estrae gli ultimi 4 caratteri del CF dal testo.
        Usato per la verifica identità in chiamata.
        """
        text_upper = text.strip().upper()
        candidates = CF_LAST4_PATTERN.findall(text_upper)
        if candidates:
            # Restituisce l'ultimo pattern trovato (più probabile essere il CF)
            return candidates[-1]
        return None

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _find_direct_cf(self, text: str) -> str | None:
        """Cerca una sequenza CF valida nel testo."""
        # Rimuove spazi e cerca
        no_spaces = re.sub(r"\s+", "", text)
        matches = CF_CANDIDATE_PATTERN.findall(no_spaces)
        if matches:
            return matches[0].upper()

        # Cerca CF lungo 16 caratteri con possibili separatori
        potential = re.sub(r"[\s\-]", "", text)
        if len(potential) == 16 and re.match(r"^[A-Z0-9]{16}$", potential):
            return potential

        return None

    def _decode_phonetic(self, text: str) -> str | None:
        """Decodifica un CF pronunciato foneticamente."""
        words = re.split(r"[\s,]+", text.lower())
        result = []

        for word in words:
            word = word.strip(" .,;:")
            if not word:
                continue

            if word in CF_PHONETIC_MAP:
                result.append(CF_PHONETIC_MAP[word])
            elif len(word) == 1 and word.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
                result.append(word.upper())

        cf_candidate = "".join(result)
        return cf_candidate if cf_candidate else None


# ---------------------------------------------------------------------------
# Client Gemini Native
# ---------------------------------------------------------------------------

class GeminiNativeClient:
    """
    Client per Gemini Live API con supporto specifico per il sistema sanitario italiano.

    Gestisce:
    - Sessioni audio real-time
    - Estrazione e validazione del Codice Fiscale dal parlato
    - Integrazione con AppointmentManager per la prenotazione
    - Gestione del flusso conversazionale in italiano
    """

    def __init__(
        self,
        api_key: str,
        settings: dict[str, Any] | None = None,
        on_transcript: Callable[[str, str], None] | None = None,
    ) -> None:
        self.api_key = api_key
        self.settings = settings or {}
        self.on_transcript = on_transcript
        self.cf_extractor = CodiceFiscaleExtractor()
        self.validator = ItalianHealthcareValidator()
        self.system_prompt = build_system_prompt(settings)
        self._sessions: dict[str, GeminiSession] = {}

    # ------------------------------------------------------------------
    # Gestione sessioni
    # ------------------------------------------------------------------

    def create_session(self, session_id: str) -> GeminiSession:
        """Crea una nuova sessione conversazionale."""
        session = GeminiSession(session_id=session_id)
        self._sessions[session_id] = session
        logger.info("Sessione Gemini creata: %s", session_id)
        return session

    def get_session(self, session_id: str) -> GeminiSession | None:
        """Recupera una sessione esistente."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Chiude e rimuove una sessione."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Sessione Gemini chiusa: %s", session_id)

    # ------------------------------------------------------------------
    # Elaborazione trascrizioni
    # ------------------------------------------------------------------

    def process_transcript(
        self, session_id: str, transcript: str
    ) -> dict[str, Any]:
        """
        Elabora una trascrizione vocale nel contesto della sessione.

        Priorità:
        1. Estrazione Codice Fiscale se in fase di raccolta dati
        2. Riconoscimento intent (prenotazione, verifica, annullamento)
        3. Estrazione dati appuntamento
        4. Generazione risposta contestuale

        Returns:
            dict con chiavi: response_text (str), action (str|None),
                             extracted_cf (str|None), session_state (str)
        """
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        session.aggiungi_messaggio("paziente", transcript)

        # Fase di raccolta Codice Fiscale
        if session.stato == "raccolta_cf":
            return self._handle_cf_collection(session, transcript)

        # Rilevamento intent
        intent = self._detect_intent(transcript)

        if intent == "prenotazione":
            session.stato = "raccolta_cf"
            return {
                "response_text": (
                    "Perfetto, la aiuto con la prenotazione. "
                    "Per prima cosa, mi può indicare il suo Codice Fiscale? "
                    "Lo può sillabare lentamente."
                ),
                "action": "richiedi_cf",
                "extracted_cf": None,
                "session_state": session.stato,
            }

        if intent == "verifica":
            session.stato = "verifica_identita"
            return {
                "response_text": (
                    "Certo, verifico il suo appuntamento. "
                    "Può indicarmi il cognome e gli ultimi 4 caratteri del suo Codice Fiscale?"
                ),
                "action": "richiedi_identita",
                "extracted_cf": None,
                "session_state": session.stato,
            }

        if intent == "annullamento":
            session.stato = "verifica_identita"
            return {
                "response_text": (
                    "Capito, procedo con la disdetta. "
                    "Può indicarmi il cognome e gli ultimi 4 caratteri del suo Codice Fiscale?"
                ),
                "action": "richiedi_identita",
                "extracted_cf": None,
                "session_state": session.stato,
            }

        # Risposta generica
        return {
            "response_text": ANNA_FALLBACK_PROMPT,
            "action": None,
            "extracted_cf": None,
            "session_state": session.stato,
        }

    def match_patient_by_cf(
        self, transcript: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Estrae e valida il Codice Fiscale da un testo trascritto.
        Metodo principale per l'identificazione del paziente.

        Returns:
            dict con chiavi: found (bool), cf (str|None), cf_info (dict|None),
                             message (str)
        """
        result = self.cf_extractor.extract_from_text(transcript)

        if not result["found"]:
            return {
                "found": False,
                "cf": None,
                "cf_info": None,
                "message": (
                    "Non sono riuscita a identificare il Codice Fiscale. "
                    "Può ripeterlo lentamente, un carattere alla volta?"
                ),
            }

        cf = result["cf"]
        validation = result["validation"]

        if session_id:
            session = self.get_session(session_id)
            if session:
                session.paziente_cf = cf

        return {
            "found": True,
            "cf": cf,
            "cf_info": validation,
            "confidence": result["confidence"],
            "message": (
                f"Ho registrato il Codice Fiscale. "
                f"Posso procedere con la prenotazione?"
            ),
        }

    def verify_identity_last4(
        self, transcript: str, expected_cf: str
    ) -> dict[str, Any]:
        """
        Verifica l'identità del paziente tramite gli ultimi 4 caratteri del CF.
        Usato per conferma identità senza esporre il CF completo.
        """
        last4 = self.cf_extractor.extract_last4(transcript)

        if not last4:
            return {
                "verified": False,
                "message": "Non ho capito i caratteri. Può ripetere gli ultimi 4 caratteri del suo Codice Fiscale?",
            }

        expected_last4 = expected_cf.strip().upper()[-4:]
        if last4.upper() == expected_last4:
            return {
                "verified": True,
                "message": "Identità verificata con successo.",
            }

        return {
            "verified": False,
            "message": "I caratteri non corrispondono. Vuole riprovare o preferisce recarsi di persona allo studio?",
        }

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _handle_cf_collection(
        self, session: GeminiSession, transcript: str
    ) -> dict[str, Any]:
        """Gestisce la fase di raccolta del Codice Fiscale."""
        session.tentativi_cf += 1

        result = self.cf_extractor.extract_from_text(transcript)

        if result["found"]:
            session.paziente_cf = result["cf"]
            session.stato = "raccolta_dati"
            session.reset_cf_attempts()
            return {
                "response_text": (
                    "Grazie! Ho acquisito il suo Codice Fiscale. "
                    "Quale tipo di prestazione fisioterapica ha bisogno?"
                ),
                "action": "cf_acquisito",
                "extracted_cf": result["cf"],
                "session_state": session.stato,
            }

        if session.tentativi_cf >= GeminiSession.MAX_TENTATIVI_CF:
            session.stato = "escalation"
            return {
                "response_text": (
                    "Mi dispiace, ho difficoltà a riconoscere il Codice Fiscale. "
                    "La metto in contatto con un operatore. Un momento per favore."
                ),
                "action": "escalation_operatore",
                "extracted_cf": None,
                "session_state": session.stato,
            }

        tentativo_mancante = GeminiSession.MAX_TENTATIVI_CF - session.tentativi_cf
        return {
            "response_text": (
                f"Non sono riuscita a registrare il Codice Fiscale. "
                f"Può ripeterlo carattere per carattere? "
                f"(Tentativo {session.tentativi_cf}/{GeminiSession.MAX_TENTATIVI_CF})"
            ),
            "action": "richiedi_cf_retry",
            "extracted_cf": None,
            "session_state": session.stato,
        }

    def _detect_intent(self, text: str) -> str:
        """Rileva l'intento del paziente dal testo trascritto."""
        text_lower = text.lower()

        prenotazione_keywords = [
            "prenotare", "prenotazione", "appuntamento", "vorrei", "devo",
            "ho bisogno", "fissare", "schedulare", "visita",
        ]
        verifica_keywords = [
            "verificare", "controllare", "quando", "che ora", "orario",
            "prossimo appuntamento", "ho un appuntamento",
        ]
        annullamento_keywords = [
            "disdire", "annullare", "cancellare", "non posso venire",
            "non verrò", "rimandare", "posticipare",
        ]

        if any(kw in text_lower for kw in annullamento_keywords):
            return "annullamento"
        if any(kw in text_lower for kw in verifica_keywords):
            return "verifica"
        if any(kw in text_lower for kw in prenotazione_keywords):
            return "prenotazione"

        return "generico"
