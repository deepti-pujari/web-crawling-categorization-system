"""
reporter.py
Writes crawl + classification results to CSV and JSON.
"""

import csv
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Columns written to the CSV output
CSV_COLUMNS = [
    "url",
    "final_url",
    "category",
    "confidence",
    "status",
    "http_code",
    "title",
    "description",
    "crawled_at",
    "error",
]


class Reporter:
    """Writes results to CSV (primary) and optionally JSON (full detail)."""

    def __init__(self, csv_path: str, json_path: str | None = None):
        self.csv_path = csv_path
        self.json_path = json_path
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)

    def write(self, results: list[dict]):
        """Write all results to CSV and optionally JSON."""
        self._write_csv(results)
        if self.json_path:
            self._write_json(results)
        logger.info("Results written to %s", self.csv_path)

    def append(self, results: list[dict]):
        """
        Append a batch of results to the CSV without rewriting the whole file.
        Useful for streaming large runs to disk in chunks.
        """
        file_exists = os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            for row in results:
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _write_csv(self, results: list[dict]):
        with open(self.csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for row in results:
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

    def _write_json(self, results: list[dict]):
        os.makedirs(os.path.dirname(os.path.abspath(self.json_path)), exist_ok=True)
        export = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_urls":   len(results),
            "results":      results,
        }
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump(export, fh, indent=2, ensure_ascii=False)
        logger.info("JSON export written to %s", self.json_path)
