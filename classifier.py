"""
classifier.py
Category assignment using cosine similarity on TF-IDF vectors,
with optional domain-name boosting for known high-confidence domains.
"""

import logging
from urllib.parse import urlparse

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)

# Confidence added when the URL domain exactly matches a category's domain list.
_DOMAIN_BOOST = 0.25

# Minimum cosine similarity to assign a category (below = "Uncategorized").
_CONFIDENCE_THRESHOLD = 0.05


class WebsiteClassifier:
    """
    Classifies a web page into one of N configurable categories.

    Classification pipeline:
      1. Transform page combined_text via TF-IDF.
      2. Compute cosine similarity against every category profile vector.
      3. Apply domain-name boost if the URL matches a known domain.
      4. Assign the highest-scoring category (if above threshold).
    """

    def __init__(self, categories: list[dict]):
        self.categories = categories
        self._extractor = FeatureExtractor()
        self._extractor.fit_categories(categories)

        # Build domain → category_index lookup for O(1) boost
        self._domain_index: dict[str, int] = {}
        for idx, cat in enumerate(categories):
            for domain in cat.get("domains", []):
                self._domain_index[domain.lower()] = idx

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, combined_text: str, url: str = "") -> tuple[str, float]:
        """
        Classify a single page.

        Args:
            combined_text: Weighted text from ContentExtractor.
            url:           Original URL (used for optional domain boost).

        Returns:
            (category_name, confidence_score)  — score in [0.0, 1.0]
        """
        if not combined_text.strip():
            return "Uncategorized", 0.0

        page_vector = self._extractor.transform(combined_text)
        similarities = cosine_similarity(page_vector, self._extractor.category_vectors).flatten()

        # Domain boost
        domain = self._extract_domain(url)
        if domain in self._domain_index:
            boosted_idx = self._domain_index[domain]
            similarities[boosted_idx] = min(1.0, similarities[boosted_idx] + _DOMAIN_BOOST)
            logger.debug("Domain boost applied for %s → %s", domain, self.categories[boosted_idx]["name"])

        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])

        if confidence < _CONFIDENCE_THRESHOLD:
            return "Uncategorized", round(confidence, 4)

        return self.categories[best_idx]["name"], round(confidence, 4)

    def classify_batch(self, pages: list[dict]) -> list[tuple[str, float]]:
        """
        Classify a batch of crawled page dicts (must contain 'combined_text' and 'url').
        More efficient than calling classify() in a loop for large batches.
        """
        texts = [p.get("combined_text", "") for p in pages]
        urls  = [p.get("url", "")           for p in pages]

        # Handle empty-text pages upfront
        results = [None] * len(pages)
        valid_indices = [i for i, t in enumerate(texts) if t.strip()]

        if not valid_indices:
            return [("Uncategorized", 0.0)] * len(pages)

        valid_texts = [texts[i] for i in valid_indices]
        matrix = self._extractor.transform_batch(valid_texts)
        similarities_matrix = cosine_similarity(matrix, self._extractor.category_vectors)

        for list_pos, orig_idx in enumerate(valid_indices):
            similarities = similarities_matrix[list_pos].copy()
            domain = self._extract_domain(urls[orig_idx])

            if domain in self._domain_index:
                boosted_idx = self._domain_index[domain]
                similarities[boosted_idx] = min(1.0, similarities[boosted_idx] + _DOMAIN_BOOST)

            best_idx = int(np.argmax(similarities))
            confidence = float(similarities[best_idx])

            if confidence < _CONFIDENCE_THRESHOLD:
                results[orig_idx] = ("Uncategorized", round(confidence, 4))
            else:
                results[orig_idx] = (self.categories[best_idx]["name"], round(confidence, 4))

        # Fill in empty-text pages
        for i in range(len(pages)):
            if results[i] is None:
                results[i] = ("Uncategorized", 0.0)

        return results

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Return the bare domain (e.g. 'github.com') from a URL string."""
        try:
            netloc = urlparse(url).netloc.lower()
            # Strip www. prefix
            return netloc.removeprefix("www.")
        except Exception:
            return ""
