"""Entry point — orchestrates fetching, summarising, and notifying."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml

from fetcher import fetch_all_articles
from summarizer import summarise
from notifier import send_digest

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
    lookback_hours = int(config.get("lookback_hours", 24))
    max_per_feed = int(config.get("max_articles_per_feed", 5))

    if not feeds:
        logger.error("No feeds configured in config.yaml")
        sys.exit(1)

    # Step 1 — fetch
    logger.info("Fetching articles from %d feed(s)…", len(feeds))
    try:
        articles = fetch_all_articles(feeds, lookback_hours, max_per_feed)
    except Exception as exc:
        logger.error("Unexpected error during fetching: %s", exc)
        sys.exit(1)

    logger.info("Fetched %d article(s) in total.", len(articles))

    # Step 2 — summarise
    logger.info("Summarising articles…")
    try:
        digest = summarise(articles)
    except Exception as exc:
        logger.error("Failed to generate digest: %s", exc)
        sys.exit(1)

    # Step 3 — notify
    logger.info("Sending digest to Discord…")
    try:
        send_digest(digest)
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        sys.exit(1)

    logger.info("=== AI News Digest completed successfully ===")


if __name__ == "__main__":
    main()
