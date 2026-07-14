"""Email resolution for CMA chat — request body vs conversation fallback."""

from unittest.mock import patch

from services.cma_stream import resolve_user_email


def test_resolve_prefers_request_email():
    email = resolve_user_email("user@example.com", "conv-123")
    assert email == "user@example.com"


def test_resolve_falls_back_to_conversation():
    with patch(
        "db.client.get_conversation",
        return_value={"user_email": "stored@example.com"},
    ):
        email = resolve_user_email(None, "conv-456")

    assert email == "stored@example.com"


def test_resolve_invalid_request_uses_conversation():
    with patch(
        "db.client.get_conversation",
        return_value={"user_email": "stored@example.com"},
    ):
        email = resolve_user_email("not-an-email", "conv-789")

    assert email == "stored@example.com"


def test_resolve_returns_none_when_missing_everywhere():
    with patch("db.client.get_conversation", return_value=None):
        assert resolve_user_email(None, "conv-empty") is None
