"""Entry point — orchestrates fetching, summarising, publishing, and notifying."""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from fetcher import fetch_all_articles
from summarizer import summarise
from publisher import publish
from notifier import send_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    logger.info("=== AI News Digest starting ===")

    try:
        config = load_config()
    except Exception as exc:
        logger.error("Failed to load config.yaml: %s", exc)
        sys.exit(1)

    feeds = config.get("feeds", [])
    lookback_hours = int(config.get("lookback_hours", 168))
    max_per_feed = int(config.get("max_articles_per_feed", 5))

    if not feeds:
        logger.error("No feeds configured in config.yaml")
        sys.exit(1)

    logger.info("Fetching articles from %d feed(s)…", len(feeds))
    try:
        articles = fetch_all_articles(feeds, lookback_hours, max_per_feed)
    except Exception as exc:
        logger.error("Unexpected error during fetching: %s", exc)
        sys.exit(1)

    logger.info("Fetched %d article(s) in total.", len(articles))

    logger.info("Summarising articles…")
    try:
        digest = summarise(articles)
    except Exception as exc:
        logger.error("Failed to generate digest: %s", exc)
        sys.exit(1)

    logger.info("Publishing to GitHub Pages…")
    try:
        url = publish(digest, date.today())
    except Exception as exc:
        logger.error("Failed to publish digest: %s", exc)
        sys.exit(1)

    logger.info("Sending Discord notification…")
    try:
        send_notification(url)
    except Exception as exc:
        logger.error("Failed to send notification: %s", exc)
        sys.exit(1)

    logger.info("=== AI News Digest completed successfully ===")


if __name__ == "__main__":
    main()
