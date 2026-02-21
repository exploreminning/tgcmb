"""Load configuration from environment. No secrets in repo."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent / ".env")

# Required
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()

# LLM
REWRITE_PROVIDER = os.getenv("REWRITE_PROVIDER", "openai").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")

# RSS: comma-separated or default feeds
_rss_env = os.getenv("RSS_FEED_URLS", "").strip()
if _rss_env:
    RSS_FEED_URLS = [u.strip() for u in _rss_env.split(",") if u.strip()]
else:
    RSS_FEED_URLS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://bitcoinist.com/feed/",
        "https://cryptopotato.com/feed/",
        "https://newsbtc.com/feed/",
    ]

# Schedule
POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "60"))
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))

# Image
DEFAULT_IMAGE_URL = os.getenv("DEFAULT_IMAGE_URL", "").strip()
FETCH_OG_IMAGE = os.getenv("FETCH_OG_IMAGE", "true").strip().lower() in ("true", "1", "yes")

# Etherscan (whale tracking)
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "").strip()

# CryptoPanic (opinions/sentiment)
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "").strip()

# Extra post limits
MAX_OPINIONS_PER_RUN = int(os.getenv("MAX_OPINIONS_PER_RUN", "2"))
ENABLE_MARKET_SNAPSHOT = os.getenv("ENABLE_MARKET_SNAPSHOT", "true").strip().lower() in ("true", "1", "yes")
ENABLE_WHALE_ALERTS = os.getenv("ENABLE_WHALE_ALERTS", "true").strip().lower() in ("true", "1", "yes")

# Persistence path for posted links
DATA_DIR = Path(__file__).resolve().parent / "data"
POSTED_LINKS_FILE = DATA_DIR / "posted_links.json"
MAX_POSTED_LINKS_STORED = 500
