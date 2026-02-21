"""Rewrite crypto news title + summary via LLM. Supports OpenAI, Groq, Ollama."""
import logging
from typing import Optional

from config import (
    GROQ_API_KEY,
    OPENAI_API_KEY,
    OLLAMA_BASE_URL,
    REWRITE_PROVIDER,
)

logger = logging.getLogger(__name__)

CAPTION_MAX_LEN = 1024

SYSTEM_PROMPT = """You rewrite crypto/finance news for a Telegram channel. Output only the rewritten content, no preamble.
- Keep factual and neutral. No speculation or opinions.
- Use a short headline (one line) then exactly ONE concise sentence summary.
- Do NOT include "Source:" or any source attribution.
- Use emojis sparingly (1-2 max) if appropriate: 📰 💰 🚀 📈 📉
- Total length must stay under 500 characters for Telegram caption."""

USER_PROMPT_TEMPLATE = """Rewrite this crypto/finance news for a channel post. Headline first, then ONE sentence summary. Do not mention the source.

Title: {title}

Summary: {summary}"""


def _call_openai(title: str, summary: str, source: str) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(title=title, summary=summary or "No summary", source=source or "Unknown")},
            ],
            max_tokens=400,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text[:CAPTION_MAX_LEN] if text else None
    except Exception as e:
        logger.exception("OpenAI rewrite failed: %s", e)
        return None


def _call_groq(title: str, summary: str, source: str) -> Optional[str]:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(title=title, summary=summary or "No summary", source=source or "Unknown")},
            ],
            max_tokens=400,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text[:CAPTION_MAX_LEN] if text else None
    except Exception as e:
        logger.exception("Groq rewrite failed: %s", e)
        return None


def _call_ollama(title: str, summary: str, source: str) -> Optional[str]:
    try:
        import requests
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(title=title, summary=summary or "No summary", source=source or "Unknown")},
            ],
            "stream": False,
        }
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        text = (data.get("message", {}).get("content") or "").strip()
        return text[:CAPTION_MAX_LEN] if text else None
    except Exception as e:
        logger.exception("Ollama rewrite failed: %s", e)
        return None


def rewrite(title: str, summary: str, source: str = "") -> Optional[str]:
    """
    Rewrite headline + summary for Telegram caption. Returns None on failure.
    Provider is chosen from config (openai, groq, ollama).
    """
    provider = REWRITE_PROVIDER
    if provider == "openai":
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not set")
            return None
        return _call_openai(title, summary, source)
    if provider == "groq":
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not set")
            return None
        return _call_groq(title, summary, source)
    if provider == "ollama":
        return _call_ollama(title, summary, source)
    logger.error("Unknown REWRITE_PROVIDER: %s", provider)
    return None
