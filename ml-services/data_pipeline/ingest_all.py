"""
MarketMind Full Data Ingestion CLI
Usage:
    python ingest_all.py --stocks --period 1mo
    python ingest_all.py --mf --period 6mo
    python ingest_all.py --options
    python ingest_all.py --all --period 1mo
"""
import argparse
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ingest_all")


def ingest_stocks(period: str, workers: int):
    """Ingest all stocks from the symbol universe."""
    from data_pipeline.stock_fetcher import StockFetcher
    from data_pipeline.symbols import get_stock_count

    logger.info(f"=== STOCKS INGESTION ({get_stock_count()} symbols, period={period}) ===")
    start = time.time()
    fetcher = StockFetcher()
    result = fetcher.fetch_all_stocks(period=period, max_workers=workers)
    elapsed = time.time() - start
    logger.info(f"Stocks done in {elapsed:.1f}s: {result['success']}/{result['total']} succeeded")
    return result


def ingest_mf(period: str):
    """Ingest all mutual fund NAV data."""
    from data_pipeline.mf_fetcher import MFNavFetcher

    logger.info(f"=== MUTUAL FUNDS INGESTION (period={period}) ===")
    start = time.time()
    fetcher = MFNavFetcher()
    result = fetcher.fetch_all_mf(period=period)
    elapsed = time.time() - start
    logger.info(f"MF done in {elapsed:.1f}s: {result['success']}/{result['total']} succeeded")
    return result


def ingest_options():
    """Ingest options chain data for F&O stocks."""
    from data_pipeline.options_fetcher import OptionsFetcher

    logger.info("=== OPTIONS CHAIN INGESTION ===")
    start = time.time()
    fetcher = OptionsFetcher()
    result = fetcher.fetch_all_options()
    elapsed = time.time() - start
    logger.info(f"Options done in {elapsed:.1f}s: {result['success']}/{result['total']} succeeded")
    return result


def main():
    parser = argparse.ArgumentParser(description="MarketMind Full Data Ingestion")
    parser.add_argument("--stocks", action="store_true", help="Ingest all stocks")
    parser.add_argument("--mf", action="store_true", help="Ingest mutual fund NAVs")
    parser.add_argument("--options", action="store_true", help="Ingest options chains")
    parser.add_argument("--all", action="store_true", help="Ingest everything")
    parser.add_argument("--period", default="1mo", help="Data period (default: 1mo)")
    parser.add_argument("--workers", type=int, default=5, help="Max concurrent workers")

    args = parser.parse_args()

    if not any([args.stocks, args.mf, args.options, args.all]):
        parser.print_help()
        return

    logger.info(f"MarketMind Data Ingestion started at {datetime.now().isoformat()}")
    overall_start = time.time()
    results = {}

    if args.stocks or args.all:
        results["stocks"] = ingest_stocks(args.period, args.workers)

    if args.mf or args.all:
        results["mf"] = ingest_mf(args.period)

    if args.options or args.all:
        results["options"] = ingest_options()

    total_elapsed = time.time() - overall_start

    logger.info("=" * 60)
    logger.info(f"INGESTION COMPLETE in {total_elapsed:.1f}s")
    for key, res in results.items():
        logger.info(f"  {key}: {res['success']}/{res['total']} succeeded")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
