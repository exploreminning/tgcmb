"""Get image URL for a news item: RSS media first, then og:image from article page."""
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_IMAGE_URL, FETCH_OG_IMAGE

logger = logging.getLogger(__name__)

TIMEOUT = 10
USER_AGENT = "CryptoNewsBot/1.0 (Telegram)"


def _is_https_url(url: Optional[str]) -> bool:
    if not url or not url.strip():
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def _image_from_rss_entry(entry: Any) -> Optional[str]:
    """Extract image URL from feedparser entry: media_content, media_thumbnail, enclosures."""
    # media_content (e.g. Media RSS)
    media = getattr(entry, "media_content", None) or entry.get("media_content") if hasattr(entry, "get") else None
    if media and isinstance(media, list):
        for m in media:
            if isinstance(m, dict):
                href = m.get("url") or m.get("href")
                mtype = (m.get("type") or "").lower()
                if href and ("image" in mtype or mtype.startswith("image/")):
                    if _is_https_url(href):
                        return href.strip()
            elif getattr(m, "get", None):
                href = m.get("url") or m.get("href")
                if href and _is_https_url(href):
                    return href.strip()

    # media_thumbnail
    thumb = getattr(entry, "media_thumbnail", None) or (entry.get("media_thumbnail") if hasattr(entry, "get") else None)
    if thumb and isinstance(thumb, list) and len(thumb) > 0:
        t = thumb[0]
        href = t.get("url") if isinstance(t, dict) else getattr(t, "url", None)
        if _is_https_url(href):
            return href.strip()

    # enclosures (image/*)
    enclosures = getattr(entry, "enclosures", None) or []
    for enc in enclosures:
        href = enc.get("href") if isinstance(enc, dict) else getattr(enc, "href", None)
        enc_type = (enc.get("type") or getattr(enc, "type", "") or "").lower()
        if href and ("image" in enc_type or enc_type.startswith("image/")):
            if _is_https_url(href):
                return href.strip()

    # Some feeds put image in summary/content as first <img>
    summary = getattr(entry, "summary", None) or entry.get("summary", "") or ""
    if isinstance(summary, str):
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary, re.I)
        if match:
            url = match.group(1).strip()
            if _is_https_url(url):
                return url
            # try absolute
            link = getattr(entry, "link", None) or entry.get("link", "")
            if link:
                abs_url = urljoin(link, url)
                if _is_https_url(abs_url):
                    return abs_url
    return None


def _og_image_from_url(article_url: str) -> Optional[str]:
    """Fetch article page and extract og:image meta."""
    if not _is_https_url(article_url):
        return None
    try:
        r = requests.get(
            article_url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text[:500000], "html.parser")
        tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if tag and tag.get("content"):
            url = tag["content"].strip()
            if _is_https_url(url):
                return url
            url = urljoin(article_url, url)
            if _is_https_url(url):
                return url
    except Exception as e:
        logger.debug("og:image fetch failed for %s: %s", article_url, e)
    return None


def get_image_url(item: dict) -> Optional[str]:
    """
    Return an image URL for the news item, or None.
    item must have "link" and optionally "entry" (raw feedparser entry).
    Uses: RSS media -> og:image (if FETCH_OG_IMAGE) -> DEFAULT_IMAGE_URL.
    """
    entry = item.get("entry")
    if entry:
        url = _image_from_rss_entry(entry)
        if url:
            return url

    link = (item.get("link") or "").strip()
    if link and FETCH_OG_IMAGE:
        url = _og_image_from_url(link)
        if url:
            return url

    if DEFAULT_IMAGE_URL and _is_https_url(DEFAULT_IMAGE_URL):
        return DEFAULT_IMAGE_URL
    return None
