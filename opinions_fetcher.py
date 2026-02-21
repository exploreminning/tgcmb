"""Fetch opinion/analysis news from CryptoPanic API."""
import logging

import requests

from config import CRYPTOPANIC_API_KEY
from posted_links import is_posted, mark_posted
from rewriter import rewrite
from telegram_poster import post

logger = logging.getLogger(__name__)

# Try without /v1/ first (free tier might use different endpoint)
CRYPTOPANIC_URL = "https://cryptopanic.com/api/posts/"
TIMEOUT = 15
# Note: Free tier doesn't support filter parameter


def fetch_opinions() -> list[dict]:
    """
    Fetch news from CryptoPanic with filter=important (opinions/analysis).
    Returns list of {title, link, summary, source, entry}.
    """
    if not CRYPTOPANIC_API_KEY:
        logger.warning("CRYPTOPANIC_API_KEY not set, skipping opinions")
        return []

    try:
        r = requests.get(
            CRYPTOPANIC_URL,
            params={
                "auth_token": CRYPTOPANIC_API_KEY,
                "public": "true",
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.exception("CryptoPanic fetch failed: %s", e)
        return []

    results = data.get("results", [])
    items = []
    for p in results[:20]:
        # Free tier only has title and description
        title = p.get("title") or "No title"
        description = p.get("description") or p.get("title", "")
        
        # Try to get URL - free tier might not have it, so use title as fallback
        url = p.get("url") or p.get("link", "") or p.get("source", {}).get("url", "") if isinstance(p.get("source"), dict) else ""
        # If no URL, create a placeholder (free tier limitation)
        if not url:
            url = f"https://cryptopanic.com/news/{p.get('id', '')}" if p.get("id") else ""
        
        source = p.get("source", {})
        source_name = source.get("title", "CryptoPanic") if isinstance(source, dict) else "CryptoPanic"
        
        items.append({
            "title": title,
            "link": url,
            "summary": description[:500] if description else title,
            "source": source_name,
            "entry": None,
        })
    return items


def post_opinions(max_posts: int = 2) -> int:
    """
    Fetch opinions, rewrite, and post. Returns number of posts made.
    """
    items = fetch_opinions()
    new_items = [i for i in items if not is_posted(i.get("link", ""))]
    to_process = new_items[:max_posts]
    posted = 0
    for item in to_process:
        link = item.get("link", "")
        title = item.get("title", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        try:
            caption = rewrite(title, summary, source)
            if not caption:
                continue
            if post(caption, None):
                mark_posted(link)
                posted += 1
                logger.info("Posted opinion: %s", link)
        except Exception as e:
            logger.exception("Error posting opinion %s: %s", link, e)
    return posted
