"""Post rewritten news to Telegram channel: sendPhoto with caption above, or sendMessage."""
import logging
import time
from typing import Optional

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

BASE_URL = "https://api.telegram.org/bot"
POST_DELAY_SECONDS = 1.5
CAPTION_MAX_LEN = 1024


def _api(method: str, **kwargs) -> dict:
    url = f"{BASE_URL}{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=kwargs, timeout=30)
        data = r.json() if r.text else {}
        if not data.get("ok"):
            logger.warning("Telegram API %s: %s", method, data)
        return data
    except Exception as e:
        logger.exception("Telegram request failed: %s", e)
        return {"ok": False, "description": str(e)}


def post(caption: str, image_url: Optional[str] = None) -> bool:
    """
    Post one item to the channel. Caption above image when image is used.
    - If image_url is set: sendPhoto with caption and show_caption_above_media=True.
    - Else: sendMessage with caption only.
    caption is truncated to 1024 chars.
    Returns True if successful.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set")
        return False

    text = (caption or "").strip()[:CAPTION_MAX_LEN]
    if not text:
        logger.warning("Empty caption, skipping post")
        return False

    if image_url and image_url.startswith("http"):
        resp = _api(
            "sendPhoto",
            chat_id=TELEGRAM_CHANNEL_ID,
            photo=image_url,
            caption=text,
            show_caption_above_media=True,
        )
    else:
        resp = _api(
            "sendMessage",
            chat_id=TELEGRAM_CHANNEL_ID,
            text=text,
        )

    if resp.get("ok"):
        time.sleep(POST_DELAY_SECONDS)
        return True
    return False
