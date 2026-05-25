"""
crawler.py
Core crawling logic: concurrent HTTP fetching with retries and politeness delays.
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .content_extractor import ContentExtractor

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "ResearchCrawler/1.0 "
        "(Web Categorization Study; github.com/deepti-pujari/web-crawling-categorization-system)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class WebCrawler:
    """
    Concurrent web crawler.

    Args:
        workers:  Number of parallel threads.
        delay:    Politeness delay (seconds) between successive requests per thread.
        timeout:  Per-request timeout in seconds.
    """

    def __init__(self, workers: int = 10, delay: float = 0.5, timeout: int = 10):
        self.workers = workers
        self.delay = delay
        self.timeout = timeout
        self.extractor = ContentExtractor()
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def crawl_batch(self, urls: list[str]) -> list[dict]:
        """
        Crawl a list of URLs concurrently.
        Returns a list of result dicts (one per URL, including failures).
        """
        results = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_url = {executor.submit(self._crawl_one, url): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                except Exception as exc:
                    logger.error("Unexpected error crawling %s: %s", url, exc)
                    result = self._error_result(url, str(exc))
                results.append(result)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _crawl_one(self, url: str) -> dict:
        """Fetch a single URL, extract content, and return a result dict."""
        time.sleep(self.delay)
        crawled_at = datetime.now(timezone.utc).isoformat()

        try:
            response = self._session.get(url, timeout=self.timeout, headers=_HEADERS)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                logger.debug("Skipping non-HTML content at %s (%s)", url, content_type)
                return self._error_result(url, f"Non-HTML content-type: {content_type}", crawled_at)

            extracted = self.extractor.extract(response.text, url)

            logger.debug("OK  %s  [%d]", url, response.status_code)
            return {
                "url":           url,
                "final_url":     response.url,
                "status":        "SUCCESS",
                "http_code":     response.status_code,
                "crawled_at":    crawled_at,
                **extracted,
            }

        except requests.exceptions.Timeout:
            logger.warning("TIMEOUT  %s", url)
            return self._error_result(url, "Timeout", crawled_at)
        except requests.exceptions.TooManyRedirects:
            logger.warning("TOO_MANY_REDIRECTS  %s", url)
            return self._error_result(url, "Too many redirects", crawled_at)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("CONNECTION_ERROR  %s  %s", url, exc)
            return self._error_result(url, f"Connection error: {exc}", crawled_at)
        except requests.exceptions.HTTPError as exc:
            logger.warning("HTTP_ERROR  %s  %s", url, exc)
            return self._error_result(url, f"HTTP {exc.response.status_code}", crawled_at)
        except Exception as exc:
            logger.error("UNKNOWN_ERROR  %s  %s", url, exc)
            return self._error_result(url, str(exc), crawled_at)

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @staticmethod
    def _error_result(url: str, error: str, crawled_at: str = "") -> dict:
        return {
            "url":           url,
            "final_url":     url,
            "status":        "ERROR",
            "http_code":     None,
            "crawled_at":    crawled_at or datetime.now(timezone.utc).isoformat(),
            "error":         error,
            "title":         "",
            "description":   "",
            "keywords":      "",
            "h1":            "",
            "h2":            "",
            "h3":            "",
            "body_text":     "",
            "combined_text": "",
        }
