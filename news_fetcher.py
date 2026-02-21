"""Fetch and parse RSS feeds; return list of news items (title, link, summary, source)."""
import logging
from datetime import datetime
from typing import Any

import feedparser

from config import RSS_FEED_URLS

logger = logging.getLogger(__name__)

# Default date for entries without published_parsed
EPOCH = datetime(1970, 1, 1)


def _parse_date(entry: Any) -> datetime:
    """Return parsed publication date or EPOCH if missing."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            from time import mktime
            return datetime.utcfromtimestamp(mktime(entry.published_parsed))
        except (TypeError, OSError):
            pass
    return EPOCH


def _entry_to_item(entry: Any, source: str) -> dict:
    """Convert feedparser entry to our item dict."""
    link = (entry.get("link") or "").strip()
    title = (entry.get("title") or "").strip() or "No title"
    summary = ""
    if entry.get("summary"):
        summary = entry.get("summary", "").strip()
    elif entry.get("description"):
        summary = entry.get("description", "").strip()
    # Strip HTML tags for plain text (simple approach)
    if summary:
        import re
        summary = re.sub(r"<[^>]+>", " ", summary)
        summary = " ".join(summary.split())[:500]
    return {
        "title": title,
        "link": link,
        "summary": summary,
        "source": source,
        "published": _parse_date(entry),
        "entry": entry,  # keep raw entry for image_fetcher (media_content, etc.)
    }


def fetch_all(feed_urls: list[str] | None = None) -> list[dict]:
    """
    Fetch all given RSS feeds, merge and dedupe by link, sort newest first.
    Returns list of items with keys: title, link, summary, source, published, entry.
    """
    urls = feed_urls or RSS_FEED_URLS
    all_items: list[dict] = []
    seen_links: set[str] = set()

    for url in urls:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "CryptoNewsBot/1.0"})
            if feed.bozo and not getattr(feed, "entries", None):
                logger.warning("Feed parse error or empty: %s", url)
                continue
            source = feed.feed.get("title", url) or url
            for entry in feed.entries:
                link = (entry.get("link") or "").strip()
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                all_items.append(_entry_to_item(entry, source))
        except Exception as e:
            logger.exception("Failed to fetch feed %s: %s", url, e)

    all_items.sort(key=lambda x: x["published"], reverse=True)
    return all_items
