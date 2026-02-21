"""Fetch large ETH/ERC20 transfers from Etherscan (whale tracking)."""
import logging
from typing import Optional

import requests

from config import ETHERSCAN_API_KEY

logger = logging.getLogger(__name__)

ETHERSCAN_URL = "https://api.etherscan.io/api"
TIMEOUT = 15

# Token contracts (Ethereum mainnet)
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # 6 decimals
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # 6 decimals
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"  # 18 decimals

# Min USD value to consider "whale" (approximate)
MIN_USD = 1_000_000
# Approximate USD per token (for filtering)
USDT_USD = 1.0
USDC_USD = 1.0
WETH_USD = 3500.0


def _format_value(raw: str, decimals: int, usd_per_unit: float) -> tuple[float, float]:
    """Convert raw token value to human amount and USD."""
    try:
        val = int(raw) / (10**decimals)
        usd = val * usd_per_unit
        return val, usd
    except (ValueError, ZeroDivisionError):
        return 0.0, 0.0


def _fetch_token_transfers(contract: str, decimals: int, symbol: str, usd_per: float) -> list[dict]:
    """Fetch recent transfers for a token contract and filter by min USD."""
    if not ETHERSCAN_API_KEY:
        return []
    try:
        r = requests.get(
            ETHERSCAN_URL,
            params={
                "module": "account",
                "action": "tokentx",
                "contractaddress": contract,
                "page": 1,
                "offset": 50,
                "sort": "desc",
                "apikey": ETHERSCAN_API_KEY,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.debug("Etherscan tokentx failed for %s: %s", symbol, e)
        return []

    if data.get("status") != "1" or not data.get("result"):
        return []

    results = []
    for tx in data["result"]:
        raw = tx.get("value", "0")
        amount, usd = _format_value(raw, decimals, usd_per)
        if usd < MIN_USD:
            continue
        results.append({
            "from": tx.get("from", ""),
            "to": tx.get("to", ""),
            "value": amount,
            "value_usd": usd,
            "symbol": symbol,
            "hash": tx.get("hash", ""),
        })
    return results


def get_whale_alerts() -> Optional[str]:
    """
    Fetch recent large transfers (USDT, USDC, WETH) and return formatted string.
    """
    if not ETHERSCAN_API_KEY:
        logger.warning("ETHERSCAN_API_KEY not set, skipping whale alerts")
        return None

    all_txs = []
    all_txs.extend(_fetch_token_transfers(USDT, 6, "USDT", USDT_USD))
    all_txs.extend(_fetch_token_transfers(USDC, 6, "USDC", USDC_USD))
    all_txs.extend(_fetch_token_transfers(WETH, 18, "WETH", WETH_USD))

    all_txs.sort(key=lambda x: x["value_usd"], reverse=True)
    top = all_txs[:5]

    if not top:
        return None

    lines = ["Whale moves"]
    for t in top:
        amt = t["value"]
        sym = t["symbol"]
        usd = t["value_usd"]
        if amt >= 1_000_000:
            amt_str = f"{amt/1e6:.1f}M"
        elif amt >= 1_000:
            amt_str = f"{amt/1e3:.1f}K"
        else:
            amt_str = f"{amt:.2f}"
        fr = t["from"][:6] + "..." + t["from"][-4:] if len(t["from"]) >= 10 else t["from"]
        to = t["to"][:6] + "..." + t["to"][-4:] if len(t["to"]) >= 10 else t["to"]
        usd_str = f"${usd/1e6:.1f}M" if usd >= 1e6 else f"${usd/1e3:.0f}K"
        lines.append(f"• {amt_str} {sym} ({usd_str}) {fr} -> {to}")

    return "\n".join(lines)
