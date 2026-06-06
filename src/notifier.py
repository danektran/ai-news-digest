"""Sends the digest to Discord via webhook."""

from __future__ import annotations

import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1900  # Discord limit is 2000; leave headroom


def _split_into_chunks(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of at most `size` characters, breaking at newlines."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > size and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))

    return chunks


def _send_embed(webhook_url: str, title: str, description: str) -> None:
    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 0x5865F2,  # Discord blurple
            }
        ]
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()


def _send_plain(webhook_url: str, content: str) -> None:
    payload = {"content": content}
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()


def send_digest(digest: str) -> None:
    """Post the digest to Discord.

    The first chunk is sent as a rich embed with a header; subsequent chunks
    are sent as plain messages.

    Args:
        digest: The full Czech-language digest string.

    Raises:
        EnvironmentError: If DISCORD_WEBHOOK_URL is not set.
        requests.HTTPError: If Discord returns a non-2xx status.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set")

    today_str = date.today().strftime("%d. %m. %Y")
    header_title = f"🤖 Denní AI souhrn — {today_str}"

    chunks = _split_into_chunks(digest)
    if not chunks:
        logger.warning("Digest is empty; nothing to send.")
        return

    logger.info("Sending digest in %d chunk(s) to Discord…", len(chunks))

    # First chunk goes as an embed
    _send_embed(webhook_url, title=header_title, description=chunks[0])

    # Remaining chunks are plain follow-up messages
    for chunk in chunks[1:]:
        _send_plain(webhook_url, chunk)

    logger.info("Digest sent successfully.")
