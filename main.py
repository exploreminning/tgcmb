"""Entrypoint: load config, run scheduler or single job (--run-once)."""
import argparse
import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from config import POST_INTERVAL_MINUTES
from scheduler import run_job

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "bot.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt=date_fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto news Telegram bot")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run one fetch/rewrite/post cycle then exit (for testing)",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    if args.run_once:
        logger.info("Running single job (--run-once)")
        run_job()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, "interval", minutes=POST_INTERVAL_MINUTES, id="crypto_news")
    logger.info("Scheduler started: every %s minutes", POST_INTERVAL_MINUTES)
    scheduler.start()


if __name__ == "__main__":
    main()
