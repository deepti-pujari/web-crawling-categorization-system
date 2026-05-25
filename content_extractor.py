"""
content_extractor.py
Extracts clean text and metadata signals from raw HTML for classification.
"""

import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags whose text is never useful for classification
_NOISE_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside"}

# Weights applied to each signal when building the combined text representation.
# Higher weight = signal repeated more times = more influence on TF-IDF.
_SIGNAL_WEIGHTS = {
    "title":       5,
    "description": 4,
    "keywords":    4,
    "h1":          3,
    "h2":          2,
    "h3":          1,
    "body":        1,
}


def _clean(text: str) -> str:
    """Collapse whitespace and strip leading/trailing space."""
    return re.sub(r"\s+", " ", text or "").strip()


class ContentExtractor:
    """
    Parses raw HTML and produces:
      - Individual signal fields (title, description, headings, body)
      - A weighted combined text string ready for the classifier
    """

    def extract(self, html: str, url: str = "") -> dict:
        """
        Parse `html` and return a dict with keys:
          title, description, keywords, h1, h2, h3, body_text, combined_text
        Returns an empty-signal dict if parsing fails.
        """
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:
            logger.warning("Failed to parse HTML for %s: %s", url, exc)
            return self._empty()

        title       = self._get_title(soup)
        description = self._get_meta(soup, "description")
        keywords    = self._get_meta(soup, "keywords")
        h1          = self._get_headings(soup, "h1")
        h2          = self._get_headings(soup, "h2")
        h3          = self._get_headings(soup, "h3")
        body_text   = self._get_body_text(soup)

        signals = {
            "title":       title,
            "description": description,
            "keywords":    keywords,
            "h1":          h1,
            "h2":          h2,
            "h3":          h3,
            "body":        body_text,
        }

        combined = self._build_combined(signals)

        return {
            "title":         title,
            "description":   description,
            "keywords":      keywords,
            "h1":            h1,
            "h2":            h2,
            "h3":            h3,
            "body_text":     body_text,
            "combined_text": combined,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_title(self, soup: BeautifulSoup) -> str:
        tag = soup.find("title")
        return _clean(tag.get_text()) if tag else ""

    def _get_meta(self, soup: BeautifulSoup, name: str) -> str:
        tag = soup.find("meta", attrs={"name": re.compile(name, re.I)})
        if tag and tag.get("content"):
            return _clean(tag["content"])
        # Also check og: variants
        og_tag = soup.find("meta", attrs={"property": re.compile(f"og:{name}", re.I)})
        if og_tag and og_tag.get("content"):
            return _clean(og_tag["content"])
        return ""

    def _get_headings(self, soup: BeautifulSoup, tag: str) -> str:
        texts = [_clean(h.get_text()) for h in soup.find_all(tag)]
        return " ".join(t for t in texts if t)

    def _get_body_text(self, soup: BeautifulSoup) -> str:
        # Remove noise tags in-place
        for noise in soup.find_all(_NOISE_TAGS):
            noise.decompose()

        # Extract remaining visible text
        raw = soup.get_text(separator=" ")
        cleaned = _clean(raw)

        # Truncate to first 2,000 chars to keep vectorisation fast
        return cleaned[:2000]

    def _build_combined(self, signals: dict) -> str:
        """
        Repeat each signal according to its weight so that title/description
        have a proportionally larger influence on the TF-IDF representation
        than raw body text.
        """
        parts = []
        for field, weight in _SIGNAL_WEIGHTS.items():
            text = signals.get(field, "")
            if text:
                parts.extend([text] * weight)
        return " ".join(parts)

    def _empty(self) -> dict:
        return {
            "title": "", "description": "", "keywords": "",
            "h1": "", "h2": "", "h3": "", "body_text": "", "combined_text": "",
        }
