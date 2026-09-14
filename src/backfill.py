from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.campaigns import rebuild_campaigns
from src.collectors.news import NewsCollector
from src.collectors.official import OfficialSiteCollector
from src.collectors.search import SearchCollector
from src.collectors.youtube import YouTubeCollector
from src.config import load_products
from src.db import connect, upsert_document
from src.dedupe import find_duplicate_candidates
from src.export import export_csv
from src.extract import extract_events
from src.report import write_report
from src.sample_data import sample_documents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start_date", required=True)
    parser.add_argument("--to", dest="end_date", required=True)
    parser.add_argument("--db", default=None)
    parser.add_argument("--use-sample", action="store_true", help="Seed sample documents for offline UI/report validation.")
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--limit-products", type=int, default=None)
    args = parser.parse_args()

    load_dotenv()
    conn = connect(Path(args.db) if args.db else None) if args.db else connect()
    products = load_products()
    if args.limit_products:
        products = products[: args.limit_products]

    collectors = []
    if not args.skip_network:
        collectors = [OfficialSiteCollector(), NewsCollector(), SearchCollector(), YouTubeCollector()]

    total_seen = 0
    for product in products:
        docs = []
        if args.use_sample:
            docs.extend(sample_documents(product))
        for collector in collectors:
            collected = collector.collect(product, args.start_date, args.end_date)
            docs.extend(collected)
        for doc in docs:
            upsert_document(conn, doc)
        total_seen += len(docs)
        print(f"{product.product}: collected/upserted {len(docs)} documents", flush=True)

    duplicate_count = find_duplicate_candidates(conn)
    event_count = extract_events(conn)
    campaign_count = rebuild_campaigns(conn)
    export_csv(conn)
    write_report(conn)
    print(f"Done. seen={total_seen}, duplicates={duplicate_count}, events={event_count}, campaigns={campaign_count}", flush=True)


if __name__ == "__main__":
    main()


