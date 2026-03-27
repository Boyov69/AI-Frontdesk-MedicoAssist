"""
email_service.py — FisioterapiAssist.it
Template email in italiano per conferme, promemoria e disdette appuntamenti.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import date, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template HTML email (italiano)
# ---------------------------------------------------------------------------

_HTML_BASE = """\
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titolo}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: #ffffff;
                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #0066cc; color: #ffffff; padding: 24px 32px; }}
    .header h1 {{ margin: 0; font-size: 22px; }}
    .header p {{ margin: 4px 0 0; font-size: 14px; opacity: 0.85; }}
    .body {{ padding: 32px; color: #333333; line-height: 1.6; }}
    .info-box {{ background: #f0f7ff; border-left: 4px solid #0066cc;
                 padding: 16px 20px; border-radius: 4px; margin: 20px 0; }}
    .info-box p {{ margin: 6px 0; font-size: 15px; }}
    .label {{ font-weight: bold; color: #0066cc; }}
    .warning {{ background: #fff8e1; border-left: 4px solid #ffc107;
                padding: 12px 16px; border-radius: 4px; margin-top: 20px; font-size: 14px; }}
    .footer {{ background: #f9f9f9; padding: 20px 32px; text-align: center;
               font-size: 12px; color: #888888; border-top: 1px solid #eeeeee; }}
    .footer a {{ color: #0066cc; text-decoration: none; }}
    .btn {{ display: inline-block; margin-top: 20px; padding: 12px 28px;
            background: #0066cc; color: #ffffff; border-radius: 6px;
            text-decoration: none; font-weight: bold; font-size: 15px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🏥 FisioterapiAssist</h1>
      <p>Sistema di gestione appuntamenti fisioterapici</p>
    </div>
    <div class="body">
      {contenuto}
    </div>
    <div class="footer">
      <p>© 2026 FisioterapiAssist.it — Tutti i diritti riservati</p>
      <p>
        Questo messaggio è stato inviato automaticamente. Non rispondere a questa email.<br>
        Per assistenza: <a href="mailto:info@fisioterapiassist.it">info@fisioterapiassist.it</a>
      </p>
      <p style="font-size:11px; color:#aaaaaa;">
        I suoi dati personali sono trattati in conformità al Regolamento UE 2016/679 (GDPR)
        e al D.Lgs. 196/2003 come modificato dal D.Lgs. 101/2018.
      </p>
    </div>
  </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Contenuto email — Conferma prenotazione
# ---------------------------------------------------------------------------

_CONFERMA_CONTENUTO = """\
<p>Gentile <strong>{nome} {cognome}</strong>,</p>
<p>La sua prenotazione è stata confermata con successo. Di seguito i dettagli:</p>

<div class="info-box">
  <p><span class="label">📅 Data:</span> {data_formattata}</p>
  <p><span class="label">🕐 Ora:</span> {ora}</p>
  <p><span class="label">⏱ Durata:</span> {durata_minuti} minuti</p>
  <p><span class="label">🩺 Prestazione:</span> {prestazione}</p>
  <p><span class="label">👨‍⚕️ Fisioterapista:</span> {fisioterapista}</p>
  {riga_nre}
  {riga_esenzione}
</div>

<p><strong>Cosa portare all'appuntamento:</strong></p>
<ul>
  <li>Tessera Sanitaria (TS-CNS)</li>
  <li>Documento d'identità valido</li>
  {item_ricetta}
  {item_esenzione}
  <li>Abbigliamento comodo per la terapia</li>
</ul>

<div class="warning">
  ⚠️ <strong>Politica di disdetta:</strong> In caso di impossibilità a presenziare,
  la preghiamo di avvisarci almeno <strong>24 ore prima</strong> telefonando allo
  {telefono_studio} oppure rispondendo a questo messaggio.
  Disdette tardive ripetute possono comportare la perdita della precedenza.
</div>

<p>La aspettiamo!</p>
"""

# ---------------------------------------------------------------------------
# Contenuto email — Promemoria (giorno prima)
# ---------------------------------------------------------------------------

_PROMEMORIA_CONTENUTO = """\
<p>Gentile <strong>{nome} {cognome}</strong>,</p>
<p>Le ricordiamo che <strong>domani</strong> ha un appuntamento presso il nostro studio:</p>

<div class="info-box">
  <p><span class="label">📅 Data:</span> {data_formattata}</p>
  <p><span class="label">🕐 Ora:</span> {ora}</p>
  <p><span class="label">🩺 Prestazione:</span> {prestazione}</p>
  <p><span class="label">👨‍⚕️ Fisioterapista:</span> {fisioterapista}</p>
</div>

<p>Non dimentichi di portare la <strong>Tessera Sanitaria</strong>
{promemoria_ricetta} e di arrivare qualche minuto prima dell'orario previsto.</p>

<p>Se non può presentarsi, la preghiamo di disdire entro questa sera telefonando allo
{telefono_studio}.</p>

<p>A domani!</p>
"""

# ---------------------------------------------------------------------------
# Contenuto email — Disdetta confermata
# ---------------------------------------------------------------------------

_DISDETTA_CONTENUTO = """\
<p>Gentile <strong>{nome} {cognome}</strong>,</p>
<p>La sua disdetta è stata registrata. L'appuntamento seguente è stato annullato:</p>

<div class="info-box">
  <p><span class="label">📅 Data:</span> {data_formattata}</p>
  <p><span class="label">🕐 Ora:</span> {ora}</p>
  <p><span class="label">🩺 Prestazione:</span> {prestazione}</p>
</div>

<p>Se desidera riprogrammare l'appuntamento, può contattarci telefonicamente al
<strong>{telefono_studio}</strong> oppure tramite il nostro sito web.</p>

<p>Grazie per averci avvisato tempestivamente.</p>
"""

# ---------------------------------------------------------------------------
# Contenuto email — Modifica appuntamento
# ---------------------------------------------------------------------------

_MODIFICA_CONTENUTO = """\
<p>Gentile <strong>{nome} {cognome}</strong>,</p>
<p>Il suo appuntamento è stato <strong>modificato</strong>. Ecco i nuovi dettagli:</p>

<div class="info-box">
  <p><span class="label">📅 Nuova data:</span> {data_formattata}</p>
  <p><span class="label">🕐 Nuovo orario:</span> {ora}</p>
  <p><span class="label">🩺 Prestazione:</span> {prestazione}</p>
  <p><span class="label">👨‍⚕️ Fisioterapista:</span> {fisioterapista}</p>
</div>

<p>Se questa modifica non fosse corretta, la preghiamo di contattarci
al più presto al numero <strong>{telefono_studio}</strong>.</p>
"""

# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

GIORNI_IT = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI_IT = [
    "", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


def _format_date_it(d: date) -> str:
    """Formatta una data in italiano: 'lunedì 14 aprile 2026'."""
    giorno_settimana = GIORNI_IT[d.weekday()]
    mese = MESI_IT[d.month]
    return f"{giorno_settimana} {d.day} {mese} {d.year}"


class ItalianEmailService:
    """
    Servizio email per FisioterapiAssist.it

    Invia email di conferma, promemoria e disdetta in italiano.
    Conforme al GDPR e al Codice Privacy italiano (D.Lgs. 196/2003).
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        self.smtp_host = settings.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = settings.get("smtp_port", 587)
        self.smtp_user = settings.get("smtp_user", "")
        self.smtp_password = settings.get("smtp_password", "")
        self.from_email = settings.get("from_email", "noreply@fisioterapiassist.it")
        self.from_name = settings.get("from_name", "FisioterapiAssist")
        self.telefono_studio = settings.get("telefono_studio", "")
        self.studio_nome = settings.get("studio_nome", "Studio FisioterapiAssist")

    # ------------------------------------------------------------------
    # Metodi pubblici
    # ------------------------------------------------------------------

    def send_conferma_prenotazione(self, appointment: dict[str, Any]) -> bool:
        """Invia email di conferma prenotazione al paziente."""
        destinatario = appointment.get("paziente_email", "")
        if not destinatario:
            logger.warning("Email conferma non inviata: email paziente mancante")
            return False

        nome = appointment.get("paziente_nome", "")
        cognome = appointment.get("paziente_cognome", "")
        data_appuntamento = date.fromisoformat(appointment["data"])

        nre = appointment.get("nre")
        esenzione = appointment.get("esenzione")

        riga_nre = (
            f'<p><span class="label">📄 Ricetta (NRE):</span> {nre}</p>'
            if nre else ""
        )
        riga_esenzione = (
            f'<p><span class="label">🔖 Esenzione:</span> {esenzione}</p>'
            if esenzione else ""
        )
        item_ricetta = "<li>Ricetta medica dematerializzata (NRE)</li>" if nre else ""
        item_esenzione = "<li>Codice di esenzione ticket sanitario</li>" if esenzione else ""

        contenuto = _CONFERMA_CONTENUTO.format(
            nome=nome,
            cognome=cognome,
            data_formattata=_format_date_it(data_appuntamento),
            ora=appointment.get("ora_inizio", ""),
            durata_minuti=appointment.get("durata_minuti", ""),
            prestazione=appointment.get("prestazione_descrizione", appointment.get("prestazione_codice", "")),
            fisioterapista=appointment.get("fisioterapista", ""),
            riga_nre=riga_nre,
            riga_esenzione=riga_esenzione,
            item_ricetta=item_ricetta,
            item_esenzione=item_esenzione,
            telefono_studio=self.telefono_studio,
        )

        oggetto = f"Conferma appuntamento — {_format_date_it(data_appuntamento)} ore {appointment.get('ora_inizio', '')}"
        return self._send_email(
            to=destinatario,
            subject=oggetto,
            html_content=_HTML_BASE.format(titolo="Conferma Appuntamento", contenuto=contenuto),
        )

    def send_promemoria(self, appointment: dict[str, Any]) -> bool:
        """Invia email di promemoria (giorno prima dell'appuntamento)."""
        destinatario = appointment.get("paziente_email", "")
        if not destinatario:
            return False

        nome = appointment.get("paziente_nome", "")
        cognome = appointment.get("paziente_cognome", "")
        data_appuntamento = date.fromisoformat(appointment["data"])

        nre = appointment.get("nre")
        promemoria_ricetta = "e la ricetta del medico (NRE)" if nre else ""

        contenuto = _PROMEMORIA_CONTENUTO.format(
            nome=nome,
            cognome=cognome,
            data_formattata=_format_date_it(data_appuntamento),
            ora=appointment.get("ora_inizio", ""),
            prestazione=appointment.get("prestazione_descrizione", appointment.get("prestazione_codice", "")),
            fisioterapista=appointment.get("fisioterapista", ""),
            promemoria_ricetta=promemoria_ricetta,
            telefono_studio=self.telefono_studio,
        )

        oggetto = f"Promemoria appuntamento domani — ore {appointment.get('ora_inizio', '')}"
        return self._send_email(
            to=destinatario,
            subject=oggetto,
            html_content=_HTML_BASE.format(titolo="Promemoria Appuntamento", contenuto=contenuto),
        )

    def send_disdetta(self, appointment: dict[str, Any]) -> bool:
        """Invia email di conferma disdetta al paziente."""
        destinatario = appointment.get("paziente_email", "")
        if not destinatario:
            return False

        nome = appointment.get("paziente_nome", "")
        cognome = appointment.get("paziente_cognome", "")
        data_appuntamento = date.fromisoformat(appointment["data"])

        contenuto = _DISDETTA_CONTENUTO.format(
            nome=nome,
            cognome=cognome,
            data_formattata=_format_date_it(data_appuntamento),
            ora=appointment.get("ora_inizio", ""),
            prestazione=appointment.get("prestazione_descrizione", appointment.get("prestazione_codice", "")),
            telefono_studio=self.telefono_studio,
        )

        oggetto = f"Disdetta appuntamento — {_format_date_it(data_appuntamento)}"
        return self._send_email(
            to=destinatario,
            subject=oggetto,
            html_content=_HTML_BASE.format(titolo="Disdetta Confermata", contenuto=contenuto),
        )

    def send_modifica_appuntamento(self, appointment: dict[str, Any]) -> bool:
        """Invia email di conferma modifica appuntamento al paziente."""
        destinatario = appointment.get("paziente_email", "")
        if not destinatario:
            return False

        nome = appointment.get("paziente_nome", "")
        cognome = appointment.get("paziente_cognome", "")
        data_appuntamento = date.fromisoformat(appointment["data"])

        contenuto = _MODIFICA_CONTENUTO.format(
            nome=nome,
            cognome=cognome,
            data_formattata=_format_date_it(data_appuntamento),
            ora=appointment.get("ora_inizio", ""),
            prestazione=appointment.get("prestazione_descrizione", appointment.get("prestazione_codice", "")),
            fisioterapista=appointment.get("fisioterapista", ""),
            telefono_studio=self.telefono_studio,
        )

        oggetto = f"Modifica appuntamento — {_format_date_it(data_appuntamento)} ore {appointment.get('ora_inizio', '')}"
        return self._send_email(
            to=destinatario,
            subject=oggetto,
            html_content=_HTML_BASE.format(titolo="Appuntamento Modificato", contenuto=contenuto),
        )

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _send_email(self, to: str, subject: str, html_content: str) -> bool:
        """Invia l'email tramite SMTP."""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Credenziali SMTP non configurate; email non inviata a %s", to)
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to

            # Versione testo plain (accessibilità)
            plain_text = self._html_to_plain(html_content)
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to, msg.as_string())

            logger.info("Email inviata a %s: %s", to, subject)
            return True

        except smtplib.SMTPException as exc:
            logger.error("Errore SMTP nell'invio a %s: %s", to, exc)
            return False
        except OSError as exc:
            logger.error("Errore di rete nell'invio email a %s: %s", to, exc)
            return False

    @staticmethod
    def _html_to_plain(html: str) -> str:
        """Converte HTML in testo plain semplificato."""
        import re as _re
        # Rimuove tag HTML
        text = _re.sub(r"<[^>]+>", " ", html)
        # Normalizza spazi
        text = _re.sub(r"\s+", " ", text).strip()
        return text
