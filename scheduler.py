"""One job: market snapshot, whale alerts, opinions, news -> post."""
import logging

from config import (
    ENABLE_MARKET_SNAPSHOT,
    ENABLE_WHALE_ALERTS,
    MAX_OPINIONS_PER_RUN,
    MAX_POSTS_PER_RUN,
)
from image_fetcher import get_image_url
from market_data import get_market_snapshot
from news_fetcher import fetch_all
from opinions_fetcher import post_opinions
from posted_links import is_posted, mark_posted
from rewriter import rewrite
from telegram_poster import post
from whale_tracker import get_whale_alerts

logger = logging.getLogger(__name__)


def run_job() -> None:
    # 1. Market snapshot (prices)
    if ENABLE_MARKET_SNAPSHOT:
        snapshot, chart_url = get_market_snapshot()
        if snapshot:
            post(snapshot, chart_url)
            logger.info("Posted market snapshot")

    # 2. Whale alerts
    if ENABLE_WHALE_ALERTS:
        whale_text = get_whale_alerts()
        if whale_text:
            post(whale_text, None)
            logger.info("Posted whale alerts")

    # 3. Opinions (CryptoPanic)
    post_opinions(max_posts=MAX_OPINIONS_PER_RUN)

    # 4. News (RSS)
    items = fetch_all()
    new_items = [i for i in items if not is_posted(i.get("link", ""))]
    to_process = new_items[:MAX_POSTS_PER_RUN]

    for item in to_process:
        link = item.get("link", "")
        title = item.get("title", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        try:
            caption = rewrite(title, summary, source)
            if not caption:
                logger.warning("Skip (rewrite failed): %s", link)
                continue
            image_url = get_image_url(item)
            if post(caption, image_url):
                mark_posted(link)
                logger.info("Posted: %s", link)
            else:
                logger.warning("Post failed: %s", link)
        except Exception as e:
            logger.exception("Error processing %s: %s", link, e)
