"""Sends a link notification to Discord via webhook."""

from __future__ import annotations

import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)


def send_notification(url: str) -> None:
    """Post a short Discord embed with the link to the published digest.

    Args:
        url: Public URL of the published digest page.

    Raises:
        EnvironmentError: If DISCORD_WEBHOOK_URL is not set.
        requests.HTTPError: If Discord returns a non-2xx status.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set")

    today_str = date.today().strftime("%d. %m. %Y")
    payload = {
        "embeds": [
            {
                "title": f"🗞️ Nový týdenní AI digest — {today_str}",
                "description": f"Tento týden v umělé inteligenci je online:\n{url}",
                "color": 0x5865F2,
            }
        ]
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
    logger.info("Discord notification sent.")
