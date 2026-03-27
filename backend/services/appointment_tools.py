"""
appointment_tools.py — FisioterapiAssist.it
Gestione appuntamenti e validazione identità paziente per il mercato italiano.
"""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Costanti sistema sanitario italiano
# ---------------------------------------------------------------------------

# Codici mese per il Codice Fiscale
CF_MONTH_CODES: dict[str, int] = {
    "A": 1,  # Gennaio
    "B": 2,  # Febbraio
    "C": 3,  # Marzo
    "D": 4,  # Aprile
    "E": 5,  # Maggio
    "H": 6,  # Giugno
    "L": 7,  # Luglio
    "M": 8,  # Agosto
    "P": 9,  # Settembre
    "R": 10, # Ottobre
    "S": 11, # Novembre
    "T": 12, # Dicembre
}

# Valori per caratteri in posizione dispari (1-based) nel calcolo del check digit
CF_ODD_VALUES: dict[str, int] = {
    "0": 1,  "1": 0,  "2": 5,  "3": 7,  "4": 9,
    "5": 13, "6": 15, "7": 17, "8": 19, "9": 21,
    "A": 1,  "B": 0,  "C": 5,  "D": 7,  "E": 9,
    "F": 13, "G": 15, "H": 17, "I": 19, "J": 21,
    "K": 2,  "L": 4,  "M": 18, "N": 20, "O": 11,
    "P": 3,  "Q": 6,  "R": 8,  "S": 12, "T": 14,
    "U": 16, "V": 10, "W": 22, "X": 25, "Y": 24,
    "Z": 23,
}

# Valori per caratteri in posizione pari (1-based)
CF_EVEN_VALUES: dict[str, int] = {
    **{str(i): i for i in range(10)},
    **{chr(65 + i): i for i in range(26)},
}

# Tipi di prestazione fisioterapica (codici SSN)
PRESTAZIONI_FISIOTERAPICHE: dict[str, str] = {
    "FKT_001": "Fisioterapia motoria individuale",
    "FKT_002": "Rieducazione posturale globale",
    "FKT_003": "Fisioterapia respiratoria",
    "FKT_004": "Linfodrenaggio manuale",
    "FKT_005": "Tecar terapia",
    "FKT_006": "TENS / elettrostimolazione",
    "FKT_007": "Ultrasuoni terapeutici",
    "FKT_008": "Magnetoterapia",
    "FKT_009": "Massoterapia",
    "FKT_010": "Terapia occupazionale",
}

# Ticket sanitario vigente (in euro, aggiornabile via settings)
TICKET_BASE_EUR = 36.15

# Orari di apertura predefiniti (configurabili tramite settings)
DEFAULT_OPENING_HOURS = {
    0: (time(8, 0), time(19, 0)),   # Lunedì
    1: (time(8, 0), time(19, 0)),   # Martedì
    2: (time(8, 0), time(19, 0)),   # Mercoledì
    3: (time(8, 0), time(19, 0)),   # Giovedì
    4: (time(8, 0), time(18, 0)),   # Venerdì
    5: (time(9, 0), time(13, 0)),   # Sabato (mattina)
    # 6 = domenica: chiuso
}

# Durata predefinita appuntamento per tipo prestazione (in minuti)
DEFAULT_DURATIONS: dict[str, int] = {
    "FKT_001": 45,
    "FKT_002": 60,
    "FKT_003": 30,
    "FKT_004": 60,
    "FKT_005": 30,
    "FKT_006": 20,
    "FKT_007": 20,
    "FKT_008": 20,
    "FKT_009": 45,
    "FKT_010": 60,
}


# ---------------------------------------------------------------------------
# Validator Codice Fiscale
# ---------------------------------------------------------------------------

class CodiceFiscaleError(ValueError):
    """Errore specifico per la validazione del Codice Fiscale."""


class ItalianHealthcareValidator:
    """
    Validatore per il sistema sanitario italiano.

    Gestisce:
    - Codice Fiscale (CF): validazione formale + check digit
    - Tessera Sanitaria (TS): verifica formato
    - Numero di esenzione ticket (esenzioni per patologia/reddito)
    - Validazione ricetta dematerializzata (NRE)
    """

    # Pattern regex per il Codice Fiscale (include omocodia)
    CF_PATTERN = re.compile(
        r"^[A-Z]{6}"          # Cognome + Nome (6 lettere)
        r"[0-9LMNPQRSTUV]{2}" # Anno di nascita (o carattere omocodia)
        r"[ABCDEHLMPRST]"     # Mese di nascita
        r"[0-9LMNPQRSTUV]{2}" # Giorno di nascita (o carattere omocodia)
        r"[A-Z][0-9LMNPQRSTUV]{3}" # Codice comune (Belfiore)
        r"[A-Z]$",            # Check digit
        re.IGNORECASE,
    )

    # Tessera Sanitaria: 20 cifre
    TS_PATTERN = re.compile(r"^\d{20}$")

    # Numero Ricetta Elettronica (NRE): 2 lettere + 13 cifre
    NRE_PATTERN = re.compile(r"^[A-Z]{2}\d{13}$", re.IGNORECASE)

    # Codice esenzione ticket: lettera + 2 o 3 cifre (es. E01, R99, E001)
    ESENZIONE_PATTERN = re.compile(r"^[A-Z]\d{2,3}$", re.IGNORECASE)

    # ---------------------------------------------------------------------------

    def validate_codice_fiscale(self, cf: str) -> dict[str, Any]:
        """
        Valida il Codice Fiscale e ne estrae le informazioni demografiche.

        Returns:
            dict con chiavi: valid (bool), cf_normalizzato, sesso, anno_nascita,
                             mese_nascita, giorno_nascita, codice_comune, error (se invalid)
        """
        if not cf or not isinstance(cf, str):
            return {"valid": False, "error": "Codice Fiscale mancante o non valido"}

        cf_upper = cf.strip().upper()

        # Gestione omocodia: sostituisce caratteri numerici codificati con le cifre originali
        cf_normalized = self._resolve_omocodia(cf_upper)

        if not self.CF_PATTERN.match(cf_upper):
            return {
                "valid": False,
                "cf_normalizzato": cf_upper,
                "error": "Formato Codice Fiscale non valido",
            }

        if not self._verify_check_digit(cf_normalized):
            return {
                "valid": False,
                "cf_normalizzato": cf_normalized,
                "error": "Check digit del Codice Fiscale non corretto",
            }

        try:
            info = self._extract_demographic_info(cf_normalized)
        except CodiceFiscaleError as exc:
            return {"valid": False, "cf_normalizzato": cf_normalized, "error": str(exc)}

        return {
            "valid": True,
            "cf_normalizzato": cf_normalized,
            **info,
        }

    def validate_tessera_sanitaria(self, ts: str) -> dict[str, Any]:
        """Valida il numero della Tessera Sanitaria (TS-CNS)."""
        if not ts or not isinstance(ts, str):
            return {"valid": False, "error": "Numero tessera sanitaria mancante"}

        ts_clean = re.sub(r"\s", "", ts.strip())

        if not self.TS_PATTERN.match(ts_clean):
            return {
                "valid": False,
                "tessera": ts_clean,
                "error": "Formato tessera sanitaria non valido (richiesti 20 cifre)",
            }

        return {
            "valid": True,
            "tessera": ts_clean,
            "regione_emittente": ts_clean[0:3],
            "asl_emittente": ts_clean[3:6],
        }

    def validate_nre(self, nre: str) -> dict[str, Any]:
        """Valida il Numero di Ricetta Elettronica dematerializzata."""
        if not nre or not isinstance(nre, str):
            return {"valid": False, "error": "NRE mancante"}

        nre_clean = nre.strip().upper()

        if not self.NRE_PATTERN.match(nre_clean):
            return {
                "valid": False,
                "nre": nre_clean,
                "error": "Formato NRE non valido (es. atteso: RM1234567890123)",
            }

        return {
            "valid": True,
            "nre": nre_clean,
            "regione": nre_clean[:2],
        }

    def validate_esenzione(self, codice: str) -> dict[str, Any]:
        """Valida il codice di esenzione ticket sanitario."""
        if not codice or not isinstance(codice, str):
            return {"valid": False, "error": "Codice esenzione mancante"}

        codice_clean = codice.strip().upper()

        if not self.ESENZIONE_PATTERN.match(codice_clean):
            return {
                "valid": False,
                "codice": codice_clean,
                "error": "Formato codice esenzione non valido (es. atteso: E01, R99)",
            }

        # Classificazione tipo esenzione
        tipo = self._classify_esenzione(codice_clean)

        return {
            "valid": True,
            "codice": codice_clean,
            "tipo": tipo,
        }

    # ---------------------------------------------------------------------------
    # Metodi privati
    # ---------------------------------------------------------------------------

    _OMOCODIA_MAP = {
        "L": "0", "M": "1", "N": "2", "P": "3", "Q": "4",
        "R": "5", "S": "6", "T": "7", "U": "8", "V": "9",
    }

    def _resolve_omocodia(self, cf: str) -> str:
        """Converte eventuali caratteri omocodia nelle cifre corrispondenti."""
        positions = [6, 7, 9, 10, 12, 13, 14]
        chars = list(cf)
        for pos in positions:
            if pos < len(chars) and chars[pos] in self._OMOCODIA_MAP:
                chars[pos] = self._OMOCODIA_MAP[chars[pos]]
        return "".join(chars)

    def _verify_check_digit(self, cf: str) -> bool:
        """Verifica il check digit (ultimo carattere) del Codice Fiscale."""
        if len(cf) != 16:
            return False

        total = 0
        for i, char in enumerate(cf[:15]):
            # Posizioni dispari (1-based) = indici pari (0-based)
            if i % 2 == 0:
                total += CF_ODD_VALUES.get(char, 0)
            else:
                total += CF_EVEN_VALUES.get(char, 0)

        expected = chr(65 + (total % 26))
        return cf[15] == expected

    def _extract_demographic_info(self, cf: str) -> dict[str, Any]:
        """Estrae le informazioni demografiche dal Codice Fiscale normalizzato."""
        year_suffix = int(cf[6:8])
        month_char = cf[8].upper()
        day_raw = int(cf[9:11])
        codice_comune = cf[11:15]

        month = CF_MONTH_CODES.get(month_char)
        if month is None:
            raise CodiceFiscaleError(f"Codice mese non valido: {month_char}")

        # Sesso: le donne hanno giorno di nascita + 40
        if day_raw > 40:
            sesso = "F"
            giorno = day_raw - 40
        else:
            sesso = "M"
            giorno = day_raw

        if not (1 <= giorno <= 31):
            raise CodiceFiscaleError(f"Giorno di nascita non valido: {giorno}")

        # Anno di nascita: anno a 2 cifre → interpreta nel range ragionevole
        current_year = date.today().year
        century = (current_year // 100) * 100
        anno = century + year_suffix
        if anno > current_year:
            anno -= 100

        return {
            "sesso": sesso,
            "anno_nascita": anno,
            "mese_nascita": month,
            "giorno_nascita": giorno,
            "codice_comune": codice_comune,
        }

    def _classify_esenzione(self, codice: str) -> str:
        """Classifica il tipo di esenzione ticket."""
        prefix = codice[0]
        classifications = {
            "E": "Esenzione per patologia cronica/rara",
            "R": "Esenzione per reddito",
            "G": "Esenzione per gravidanza",
            "D": "Esenzione per donatori di sangue/organi",
            "I": "Esenzione per invalidità",
        }
        return classifications.get(prefix, "Altra esenzione")


# ---------------------------------------------------------------------------
# Gestione appuntamenti
# ---------------------------------------------------------------------------

@dataclass
class Appointment:
    """Rappresenta un appuntamento fisioterapico."""

    paziente_cf: str
    paziente_nome: str
    paziente_cognome: str
    paziente_telefono: str
    paziente_email: str
    prestazione_codice: str
    data: date
    ora_inizio: time
    durata_minuti: int
    fisioterapista: str
    nre: str | None = None
    esenzione: str | None = None
    note: str = ""
    confermato: bool = False
    id: str = field(default_factory=lambda: "")

    def __post_init__(self) -> None:
        if not self.id:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            self.id = f"APP-{ts}-{self.paziente_cf[:4].upper()}"

    @property
    def ora_fine(self) -> time:
        """Calcola l'orario di fine appuntamento."""
        dt_inizio = datetime.combine(self.data, self.ora_inizio)
        dt_fine = dt_inizio + timedelta(minutes=self.durata_minuti)
        return dt_fine.time()

    @property
    def prestazione_descrizione(self) -> str:
        return PRESTAZIONI_FISIOTERAPICHE.get(self.prestazione_codice, self.prestazione_codice)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "paziente_cf": self.paziente_cf,
            "paziente_nome": self.paziente_nome,
            "paziente_cognome": self.paziente_cognome,
            "paziente_telefono": self.paziente_telefono,
            "paziente_email": self.paziente_email,
            "prestazione_codice": self.prestazione_codice,
            "prestazione_descrizione": self.prestazione_descrizione,
            "data": self.data.isoformat(),
            "ora_inizio": self.ora_inizio.strftime("%H:%M"),
            "ora_fine": self.ora_fine.strftime("%H:%M"),
            "durata_minuti": self.durata_minuti,
            "fisioterapista": self.fisioterapista,
            "nre": self.nre,
            "esenzione": self.esenzione,
            "note": self.note,
            "confermato": self.confermato,
        }


class AppointmentManager:
    """
    Gestisce la logica di prenotazione degli appuntamenti fisioterapici.

    Integra la validazione ItalianHealthcareValidator per garantire
    la correttezza dei dati del paziente prima di ogni prenotazione.
    """

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.validator = ItalianHealthcareValidator()
        self.settings = settings or {}
        self._appointments: list[Appointment] = []

    # ------------------------------------------------------------------
    # Validazione paziente
    # ------------------------------------------------------------------

    def validate_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Valida i dati del paziente prima della prenotazione.

        Richiede almeno il Codice Fiscale.
        Verifica opzionalmente TS, NRE e codice esenzione se forniti.
        """
        errors: list[str] = []
        warnings: list[str] = []
        validated: dict[str, Any] = {}

        # Codice Fiscale (obbligatorio)
        cf_result = self.validator.validate_codice_fiscale(data.get("codice_fiscale", ""))
        if not cf_result["valid"]:
            errors.append(f"Codice Fiscale: {cf_result['error']}")
        else:
            validated["codice_fiscale"] = cf_result["cf_normalizzato"]
            validated["cf_info"] = cf_result

        # Tessera Sanitaria (opzionale)
        if ts := data.get("tessera_sanitaria"):
            ts_result = self.validator.validate_tessera_sanitaria(ts)
            if not ts_result["valid"]:
                warnings.append(f"Tessera Sanitaria: {ts_result['error']}")
            else:
                validated["tessera_sanitaria"] = ts_result["tessera"]

        # NRE Ricetta (opzionale)
        if nre := data.get("nre"):
            nre_result = self.validator.validate_nre(nre)
            if not nre_result["valid"]:
                errors.append(f"Ricetta NRE: {nre_result['error']}")
            else:
                validated["nre"] = nre_result["nre"]

        # Esenzione ticket (opzionale)
        if esenzione := data.get("esenzione"):
            ese_result = self.validator.validate_esenzione(esenzione)
            if not ese_result["valid"]:
                warnings.append(f"Esenzione: {ese_result['error']}")
            else:
                validated["esenzione"] = ese_result["codice"]
                validated["esenzione_tipo"] = ese_result["tipo"]

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_data": validated,
        }

    # ------------------------------------------------------------------
    # Disponibilità e prenotazione
    # ------------------------------------------------------------------

    def get_available_slots(
        self,
        target_date: date,
        prestazione_codice: str,
        fisioterapista: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Restituisce gli slot disponibili per una data e prestazione specifiche.
        """
        durata = DEFAULT_DURATIONS.get(prestazione_codice, 30)
        weekday = target_date.weekday()

        if weekday not in DEFAULT_OPENING_HOURS:
            return []

        apertura, chiusura = DEFAULT_OPENING_HOURS[weekday]
        slots: list[dict[str, Any]] = []
        current = datetime.combine(target_date, apertura)
        end = datetime.combine(target_date, chiusura)

        while current + timedelta(minutes=durata) <= end:
            slot_time = current.time()
            if not self._is_slot_booked(target_date, slot_time, durata, fisioterapista):
                slots.append({
                    "data": target_date.isoformat(),
                    "ora": slot_time.strftime("%H:%M"),
                    "durata_minuti": durata,
                    "fisioterapista": fisioterapista or "Primo disponibile",
                    "prestazione": PRESTAZIONI_FISIOTERAPICHE.get(prestazione_codice, prestazione_codice),
                })
            current += timedelta(minutes=30)

        return slots

    def book_appointment(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prenota un appuntamento dopo validazione dei dati del paziente.

        Returns:
            dict con chiavi: success (bool), appointment (dict), errors (list)
        """
        # 1. Validazione paziente
        validation = self.validate_patient(data)
        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
                "appointment": None,
            }

        # 2. Parsing data/ora
        try:
            app_date = date.fromisoformat(data["data"])
            app_time = time.fromisoformat(data["ora"])
        except (KeyError, ValueError) as exc:
            return {
                "success": False,
                "errors": [f"Data/ora non valida: {exc}"],
                "appointment": None,
            }

        prestazione = data.get("prestazione_codice", "FKT_001")
        durata = DEFAULT_DURATIONS.get(prestazione, 30)
        fisioterapista = data.get("fisioterapista", "Primo disponibile")

        # 3. Controllo disponibilità
        if self._is_slot_booked(app_date, app_time, durata, fisioterapista):
            return {
                "success": False,
                "errors": ["Lo slot richiesto non è disponibile. Scegliere un altro orario."],
                "appointment": None,
            }

        validated = validation["validated_data"]

        # 4. Creazione appuntamento
        appointment = Appointment(
            paziente_cf=validated["codice_fiscale"],
            paziente_nome=data.get("nome", ""),
            paziente_cognome=data.get("cognome", ""),
            paziente_telefono=data.get("telefono", ""),
            paziente_email=data.get("email", ""),
            prestazione_codice=prestazione,
            data=app_date,
            ora_inizio=app_time,
            durata_minuti=durata,
            fisioterapista=fisioterapista,
            nre=validated.get("nre"),
            esenzione=validated.get("esenzione"),
            note=data.get("note", ""),
            confermato=False,
        )

        self._appointments.append(appointment)
        logger.info("Appuntamento prenotato: %s", appointment.id)

        return {
            "success": True,
            "errors": [],
            "warnings": validation.get("warnings", []),
            "appointment": appointment.to_dict(),
        }

    def cancel_appointment(self, appointment_id: str, cf: str) -> dict[str, Any]:
        """Annulla un appuntamento verificando il Codice Fiscale del paziente."""
        cf_result = self.validator.validate_codice_fiscale(cf)
        if not cf_result["valid"]:
            return {"success": False, "error": "Codice Fiscale non valido"}

        cf_norm = cf_result["cf_normalizzato"]

        for app in self._appointments:
            if app.id == appointment_id and app.paziente_cf == cf_norm:
                self._appointments.remove(app)
                logger.info("Appuntamento annullato: %s", appointment_id)
                return {"success": True, "appointment_id": appointment_id}

        return {
            "success": False,
            "error": "Appuntamento non trovato o Codice Fiscale non corrispondente",
        }

    def get_patient_appointments(self, cf: str) -> dict[str, Any]:
        """Recupera tutti gli appuntamenti di un paziente tramite Codice Fiscale."""
        cf_result = self.validator.validate_codice_fiscale(cf)
        if not cf_result["valid"]:
            return {"valid": False, "error": cf_result["error"], "appointments": []}

        cf_norm = cf_result["cf_normalizzato"]
        patient_apps = [
            app.to_dict()
            for app in self._appointments
            if app.paziente_cf == cf_norm
        ]

        return {
            "valid": True,
            "cf": cf_norm,
            "appointments": patient_apps,
            "totale": len(patient_apps),
        }

    def calculate_ticket(self, prestazione_codice: str, esenzione: str | None = None) -> dict[str, Any]:
        """Calcola il ticket sanitario per una prestazione."""
        if esenzione:
            ese_result = self.validator.validate_esenzione(esenzione)
            if ese_result["valid"]:
                return {
                    "prestazione": PRESTAZIONI_FISIOTERAPICHE.get(prestazione_codice, prestazione_codice),
                    "importo_eur": 0.0,
                    "esenzione": esenzione,
                    "tipo_esenzione": ese_result["tipo"],
                    "esente": True,
                }

        importo = self.settings.get("ticket_base_eur", TICKET_BASE_EUR)
        return {
            "prestazione": PRESTAZIONI_FISIOTERAPICHE.get(prestazione_codice, prestazione_codice),
            "importo_eur": importo,
            "esenzione": None,
            "esente": False,
        }

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _is_slot_booked(
        self,
        target_date: date,
        start_time: time,
        duration_minutes: int,
        fisioterapista: str | None,
    ) -> bool:
        """Verifica se uno slot è già occupato."""
        new_start = datetime.combine(target_date, start_time)
        new_end = new_start + timedelta(minutes=duration_minutes)

        for app in self._appointments:
            if app.data != target_date:
                continue
            if fisioterapista and app.fisioterapista != fisioterapista:
                continue
            existing_start = datetime.combine(app.data, app.ora_inizio)
            existing_end = datetime.combine(app.data, app.ora_fine)
            # Sovrapposizione
            if new_start < existing_end and new_end > existing_start:
                return True

        return False
