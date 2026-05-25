"""tests/test_url_queue.py"""
import os
import json
import tempfile
import pytest
from src.crawler.url_queue import UrlQueue, is_valid_url, normalise_url


# ------------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------------

def test_valid_http_url():
    assert is_valid_url("http://example.com") is True

def test_valid_https_url():
    assert is_valid_url("https://github.com/deepti") is True

def test_invalid_no_scheme():
    assert is_valid_url("github.com") is False

def test_invalid_ftp():
    assert is_valid_url("ftp://files.example.com") is False

def test_invalid_empty():
    assert is_valid_url("") is False

def test_normalise_strips_trailing_slash():
    assert normalise_url("https://example.com/") == "https://example.com"

def test_normalise_strips_whitespace():
    assert normalise_url("  https://example.com  ") == "https://example.com"


# ------------------------------------------------------------------
# UrlQueue
# ------------------------------------------------------------------

def test_load_from_file_counts(tmp_path):
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "https://github.com\n"
        "https://stackoverflow.com\n"
        "# comment line\n"
        "\n"
        "not-a-url\n"
    )
    q = UrlQueue()
    added = q.load_from_file(str(url_file))
    assert added == 2
    assert q.pending_count == 2

def test_deduplication(tmp_path):
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "https://github.com\n"
        "https://github.com\n"
        "https://github.com/\n"   # normalises to same URL
    )
    q = UrlQueue()
    added = q.load_from_file(str(url_file))
    assert added == 1

def test_pop_batch():
    q = UrlQueue()
    q.load_from_list(["https://a.com", "https://b.com", "https://c.com"])
    batch = q.pop_batch(2)
    assert len(batch) == 2
    assert q.pending_count == 1

def test_mark_completed_and_failed():
    q = UrlQueue()
    q.load_from_list(["https://a.com", "https://b.com"])
    q.mark_completed("https://a.com")
    q.mark_failed("https://b.com")
    assert q.completed_count == 1
    assert q.failed_count == 1

def test_checkpoint_roundtrip(tmp_path):
    ckpt = str(tmp_path / "ckpt.json")
    q1 = UrlQueue(checkpoint_path=ckpt)
    q1.load_from_list(["https://a.com", "https://b.com"])
    q1.pop_batch(1)
    q1.mark_completed("https://a.com")
    q1.save_checkpoint()

    q2 = UrlQueue(checkpoint_path=ckpt)
    assert q2.pending_count == 1
    assert q2.completed_count == 1
