import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from notifier import send_notification


def test_send_notification_posts_embed(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("notifier.requests.post", return_value=mock_response) as mock_post:
        send_notification("https://danektran.github.io/ai-news-digest")

    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert "embeds" in payload
    assert "https://danektran.github.io/ai-news-digest" in payload["embeds"][0]["description"]


def test_send_notification_raises_without_webhook(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    with pytest.raises(EnvironmentError, match="DISCORD_WEBHOOK_URL"):
        send_notification("https://danektran.github.io/ai-news-digest")
