"""
main.py
Entry point — orchestrates the full crawl → extract → classify → report pipeline.

Usage:
    python src/main.py --input data/sample_urls.txt --output results/output.csv
    python src/main.py --input urls.txt --output results/out.csv --workers 20 --json-output results/out.json
    python src/main.py --input urls.txt --output results/out.csv --checkpoint results/ckpt.json
"""

import argparse
import json
import logging
import sys
import os
import time
from pathlib import Path

# Allow running as `python src/main.py` from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.crawler.url_queue import UrlQueue
from src.crawler.crawler import WebCrawler
from src.categorizer.classifier import WebsiteClassifier
from src.output.reporter import Reporter

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

DEFAULT_CATEGORIES_PATH = Path(__file__).parent / "categorizer" / "categories.json"
BATCH_SIZE = 50   # URLs crawled per batch (tune to memory/network)


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------

def run(
    input_path: str,
    output_csv: str,
    categories_path: str = str(DEFAULT_CATEGORIES_PATH),
    workers: int = 10,
    delay: float = 0.5,
    timeout: int = 10,
    json_output: str | None = None,
    checkpoint: str | None = None,
):
    start_time = time.time()
    logger.info("=" * 55)
    logger.info("  Web Crawling & Categorization System")
    logger.info("  Input      : %s", input_path)
    logger.info("  Output     : %s", output_csv)
    logger.info("  Categories : %s", categories_path)
    logger.info("  Workers    : %d", workers)
    logger.info("=" * 55)

    # 1. Load categories
    with open(categories_path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    categories = config["categories"]
    logger.info("Loaded %d categories", len(categories))

    # 2. Build URL queue
    queue = UrlQueue(checkpoint_path=checkpoint)
    url_count = queue.load_from_file(input_path)
    if url_count == 0 and queue.pending_count == 0:
        logger.error("No valid URLs found in %s. Exiting.", input_path)
        sys.exit(1)

    # 3. Initialise components
    crawler    = WebCrawler(workers=workers, delay=delay, timeout=timeout)
    classifier = WebsiteClassifier(categories=categories)
    reporter   = Reporter(csv_path=output_csv, json_path=json_output)

    all_results: list[dict] = []
    batch_num = 0

    # 4. Crawl → classify → write in batches
    while not queue.is_empty():
        batch_num += 1
        batch_urls = queue.pop_batch(BATCH_SIZE)
        logger.info(
            "Batch %d — crawling %d URLs (%d remaining in queue)",
            batch_num, len(batch_urls), queue.pending_count,
        )

        # Crawl
        crawled = crawler.crawl_batch(batch_urls)

        # Classify
        classifications = classifier.classify_batch(crawled)

        # Merge classification into each result dict
        for page, (category, confidence) in zip(crawled, classifications):
            page["category"]   = category
            page["confidence"] = confidence
            if page["status"] == "SUCCESS":
                queue.mark_completed(page["url"])
            else:
                queue.mark_failed(page["url"])

        # Append this batch to CSV immediately (streaming write)
        reporter.append(crawled)
        all_results.extend(crawled)

        # Checkpoint after each batch
        queue.save_checkpoint()

        # Progress log
        success = sum(1 for r in crawled if r["status"] == "SUCCESS")
        logger.info(
            "Batch %d done — %d/%d succeeded. Total: %d processed.",
            batch_num, success, len(batch_urls), len(all_results),
        )

    # 5. Write JSON export if requested (full run, not streaming)
    if json_output:
        reporter.write(all_results)

    # 6. Summary
    elapsed = time.time() - start_time
    total      = len(all_results)
    successful = sum(1 for r in all_results if r["status"] == "SUCCESS")
    failed     = total - successful

    logger.info("=" * 55)
    logger.info("  COMPLETE")
    logger.info("  Total URLs processed : %d", total)
    logger.info("  Successful           : %d", successful)
    logger.info("  Failed               : %d", failed)
    logger.info("  Time elapsed         : %.1fs", elapsed)
    logger.info("  Output               : %s", output_csv)
    logger.info("=" * 55)

    # Category distribution
    from collections import Counter
    dist = Counter(r["category"] for r in all_results if r["status"] == "SUCCESS")
    logger.info("Category distribution:")
    for cat, count in dist.most_common():
        pct = count / successful * 100 if successful else 0
        logger.info("  %-25s %4d  (%.1f%%)", cat, count, pct)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Crawl and categorize websites into N predefined categories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input",       required=True,  help="Path to input URL file (one URL per line)")
    parser.add_argument("--output",      required=True,  help="Path for CSV output")
    parser.add_argument("--categories",  default=str(DEFAULT_CATEGORIES_PATH), help="Path to categories JSON")
    parser.add_argument("--workers",     type=int,   default=10,  help="Parallel crawl threads")
    parser.add_argument("--delay",       type=float, default=0.5, help="Politeness delay between requests (s)")
    parser.add_argument("--timeout",     type=int,   default=10,  help="Per-URL timeout (s)")
    parser.add_argument("--json-output", default=None, help="Optional path for full JSON export")
    parser.add_argument("--checkpoint",  default=None, help="Checkpoint file path (enables resume)")

    args = parser.parse_args()

    run(
        input_path     = args.input,
        output_csv     = args.output,
        categories_path= args.categories,
        workers        = args.workers,
        delay          = args.delay,
        timeout        = args.timeout,
        json_output    = args.json_output,
        checkpoint     = args.checkpoint,
    )


if __name__ == "__main__":
    main()
