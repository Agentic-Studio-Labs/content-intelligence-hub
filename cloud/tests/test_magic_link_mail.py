from unittest.mock import MagicMock


import shared.config as app_settings
from shared.magic_link_mail import magic_link_sign_in_url, send_magic_link_email


def test_magic_link_sign_in_url(monkeypatch):
    monkeypatch.setattr(
        app_settings.settings,
        "magic_link_app_base_url",
        "https://app.example.com/",
    )
    u = magic_link_sign_in_url("abc.def+ghi")
    assert u == "https://app.example.com/#/login?token=abc.def%2Bghi"


def test_magic_link_sign_in_url_empty_base(monkeypatch):
    monkeypatch.setattr(app_settings.settings, "magic_link_app_base_url", "")
    assert magic_link_sign_in_url("tok") is None


def test_send_magic_link_skips_without_api_key(monkeypatch):
    monkeypatch.setattr(app_settings.settings, "resend_api_key", "")
    assert send_magic_link_email("u@test.com", "token") is False


def test_send_magic_link_uses_resend(monkeypatch):
    monkeypatch.setattr(app_settings.settings, "resend_api_key", "re_test")
    monkeypatch.setattr(
        app_settings.settings,
        "magic_link_from_email",
        "CIH <noreply@agenticstudiolabs.com>",
    )
    monkeypatch.setattr(app_settings.settings, "magic_link_ttl_minutes", 15)
    mock_send = MagicMock(return_value={"id": "re_1"})
    monkeypatch.setattr("shared.magic_link_mail.resend.Emails.send", mock_send)

    assert send_magic_link_email("user@test.com", "signed.token") is True
    mock_send.assert_called_once()
    params = mock_send.call_args[0][0]
    assert params["to"] == ["user@test.com"]
    assert "signed.token" in params["html"]
    assert "signed.token" in params["text"]
