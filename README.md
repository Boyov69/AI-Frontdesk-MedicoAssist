# AI-Frontdesk-MedicoAssist

**FisioterapiAssist.it** — AI-powered virtual receptionist for Italian physiotherapy practices.

This repository is the Italian market adaptation of the AI-Frontdesk platform, specifically designed for the Italian national health system (SSN — Servizio Sanitario Nazionale).

---

## 🇮🇹 Italian Healthcare Features

| Feature | Belgian (KinesistAssist) | Italian (FisioterapiAssist) |
|---------|--------------------------|------------------------------|
| Patient ID | RRN (Rijksregisternummer) | **Codice Fiscale (CF)** |
| Health insurance | RIZIV | **SSN / ASL** |
| Prescription | Paper/DMFA | **Ricetta Dematerializzata (NRE)** |
| Ticket exemption | RIZIV codes | **Codici Esenzione (E/R/G/D/I)** |
| Language | Nederlands (NL) | **Italiano (IT)** |
| AI agent name | Anna | **Anna** |
| Privacy law | GDPR + BE | **GDPR + GARANTE (D.Lgs. 196/2003)** |

---

## 🏗️ Architecture

```
AI-Frontdesk-MedicoAssist/
├── backend/
│   ├── services/
│   │   ├── appointment_tools.py      ← ItalianHealthcareValidator + AppointmentManager
│   │   ├── vonage_realtime_bridge.py ← IT prompt + Codice Fiscale (CF) logic
│   │   └── email_service.py          ← Italian email templates
│   └── api/
│       ├── gemini_prompts.py         ← Italian Anna system prompt (Gemini Live)
│       └── gemini_native.py          ← CF extraction from voice transcripts
├── tests/
│   ├── test_appointment_tools.py     ← CF validation, booking, ticket tests
│   ├── test_email_service.py         ← Italian email template tests
│   ├── test_gemini_native.py         ← CF extractor + Gemini session tests
│   └── test_vonage_bridge.py         ← Vonage NCCO + CF phone flow tests
├── medicoassist_settings.json        ← Italian configuration (SSN, ASL, ticket)
└── requirements.txt
```

---

## 🔑 Key Components

### `ItalianHealthcareValidator`
Validates Italian healthcare identifiers:
- **Codice Fiscale (CF)**: 16-character tax code with check digit verification, omocodia support, and demographic extraction
- **Tessera Sanitaria (TS-CNS)**: 20-digit national health card
- **NRE** (Numero Ricetta Elettronica): dematerialized prescription number
- **Codici Esenzione**: ticket exemption codes (E=patologia, R=reddito, G=gravidanza, etc.)

### `AppointmentManager`
Booking logic with Italian SSN integration:
- Validates CF before every booking
- Supports 10 physiotherapy service types (`FKT_001` – `FKT_010`)
- Calculates ticket sanitario (€36.15 base, €0.00 if exempt)
- Availability checking per weekday schedule

### `GeminiNativeClient` + `CodiceFiscaleExtractor`
Gemini Live API integration with Italian voice recognition:
- Extracts Codice Fiscale from spoken text (direct + phonetic + space-separated)
- Italian intent detection (prenotazione / verifica / annullamento)
- Session management with max CF retry logic

### `VonageRealtimeBridge`
Real-time phone call bridge:
- Vonage NCCO generation with Italian TTS (`it-IT`)
- HMAC-SHA256 webhook signature verification
- Progressive CF collection with Italian phonetic hints
- Escalation to human operator after 3 failed CF attempts

### `ItalianEmailService`
HTML email templates in Italian:
- Conferma prenotazione (with NRE + esenzione details)
- Promemoria (24h before appointment)
- Disdetta confermata
- Modifica appuntamento
- GDPR/GARANTE footer on every email

---

## ⚙️ Configuration

Copy and fill in `medicoassist_settings.json`:

```json
{
  "studio": { "nome": "...", "asl_convenzione": "..." },
  "sanitario": { "ticket_base_eur": 36.15, "ssn_convenzionato": true },
  "ai": { "gemini_api_key": "...", "gemini_model": "gemini-2.0-flash-live-001" },
  "vonage": { "api_key": "...", "api_secret": "..." },
  "email": { "smtp_host": "...", "smtp_user": "...", "smtp_password": "..." },
  "supabase": { "url": "...", "anon_key": "..." }
}
```

---

## 🧪 Testing

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

All 129 tests should pass.

---

## 🔒 Privacy & GDPR

- Patient data (CF, TS) is never logged in full — only first 4 characters in logs
- CF not read back aloud in full during calls (only last 4 chars for identity verification)
- Supabase schema isolated from Belgian data (separate project)
- Email footer includes GARANTE/GDPR notice on every message
- Configurable data retention (default: appointments 10 years, calls 30 days)

---

## 🚀 Why a Separate Repo (not a branch)?

Per the architectural strategy:
- **GARANTE Privacy**: Italian patient data must not be commingled with Belgian data
- **Supabase isolation**: separate project per country (already the standard)
- **Independent deployments**: Italian downtime/bugs don't affect Belgian service
- **Future Italian partners**: cleaner codebase for IT resellers/integrators
