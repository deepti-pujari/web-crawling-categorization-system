"""
feature_extractor.py
Fits a TF-IDF vectoriser on category keyword profiles and transforms page text.
"""

import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import spmatrix

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Builds and caches TF-IDF representations for both category profiles
    and incoming page text.

    The vectoriser is fitted once on the category keyword corpus so that
    the same vocabulary is used for both profiles and new pages —
    ensuring meaningful cosine similarity comparisons.
    """

    def __init__(self, max_features: int = 8000, ngram_range: tuple = (1, 2)):
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True,        # Apply log(1 + tf) to dampen high-freq terms
            strip_accents="unicode",
            analyzer="word",
            min_df=1,
        )
        self._fitted = False
        self._category_vectors: spmatrix | None = None
        self._category_names: list[str] = []

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit_categories(self, categories: list[dict]):
        """
        Fit the vectoriser on the category keyword corpus.
        Must be called before any call to transform() or category_vectors.

        Each category dict must have at least:
          { "name": str, "keywords": list[str] }
        """
        self._category_names = [cat["name"] for cat in categories]
        category_docs = [" ".join(cat["keywords"]) for cat in categories]

        self._vectorizer.fit(category_docs)
        self._category_vectors = self._vectorizer.transform(category_docs)
        self._fitted = True

        logger.info(
            "FeatureExtractor fitted on %d categories, vocabulary size: %d",
            len(categories),
            len(self._vectorizer.vocabulary_),
        )

    # ------------------------------------------------------------------
    # Transforming
    # ------------------------------------------------------------------

    def transform(self, text: str) -> spmatrix:
        """
        Transform a single text string into a TF-IDF vector.
        Requires fit_categories() to have been called first.
        """
        self._assert_fitted()
        return self._vectorizer.transform([text])

    def transform_batch(self, texts: list[str]) -> spmatrix:
        """Transform a list of text strings into a TF-IDF matrix."""
        self._assert_fitted()
        return self._vectorizer.transform(texts)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def category_vectors(self) -> spmatrix:
        self._assert_fitted()
        return self._category_vectors

    @property
    def category_names(self) -> list[str]:
        return self._category_names

    @property
    def vocabulary_size(self) -> int:
        self._assert_fitted()
        return len(self._vectorizer.vocabulary_)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _assert_fitted(self):
        if not self._fitted:
            raise RuntimeError(
                "FeatureExtractor has not been fitted. "
                "Call fit_categories(categories) first."
            )
