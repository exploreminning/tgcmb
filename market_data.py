"""Fetch top crypto prices and 24h changes from CoinGecko (free, no API key)."""
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINS = ["bitcoin", "ethereum", "solana", "bnb"]
TIMEOUT = 15


def get_market_snapshot() -> tuple[Optional[str], Optional[str]]:
    """
    Fetch top 3-4 coins and return formatted string with emojis + chart image URL.
    Returns (text, image_url) tuple.
    """
    try:
        r = requests.get(
            COINGECKO_URL,
            params={
                "vs_currency": "usd",
                "ids": ",".join(COINS),
                "order": "market_cap_desc",
                "per_page": 4,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h",
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.exception("CoinGecko fetch failed: %s", e)
        return None, None

    if not data:
        return None, None

    lines = ["📊 Market Update"]
    chart_url = None
    for c in data[:4]:
        sym = (c.get("symbol") or "").upper()
        price = c.get("current_price")
        pct = c.get("price_change_percentage_24h")
        if sym and price is not None:
            if price >= 1000:
                pstr = f"${price/1000:.1f}k"
            elif price >= 1:
                pstr = f"${price:.2f}"
            else:
                pstr = f"${price:.4f}"
            if pct is not None:
                emoji = "🟢" if pct >= 0 else "🔴"
                sign = "+" if pct >= 0 else ""
                lines.append(f"{emoji} {sym} {pstr} ({sign}{pct:.1f}%)")
            else:
                lines.append(f"⚪ {sym} {pstr}")
        
        # Use Bitcoin's image as chart placeholder (first coin)
        if not chart_url and c.get("image"):
            chart_url = c.get("image")

    # If no image from API, use CoinGecko Bitcoin chart page (Telegram will preview)
    if not chart_url:
        chart_url = "https://www.coingecko.com/en/coins/bitcoin"
    
    return "\n".join(lines) if lines else None, chart_url
