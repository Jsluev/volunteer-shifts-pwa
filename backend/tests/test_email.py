from unittest.mock import patch, MagicMock
from app.services.email import send_email


def test_send_email_no_smtp_config():
    with patch("app.services.email.settings") as mock_settings:
        mock_settings.SMTP_HOST = ""
        result = send_email("test@test.com", "Subject", "Body")
        assert result is False


def test_send_email_success():
    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.smtplib.SMTP") as mock_smtp:
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user@test.com"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_PORT = 587

        server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email("recipient@test.com", "Test Subject", "Test Body")
        assert result is True
        server.send_message.assert_called_once()


def test_send_email_connection_error():
    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.smtplib.SMTP") as mock_smtp:
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user@test.com"
        mock_settings.SMTP_PASSWORD = "pass"

        mock_smtp.return_value.__enter__ = MagicMock(side_effect=ConnectionError)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email("recipient@test.com", "Subject", "Body")
        assert result is False
