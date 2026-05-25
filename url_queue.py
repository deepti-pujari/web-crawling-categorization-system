"""
url_queue.py
URL queue manager with deduplication, validation, and checkpoint support.
"""

import os
import re
import json
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """Return True if the URL has a valid scheme and netloc."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def normalise_url(url: str) -> str:
    """Strip trailing slashes and whitespace for consistent deduplication."""
    return url.strip().rstrip("/")


class UrlQueue:
    """
    Manages a deduplicated queue of URLs to crawl.
    Supports loading from a file, checkpointing progress,
    and resuming interrupted runs.
    """

    def __init__(self, checkpoint_path: str | None = None):
        self._pending: list[str] = []
        self._seen: set[str] = set()
        self._completed: set[str] = set()
        self._failed: set[str] = set()
        self.checkpoint_path = checkpoint_path

        if checkpoint_path and os.path.exists(checkpoint_path):
            self._load_checkpoint(checkpoint_path)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_from_file(self, path: str) -> int:
        """
        Read URLs from a plain-text file (one URL per line).
        Skips blanks, comments (#), invalid URLs, and already-seen URLs.
        Returns the number of URLs added to the queue.
        """
        added = 0
        skipped_invalid = 0
        skipped_duplicate = 0

        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                url = normalise_url(line)

                if not is_valid_url(url):
                    skipped_invalid += 1
                    continue

                if url in self._seen:
                    skipped_duplicate += 1
                    continue

                self._pending.append(url)
                self._seen.add(url)
                added += 1

        logger.info(
            "Loaded %d URLs (%d invalid, %d duplicate skipped) from %s",
            added, skipped_invalid, skipped_duplicate, path,
        )
        return added

    def load_from_list(self, urls: list[str]) -> int:
        """Add URLs from a Python list, applying the same dedup/validation rules."""
        added = 0
        for raw in urls:
            url = normalise_url(raw)
            if is_valid_url(url) and url not in self._seen:
                self._pending.append(url)
                self._seen.add(url)
                added += 1
        return added

    # ------------------------------------------------------------------
    # Queue operations
    # ------------------------------------------------------------------

    def pop_batch(self, size: int) -> list[str]:
        """Return up to `size` URLs from the front of the queue."""
        batch = self._pending[:size]
        self._pending = self._pending[size:]
        return batch

    def mark_completed(self, url: str):
        self._completed.add(url)

    def mark_failed(self, url: str):
        self._failed.add(url)

    # ------------------------------------------------------------------
    # Stats / introspection
    # ------------------------------------------------------------------

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    @property
    def total_seen(self) -> int:
        return len(self._seen)

    def is_empty(self) -> bool:
        return len(self._pending) == 0

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def save_checkpoint(self):
        """Persist queue state to disk so a run can be resumed."""
        if not self.checkpoint_path:
            return
        state = {
            "pending": self._pending,
            "seen": list(self._seen),
            "completed": list(self._completed),
            "failed": list(self._failed),
        }
        with open(self.checkpoint_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        logger.debug("Checkpoint saved to %s", self.checkpoint_path)

    def _load_checkpoint(self, path: str):
        """Restore queue state from a checkpoint file."""
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        self._pending = state.get("pending", [])
        self._seen = set(state.get("seen", []))
        self._completed = set(state.get("completed", []))
        self._failed = set(state.get("failed", []))
        logger.info(
            "Resumed from checkpoint: %d pending, %d completed, %d failed",
            len(self._pending), len(self._completed), len(self._failed),
        )
