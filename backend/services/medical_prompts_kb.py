"""
MedicoAssist.it — Medical Prompts Knowledge Base
Italian-language prompts and knowledge base for the AI assistant (Anna).
Adapted for Italian physiotherapy / medico specialist context.
"""

# ============================================================
# System Prompt — Anna, Assistente Virtuale
# ============================================================
SYSTEM_PROMPT = """Sei Anna, l'assistente virtuale AI dello studio medico specialistico.
Il tuo ruolo è gestire le chiamate telefoniche e assistere i pazienti in modo professionale e cortese.

COMPETENZE:
- Prenotazione, modifica e annullamento appuntamenti
- Verifica identità tramite Codice Fiscale
- Informazioni su orari, prestazioni, e disponibilità del medico specialista
- Gestione ricette dematerializzate (NRE — Numero Ricetta Elettronica)
- Informazioni su ticket sanitario ed esenzioni

REGOLE:
1. Parla SEMPRE in italiano formale (dare del Lei)
2. Chiedi SEMPRE il Codice Fiscale per identificare il paziente
3. Non fornire MAI diagnosi o consigli medici
4. In caso di emergenza, consiglia di chiamare il 118
5. Se non puoi aiutare, trasferisci al personale
6. Rispetta la privacy dei dati sensibili (GDPR/GARANTE)
7. Sii empatica ma professionale

CONTESTO MEDICO:
- Lo studio offre servizi di medicina specialistica
- I medici specialisti sono i professionisti sanitari dello studio
- Il sistema sanitario è l'SSN (Servizio Sanitario Nazionale)
- Le prestazioni sono convenzionate con il SSN (ticket) o private
"""

# ============================================================
# Response Templates
# ============================================================
RESPONSE_TEMPLATES = {
    "greeting": "Buongiorno, sono Anna, l'assistente virtuale dello studio. Come posso aiutarla?",

    "ask_cf": "Per procedere, avrei bisogno del suo Codice Fiscale. Me lo può comunicare, per cortesia?",

    "cf_confirmed": "Perfetto, ho trovato la sua anagrafica. Come posso aiutarla oggi?",

    "cf_not_found": "Mi dispiace, non ho trovato il suo Codice Fiscale nel nostro sistema. "
                    "Potrebbe essere un nuovo paziente. Vuole che la registri?",

    "cf_invalid": "Il Codice Fiscale che mi ha comunicato non sembra valido. "
                  "Può ripeterlo per favore? Sono 16 caratteri alfanumerici.",

    "appointment_confirmed": "Il suo appuntamento è stato confermato per il {data} alle ore {ora}. "
                             "Riceverà una conferma via email.",

    "appointment_cancelled": "L'appuntamento è stato annullato. Vuole prenotarne uno nuovo?",

    "no_availability": "Mi dispiace, non ci sono disponibilità per la data richiesta. "
                       "Posso proporle delle alternative?",

    "transfer_to_human": "La metto in contatto con il personale dello studio. "
                         "Attenda in linea, per favore.",

    "emergency": "Se si tratta di un'emergenza, la prego di chiamare il 118 immediatamente.",

    "goodbye": "La ringrazio per aver chiamato. Arrivederci e buona giornata!",

    "error": "Mi scusi, si è verificato un problema. Posso provare ad aiutarla in un altro modo?",

    "ticket_info": "Il ticket sanitario per questa prestazione è di €{importo}. "
                   "Se ha un codice di esenzione, può comunicarmelo.",

    "nre_request": "Ha con sé il Numero Ricetta Elettronica (NRE)? Lo troverà sulla ricetta del medico.",

    "slot_available": "Ho trovato delle disponibilità. Il primo slot libero è {data} alle {ora}. "
                      "Le va bene?",
}

# ============================================================
# Italian Prestazioni (Service Types)
# ============================================================
PRESTAZIONI = {
    "FKT_001": "Fisioterapia — Riabilitazione Motoria",
    "FKT_002": "Fisioterapia — Terapia Manuale",
    "FKT_003": "Fisioterapia — Massoterapia",
    "FKT_004": "Fisioterapia — Elettroterapia (TENS)",
    "FKT_005": "Fisioterapia — Ultrasuoni",
    "FKT_006": "Fisioterapia — Laser Terapia",
    "FKT_007": "Fisioterapia — Magnetoterapia",
    "FKT_008": "Fisioterapia — Kinesiterapia",
    "FKT_009": "Fisioterapia — Rieducazione Posturale",
    "FKT_010": "Fisioterapia — Riabilitazione Post-Chirurgica",
    "MED_001": "Visita Specialistica",
    "MED_002": "Visita di Controllo",
    "MED_003": "Consulto Specialistico",
}

# ============================================================
# Esenzioni (Ticket Exemptions)
# ============================================================
ESENZIONI = {
    "E": "Esenzione per reddito",
    "R": "Esenzione per patologia rara",
    "G": "Esenzione per gravidanza",
    "D": "Esenzione per invalidità",
    "I": "Esenzione per età (>65 anni con reddito basso)",
}

TICKET_BASE = 36.15  # EUR — standard SSN ticket


def get_prompt(key: str, **kwargs) -> str:
    """Get a response template with optional formatting."""
    template = RESPONSE_TEMPLATES.get(key, RESPONSE_TEMPLATES["error"])
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
