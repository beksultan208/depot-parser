#!/usr/bin/env python3
# ─────────────────────────────────────────────
# parser.py  –  Home Depot Product Parser
# ─────────────────────────────────────────────
# Usage:
#   python parser.py --mode test                    # JSON output, no DB
#   python parser.py --mode db                      # save to PostgreSQL
#   python parser.py --mode db --query "lumber"     # single category
# ─────────────────────────────────────────────
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from serpapi import GoogleSearch  # google-search-results package

import config

# ── Logging setup ─────────────────────────────

def setup_logging():
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / "parser.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


logger = logging.getLogger(__name__)

# ── SerpApi helpers ───────────────────────────

def search_products(query: str, page: int = 1) -> dict:
    """
    Step 1: search Home Depot for a query.
    SerpApi uses 0-based page index for home_depot engine (page=0 → first 24).
    """
    params = {
        "engine":  "home_depot",
        "q":       query,
        "ps":      24,           # products per page
        "start":   (page - 1) * 24,
        "api_key": config.SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    return search.get_dict()


def fetch_product_detail(product_id: str) -> dict:
    """Step 2: fetch full product detail by product_id."""
    params = {
        "engine":     "home_depot_product",
        "product_id": product_id,
        "api_key":    config.SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    return search.get_dict()


# ── Data extraction ───────────────────────────

def extract_product_ids(search_result: dict) -> list[str]:
    """Pull product IDs out of a Step-1 search result."""
    products = search_result.get("products", [])
    ids = []
    for p in products:
        pid = p.get("product_id") or p.get("item_id")
        if pid:
            ids.append(str(pid))
    return ids


def extract_product_data(detail: dict, category: str) -> dict:
    """
    Flatten the Step-2 detail response into the schema we store.
    Field names differ slightly across SerpApi versions so we probe
    several common keys.
    """
    product = detail.get("product_results") or detail.get("product") or {}

    # ── price ─────────────────────────────────
    price = None
    raw_price = product.get("price") or product.get("price_string") or ""
    if isinstance(raw_price, (int, float)):
        price = float(raw_price)
    elif isinstance(raw_price, str):
        cleaned = raw_price.replace("$", "").replace(",", "").strip()
        try:
            price = float(cleaned)
        except ValueError:
            price = None

    # ── description ───────────────────────────
    description = (
        product.get("description")
        or product.get("highlights_string")
        or ""
    )
    if isinstance(description, list):
        description = "\n".join(description)

    # ── specifications ────────────────────────
    specs = product.get("specifications") or []
    spec_lines = []
    if isinstance(specs, list):
        for s in specs:
            name  = s.get("name",  "")
            value = s.get("value", "")
            if name or value:
                spec_lines.append(f"{name}: {value}")
    if spec_lines and not description:
        description = "\n".join(spec_lines)

    return {
        "product_id":   str(product.get("product_id") or product.get("item_id") or ""),
        "title":        product.get("title") or product.get("name") or "",
        "price":        price,
        "description":  description,
        "brand":        product.get("brand") or product.get("brand_name") or "",
        "model_number": product.get("model_number") or product.get("model") or "",
        "category":     category,
        "raw_json":     detail,
    }


# ── Core pipeline ─────────────────────────────

def parse_query(query: str, mode: str, conn=None, test_results: list | None = None):
    """
    Run the full 2-step pipeline for one search query.

    Returns (total_found, saved, skipped) counts for this query.
    """
    total_found = saved = skipped = 0

    for page in range(1, config.MAX_PAGES + 1):
        logger.info("  [%s] page %d / %d …", query, page, config.MAX_PAGES)
        try:
            search_result = search_products(query, page)
        except Exception as exc:
            logger.error("  Search API error (page %d): %s", page, exc)
            break

        if "error" in search_result:
            logger.error("  SerpApi error: %s", search_result["error"])
            break

        product_ids = extract_product_ids(search_result)
        if not product_ids:
            logger.info("  No more products on page %d — stopping.", page)
            break

        logger.info("  Found %d product IDs on page %d.", len(product_ids), page)
        total_found += len(product_ids)

        for pid in product_ids:
            time.sleep(config.REQUEST_DELAY)
            try:
                detail = fetch_product_detail(pid)
            except Exception as exc:
                logger.warning("  Detail fetch failed for %s: %s", pid, exc)
                skipped += 1
                continue

            if "error" in detail:
                logger.warning("  Detail error for %s: %s", pid, detail["error"])
                skipped += 1
                continue

            product = extract_product_data(detail, category=query)

            if not product["product_id"]:
                product["product_id"] = pid  # fallback

            # ── Save ──────────────────────────
            if mode == "db":
                import db as db_module
                inserted = db_module.save_product(conn, product)
                if inserted:
                    saved += 1
                    logger.debug("  Saved: %s", product["title"])
                else:
                    skipped += 1
                    logger.debug("  Duplicate (skipped): %s", product["product_id"])
            else:  # test mode
                # Dedup in-memory by product_id
                existing_ids = {r["product_id"] for r in test_results}
                if product["product_id"] not in existing_ids:
                    # raw_json may not be JSON-serialisable cleanly; keep it
                    test_results.append(product)
                    saved += 1
                else:
                    skipped += 1

        time.sleep(config.REQUEST_DELAY)

    return total_found, saved, skipped


# ── Test-mode JSON output ─────────────────────

def save_test_results(results: list):
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "test_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)
    logger.info("Test results written → %s  (%d products)", out_path, len(results))


# ── Entry point ───────────────────────────────

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Home Depot product parser via SerpApi")
    parser.add_argument(
        "--mode",
        choices=["db", "test"],
        default="test",
        help="'db' saves to PostgreSQL; 'test' saves to output/test_results.json",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Parse a single category instead of the full SEARCH_QUERIES list",
    )
    args = parser.parse_args()

    queries = [args.query] if args.query else config.SEARCH_QUERIES

    logger.info("=" * 60)
    logger.info("Home Depot Parser  |  mode=%s  |  queries=%s", args.mode, queries)
    logger.info("=" * 60)

    # ── DB setup (production mode only) ──────
    conn = None
    if args.mode == "db":
        try:
            import db as db_module
            conn = db_module.get_connection()
            db_module.init_db(conn)
            logger.info("PostgreSQL connection established.")
        except Exception as exc:
            logger.critical("Cannot connect to PostgreSQL: %s", exc)
            sys.exit(1)

    # ── Run queries ───────────────────────────
    test_results: list = []
    grand_total = grand_saved = grand_skipped = 0

    for q in queries:
        logger.info("")
        logger.info("─── Query: %s ───", q)
        total, saved, skipped = parse_query(
            query=q,
            mode=args.mode,
            conn=conn,
            test_results=test_results,
        )
        grand_total   += total
        grand_saved   += saved
        grand_skipped += skipped
        logger.info(
            "  → found=%d  saved=%d  skipped=%d", total, saved, skipped
        )

    # ── Finalise ──────────────────────────────
    if args.mode == "test":
        save_test_results(test_results)

    if conn:
        conn.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info(
        "SUMMARY  total_found=%-5d  saved=%-5d  skipped=%-5d",
        grand_total,
        grand_saved,
        grand_skipped,
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
