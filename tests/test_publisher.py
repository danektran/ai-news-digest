import os
import re
from pathlib import Path
from datetime import date
import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from publisher import publish

SAMPLE_DIGEST = """## Modely a výzkum

**GPT-5 spuštěn** — OpenAI představil nejambicióznější model. [Odkaz](https://openai.com/blog/gpt5)

**Claude 4 vydán** — Anthropic přináší rozšířený kontext. [Odkaz](https://anthropic.com/blog/claude4)

## Produkty a launches

**Gemini Ultra 2** — Google DeepMind vydal novou verzi. [Odkaz](https://deepmind.google)

Celkem 3 články tento týden.
"""


def test_publish_creates_index_html(tmp_path):
    publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    assert (tmp_path / "index.html").exists()


def test_publish_creates_archive_file(tmp_path):
    publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    assert (tmp_path / "digests" / "2026-06-07.html").exists()


def test_index_html_contains_digest_content(tmp_path):
    publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    content = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "GPT-5 spuštěn" in content
    assert "Claude 4 vydán" in content


def test_index_html_contains_archive_link_after_second_run(tmp_path):
    publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    publish(SAMPLE_DIGEST, date(2026, 6, 14), docs_dir=tmp_path)
    content = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2026-06-07" in content  # previous week appears as archive link


def test_archive_file_contains_digest_content(tmp_path):
    publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    content = (tmp_path / "digests" / "2026-06-07.html").read_text(encoding="utf-8")
    assert "GPT-5 spuštěn" in content


def test_publish_returns_github_pages_url(tmp_path):
    url = publish(SAMPLE_DIGEST, date(2026, 6, 7), docs_dir=tmp_path)
    assert url == "https://danektran.github.io/ai-news-digest"
