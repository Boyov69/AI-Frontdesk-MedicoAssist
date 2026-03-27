"""
Tests per ItalianEmailService — template email italiani.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from backend.services.email_service import (
    ItalianEmailService,
    _format_date_it,
    GIORNI_IT,
    MESI_IT,
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def settings():
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "test@example.com",
        "smtp_password": "test-password",
        "from_email": "noreply@fisioterapiassist.it",
        "from_name": "FisioterapiAssist",
        "telefono_studio": "+39 06 12345678",
        "studio_nome": "Studio FisioterapiAssist Test",
    }


@pytest.fixture
def email_service(settings):
    return ItalianEmailService(settings)


@pytest.fixture
def sample_appointment():
    return {
        "id": "APP-20260512-RSSM",
        "paziente_cf": "RSSMRA85M01H501Q",
        "paziente_nome": "Mario",
        "paziente_cognome": "Rossi",
        "paziente_telefono": "+39 333 1234567",
        "paziente_email": "mario.rossi@example.it",
        "prestazione_codice": "FKT_001",
        "prestazione_descrizione": "Fisioterapia motoria individuale",
        "data": "2026-05-12",
        "ora_inizio": "09:00",
        "ora_fine": "09:45",
        "durata_minuti": 45,
        "fisioterapista": "Dr. Bianchi",
        "nre": "RM1234567890123",
        "esenzione": None,
        "note": "",
        "confermato": True,
    }


# ---------------------------------------------------------------------------
# Test formato data italiano
# ---------------------------------------------------------------------------

class TestFormatDateIt:

    def test_lunedi(self):
        result = _format_date_it(date(2026, 5, 11))  # Lunedì
        assert "lunedì" in result
        assert "11" in result
        assert "maggio" in result
        assert "2026" in result

    def test_domenica(self):
        result = _format_date_it(date(2026, 5, 10))  # Domenica
        assert "domenica" in result

    def test_gennaio(self):
        result = _format_date_it(date(2026, 1, 1))
        assert "gennaio" in result

    def test_dicembre(self):
        result = _format_date_it(date(2026, 12, 25))
        assert "dicembre" in result
        assert "25" in result

    def test_all_months_present(self):
        """Verifica che tutti i mesi siano nel MESI_IT."""
        assert len(MESI_IT) == 13  # indice 0 vuoto + 12 mesi
        assert MESI_IT[1] == "gennaio"
        assert MESI_IT[12] == "dicembre"

    def test_all_days_present(self):
        """Verifica che tutti i giorni siano nel GIORNI_IT."""
        assert len(GIORNI_IT) == 7
        assert GIORNI_IT[0] == "lunedì"
        assert GIORNI_IT[6] == "domenica"


# ---------------------------------------------------------------------------
# Test ItalianEmailService — Conferma prenotazione
# ---------------------------------------------------------------------------

class TestConfermaPrenotazione:

    def test_send_conferma_without_smtp_returns_false(self, settings, sample_appointment):
        """Senza credenziali SMTP, l'invio deve fallire gracefully."""
        settings_no_smtp = {**settings, "smtp_user": "", "smtp_password": ""}
        service = ItalianEmailService(settings_no_smtp)
        result = service.send_conferma_prenotazione(sample_appointment)
        assert result is False

    def test_send_conferma_no_email_returns_false(self, email_service, sample_appointment):
        """Senza email paziente, non deve inviare."""
        app = {**sample_appointment, "paziente_email": ""}
        result = email_service.send_conferma_prenotazione(app)
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_conferma_success(self, mock_smtp, email_service, sample_appointment):
        """Con SMTP mockato, deve inviare con successo."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_conferma_prenotazione(sample_appointment)
        assert result is True
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_conferma_sent_to_correct_recipient(self, mock_smtp, email_service, sample_appointment):
        """L'email di conferma deve essere inviata all'indirizzo del paziente."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_conferma_prenotazione(sample_appointment)

        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args[0]
        # call_args: (from, to, content)
        assert call_args[1] == "mario.rossi@example.it"

    @patch("smtplib.SMTP")
    def test_conferma_includes_nre(self, mock_smtp, email_service, sample_appointment):
        """Con NRE, l'HTML generato deve includerlo."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Capture the HTML before MIME encoding by checking the HTML generation
        html_contents = []
        original_send = email_service._send_email

        def capture_html(to, subject, html_content):
            html_contents.append(html_content)
            return original_send(to, subject, html_content)

        email_service._send_email = capture_html
        email_service.send_conferma_prenotazione(sample_appointment)

        assert len(html_contents) > 0
        assert "RM1234567890123" in html_contents[0]

    @patch("smtplib.SMTP")
    def test_conferma_without_nre(self, mock_smtp, email_service, sample_appointment):
        """Senza NRE, l'HTML generato non deve includere il campo NRE."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        html_contents = []
        original_send = email_service._send_email

        def capture_html(to, subject, html_content):
            html_contents.append(html_content)
            return original_send(to, subject, html_content)

        email_service._send_email = capture_html

        app = {**sample_appointment, "nre": None}
        email_service.send_conferma_prenotazione(app)
        assert "RM1234567890123" not in html_contents[0]


# ---------------------------------------------------------------------------
# Test ItalianEmailService — Promemoria
# ---------------------------------------------------------------------------

class TestPromemoria:

    def test_send_promemoria_no_email_returns_false(self, email_service, sample_appointment):
        app = {**sample_appointment, "paziente_email": ""}
        result = email_service.send_promemoria(app)
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_promemoria_success(self, mock_smtp, email_service, sample_appointment):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_promemoria(sample_appointment)
        assert result is True


# ---------------------------------------------------------------------------
# Test ItalianEmailService — Disdetta
# ---------------------------------------------------------------------------

class TestDisdetta:

    def test_send_disdetta_no_email_returns_false(self, email_service, sample_appointment):
        app = {**sample_appointment, "paziente_email": ""}
        result = email_service.send_disdetta(app)
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_disdetta_success(self, mock_smtp, email_service, sample_appointment):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_disdetta(sample_appointment)
        assert result is True

    @patch("smtplib.SMTP")
    def test_disdetta_sends_to_correct_recipient(self, mock_smtp, email_service, sample_appointment):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_disdetta(sample_appointment)

        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args[0]
        assert call_args[1] == "mario.rossi@example.it"


# ---------------------------------------------------------------------------
# Test ItalianEmailService — Modifica
# ---------------------------------------------------------------------------

class TestModifica:

    def test_send_modifica_no_email_returns_false(self, email_service, sample_appointment):
        app = {**sample_appointment, "paziente_email": ""}
        result = email_service.send_modifica_appuntamento(app)
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_modifica_success(self, mock_smtp, email_service, sample_appointment):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_modifica_appuntamento(sample_appointment)
        assert result is True
