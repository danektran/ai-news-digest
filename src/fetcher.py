"""Fetches and filters articles from RSS feeds."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import feedparser
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def _parse_published_date(entry: Any) -> datetime | None:
    """Extract and parse a published date from a feed entry."""
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = dateutil_parser.parse(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
    # feedparser also stores parsed time tuples
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                import calendar
                timestamp = calendar.timegm(parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except Exception:
                continue
    return None


def fetch_articles(feed_config: dict, lookback_hours: int, max_per_feed: int) -> list[dict]:
    """Fetch recent articles from a single RSS feed.

    Args:
        feed_config: Dict with 'name' and 'url' keys.
        lookback_hours: Only return articles published within this many hours.
        max_per_feed: Maximum number of articles to return per feed.

    Returns:
        List of article dicts with keys: title, url, summary, source_name, published_date.
    """
    name = feed_config["name"]
    url = feed_config["url"]
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=lookback_hours)

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("Failed to fetch feed '%s': %s", name, exc)
        return []

    if feed.bozo and not feed.entries:
        logger.warning("Feed '%s' returned a malformed/empty response", name)
        return []

    articles: list[dict] = []
    for entry in feed.entries:
        published = _parse_published_date(entry)
        if published is None:
            # Include entries without a date so we don't miss brand-new posts
            published = datetime.now(tz=timezone.utc)

        if published < cutoff:
            continue

        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        summary = summary.strip() if summary else ""

        if not title or not link:
            continue

        articles.append(
            {
                "title": title,
                "url": link,
                "summary": summary,
                "source_name": name,
                "published_date": published,
            }
        )

        if len(articles) >= max_per_feed:
            break

    logger.info("Feed '%s': fetched %d article(s)", name, len(articles))
    return articles


def fetch_all_articles(
    feeds: list[dict], lookback_hours: int, max_per_feed: int
) -> list[dict]:
    """Fetch articles from all configured feeds.

    Args:
        feeds: List of feed config dicts.
        lookback_hours: Lookback window in hours.
        max_per_feed: Max articles per feed.

    Returns:
        Combined, time-sorted list of articles from all feeds.
    """
    all_articles: list[dict] = []
    for feed_config in feeds:
        articles = fetch_articles(feed_config, lookback_hours, max_per_feed)
        all_articles.extend(articles)

    all_articles.sort(key=lambda a: a["published_date"], reverse=True)
    logger.info("Total articles fetched across all feeds: %d", len(all_articles))
    return all_articles
