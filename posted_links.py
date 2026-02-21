"""Persist posted article links in JSON to avoid reposting."""
import json
import logging
from pathlib import Path

from config import MAX_POSTED_LINKS_STORED, POSTED_LINKS_FILE

logger = logging.getLogger(__name__)


def _ensure_data_dir() -> None:
    POSTED_LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load() -> list[str]:
    _ensure_data_dir()
    if not POSTED_LINKS_FILE.exists():
        return []
    try:
        with open(POSTED_LINKS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("posted_links", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception as e:
        logger.warning("Could not load posted links: %s", e)
        return []


def _save(links: list[str]) -> None:
    _ensure_data_dir()
    try:
        with open(POSTED_LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump({"posted_links": links}, f, indent=0)
    except Exception as e:
        logger.exception("Could not save posted links: %s", e)


def is_posted(link: str) -> bool:
    return (link or "").strip() in set(_load())


def mark_posted(link: str) -> None:
    link = (link or "").strip()
    if not link:
        return
    links = _load()
    if link in links:
        return
    links.append(link)
    if len(links) > MAX_POSTED_LINKS_STORED:
        links = links[-MAX_POSTED_LINKS_STORED:]
    _save(links)
