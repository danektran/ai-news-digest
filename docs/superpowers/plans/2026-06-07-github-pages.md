# GitHub Pages Web + Discord Notification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the weekly AI digest as a styled static HTML page on GitHub Pages and replace the full Discord message with a short link notification.

**Architecture:** A new `publisher.py` generates a newspaper-style HTML page and an archival copy, both written to `docs/`. The GitHub Actions workflow commits and pushes `docs/` after each run. Discord receives only a short embed with the public URL.

**Tech Stack:** Python 3.11, pure HTML/CSS (no frameworks), GitHub Pages (`docs/` folder on `main`), GitHub Actions, pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/publisher.py` | Convert text digest → HTML, write `docs/index.html` + `docs/digests/YYYY-MM-DD.html` |
| Create | `tests/test_publisher.py` | Unit tests for publisher |
| Modify | `src/notifier.py` | Replace `send_digest` with `send_notification(url)` |
| Modify | `tests/test_notifier.py` | Tests for updated notifier (create if missing) |
| Modify | `src/main.py` | Call publisher, pass URL to notifier |
| Modify | `.github/workflows/daily-digest.yml` | Add `contents: write` permission + git commit/push step |
| Create | `docs/.gitkeep` | Ensure `docs/` exists in repo before first run |

---

### Task 1: Add pytest to requirements and create docs/.gitkeep

**Files:**
- Modify: `requirements.txt`
- Create: `docs/.gitkeep`

- [ ] **Step 1: Add pytest to requirements.txt**

Open `requirements.txt` and add `pytest` at the end:

```
anthropic
feedparser
requests
pyyaml
python-dateutil
pytest
```

- [ ] **Step 2: Create docs/.gitkeep**

Create an empty file `docs/.gitkeep` so the `docs/` directory is tracked by git before the first workflow run.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt docs/.gitkeep
git commit -m "chore: add pytest, create docs dir"
git push
```

---

### Task 2: Implement publisher.py

**Files:**
- Create: `src/publisher.py`
- Create: `tests/test_publisher.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_publisher.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:\Users\trani\ai-news-digest
pip install pytest -q
pytest tests/test_publisher.py -v
```

Expected: `ImportError` or `ModuleNotFoundError: No module named 'publisher'`

- [ ] **Step 3: Implement src/publisher.py**

Create `src/publisher.py`:

```python
"""Converts text digest to newspaper-style HTML and writes to docs/."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

GITHUB_PAGES_URL = "https://danektran.github.io/ai-news-digest"

_CSS = """
  body { margin: 0; background: #fafaf9; font-family: Georgia, 'Times New Roman', serif; color: #1c1917; }
  .page { max-width: 860px; margin: 0 auto; padding: 32px 24px; }
  .masthead { border-bottom: 3px solid #1c1917; padding-bottom: 12px; margin-bottom: 24px; }
  .masthead-label { font-size: 11px; letter-spacing: 3px; color: #78716c; text-transform: uppercase; margin-bottom: 4px; }
  .masthead-title { font-size: 32px; font-weight: 900; margin: 0 0 4px; }
  .masthead-date { font-size: 12px; color: #78716c; }
  .layout { display: flex; gap: 32px; }
  .main-col { flex: 2; }
  .side-col { flex: 1; border-left: 1px solid #e7e5e4; padding-left: 24px; }
  h2 { font-size: 13px; letter-spacing: 2px; text-transform: uppercase; color: #78716c; border-bottom: 1px solid #e7e5e4; padding-bottom: 4px; margin: 20px 0 10px; }
  p { font-size: 15px; line-height: 1.7; margin: 0 0 12px; }
  a { color: #1c1917; }
  .archive { margin-top: 40px; border-top: 2px solid #1c1917; padding-top: 12px; }
  .archive h2 { margin-top: 0; }
  .archive ul { list-style: none; padding: 0; margin: 0; }
  .archive li { font-size: 13px; padding: 4px 0; border-bottom: 1px solid #e7e5e4; }
  @media (max-width: 600px) { .layout { flex-direction: column; } .side-col { border-left: none; padding-left: 0; border-top: 1px solid #e7e5e4; padding-top: 16px; } }
"""


def _digest_to_html_body(digest: str) -> str:
    """Convert markdown-like digest text to HTML paragraphs and headings."""
    lines = digest.splitlines()
    html_lines: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("**") and "**" in line[2:]:
            # Bold lead: **Title** — rest of text. [Odkaz](url)
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', line)
            html_lines.append(f"<p>{line}</p>")
        else:
            line = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', line)
            html_lines.append(f"<p>{line}</p>")
    return "\n".join(html_lines)


def _extract_archive_links(index_html: str) -> list[tuple[str, str]]:
    """Extract existing archive entries from index.html as (date_str, href) pairs."""
    pattern = r'<a href="(digests/(\d{4}-\d{2}-\d{2})\.html)">'
    return [(m.group(2), m.group(1)) for m in re.finditer(pattern, index_html)]


def _render_page(title: str, date_str: str, body_html: str, archive_links: list[tuple[str, str]]) -> str:
    archive_items = "".join(
        f'<li><a href="{href}">{ds}</a></li>' for ds, href in sorted(archive_links, reverse=True)
    )
    archive_section = f"""
    <div class="archive">
      <h2>Archiv</h2>
      <ul>{archive_items}</ul>
    </div>""" if archive_items else ""

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="page">
    <div class="masthead">
      <div class="masthead-label">Týdenní přehled umělé inteligence</div>
      <div class="masthead-title">AI Digest</div>
      <div class="masthead-date">{date_str}</div>
    </div>
    <div class="layout">
      <div class="main-col">
        {body_html}
      </div>
    </div>
    {archive_section}
  </div>
</body>
</html>"""


def publish(digest: str, digest_date: date, docs_dir: Path | None = None) -> str:
    """Write digest HTML to docs/ and return the public GitHub Pages URL.

    Args:
        digest: Plain text digest from summariser.
        digest_date: The date of this digest.
        docs_dir: Override for the docs directory (used in tests).

    Returns:
        Public GitHub Pages URL string.
    """
    if docs_dir is None:
        docs_dir = Path(__file__).parent.parent / "docs"

    docs_dir = Path(docs_dir)
    digests_dir = docs_dir / "digests"
    digests_dir.mkdir(parents=True, exist_ok=True)

    date_str = digest_date.strftime("%d. %m. %Y")
    date_slug = digest_date.strftime("%Y-%m-%d")
    title = f"AI Digest — {date_str}"
    body_html = _digest_to_html_body(digest)

    # Read existing archive links from current index.html
    index_path = docs_dir / "index.html"
    existing_links: list[tuple[str, str]] = []
    if index_path.exists():
        existing_links = _extract_archive_links(index_path.read_text(encoding="utf-8"))

    # Write archival copy
    archive_path = digests_dir / f"{date_slug}.html"
    archive_html = _render_page(title, date_str, body_html, [])
    archive_path.write_text(archive_html, encoding="utf-8")

    # Add this week to archive list for the index
    archive_links = [(date_slug, f"digests/{date_slug}.html")] + [
        (ds, href) for ds, href in existing_links if ds != date_slug
    ]

    # Write index.html (latest + full archive)
    index_html = _render_page(title, date_str, body_html, archive_links)
    index_path.write_text(index_html, encoding="utf-8")

    return GITHUB_PAGES_URL
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_publisher.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/publisher.py tests/test_publisher.py
git commit -m "feat: add HTML publisher for GitHub Pages"
git push
```

---

### Task 3: Update notifier.py to send a link instead of full digest

**Files:**
- Modify: `src/notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_notifier.py`:

```python
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from notifier import send_notification


def test_send_notification_posts_embed(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("notifier.requests.post", return_value=mock_response) as mock_post:
        send_notification("https://danektran.github.io/ai-news-digest")

    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert "embeds" in payload
    assert "https://danektran.github.io/ai-news-digest" in payload["embeds"][0]["description"]


def test_send_notification_raises_without_webhook(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    with pytest.raises(EnvironmentError, match="DISCORD_WEBHOOK_URL"):
        send_notification("https://danektran.github.io/ai-news-digest")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_notifier.py -v
```

Expected: `ImportError: cannot import name 'send_notification' from 'notifier'`

- [ ] **Step 3: Replace send_digest with send_notification in notifier.py**

Replace the entire content of `src/notifier.py` with:

```python
"""Sends a link notification to Discord via webhook."""

from __future__ import annotations

import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)


def send_notification(url: str) -> None:
    """Post a short Discord embed with the link to the published digest.

    Args:
        url: Public URL of the published digest page.

    Raises:
        EnvironmentError: If DISCORD_WEBHOOK_URL is not set.
        requests.HTTPError: If Discord returns a non-2xx status.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set")

    today_str = date.today().strftime("%d. %m. %Y")
    payload = {
        "embeds": [
            {
                "title": f"🗞️ Nový týdenní AI digest — {today_str}",
                "description": f"Tento týden v umělé inteligenci je online:\n{url}",
                "color": 0x5865F2,
            }
        ]
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
    logger.info("Discord notification sent.")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_notifier.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/notifier.py tests/test_notifier.py
git commit -m "feat: replace full Discord digest with link notification"
git push
```

---

### Task 4: Wire publisher and updated notifier into main.py

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Update main.py**

Replace the content of `src/main.py` with:

```python
"""Entry point — orchestrates fetching, summarising, publishing, and notifying."""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from fetcher import fetch_all_articles
from summarizer import summarise
from publisher import publish
from notifier import send_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    logger.info("=== AI News Digest starting ===")

    try:
        config = load_config()
    except Exception as exc:
        logger.error("Failed to load config.yaml: %s", exc)
        sys.exit(1)

    feeds = config.get("feeds", [])
    lookback_hours = int(config.get("lookback_hours", 168))
    max_per_feed = int(config.get("max_articles_per_feed", 5))

    if not feeds:
        logger.error("No feeds configured in config.yaml")
        sys.exit(1)

    logger.info("Fetching articles from %d feed(s)…", len(feeds))
    try:
        articles = fetch_all_articles(feeds, lookback_hours, max_per_feed)
    except Exception as exc:
        logger.error("Unexpected error during fetching: %s", exc)
        sys.exit(1)

    logger.info("Fetched %d article(s) in total.", len(articles))

    logger.info("Summarising articles…")
    try:
        digest = summarise(articles)
    except Exception as exc:
        logger.error("Failed to generate digest: %s", exc)
        sys.exit(1)

    logger.info("Publishing to GitHub Pages…")
    try:
        url = publish(digest, date.today())
    except Exception as exc:
        logger.error("Failed to publish digest: %s", exc)
        sys.exit(1)

    logger.info("Sending Discord notification…")
    try:
        send_notification(url)
    except Exception as exc:
        logger.error("Failed to send notification: %s", exc)
        sys.exit(1)

    logger.info("=== AI News Digest completed successfully ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests to verify nothing is broken**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: wire publisher and link notifier into main pipeline"
git push
```

---

### Task 5: Update GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/daily-digest.yml`

- [ ] **Step 1: Update the workflow file**

Replace the content of `.github/workflows/daily-digest.yml` with:

```yaml
name: Weekly AI Digest

on:
  schedule:
    - cron: '0 6 * * 1'   # every Monday at 06:00 UTC (08:00 CEST / 07:00 CET)
  workflow_dispatch:        # allow manual runs from the GitHub UI

permissions:
  contents: write

jobs:
  digest:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run digest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: python src/main.py

      - name: Publish to GitHub Pages
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git diff --cached --quiet || git commit -m "digest: $(date +%Y-%m-%d)"
          git push
```

- [ ] **Step 2: Commit and push**

```bash
git add .github/workflows/daily-digest.yml
git commit -m "ci: add GitHub Pages publish step with contents:write permission"
git push
```

---

### Task 6: Enable GitHub Pages and test manually

- [ ] **Step 1: Enable GitHub Pages**

Go to: `https://github.com/danektran/ai-news-digest/settings/pages`

Set:
- **Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/docs`

Click **Save**.

- [ ] **Step 2: Trigger manual workflow run**

Go to: `https://github.com/danektran/ai-news-digest/actions`

Click **Weekly AI Digest** → **Run workflow** → **Run workflow**.

- [ ] **Step 3: Verify**

After the workflow completes:
- Check `https://danektran.github.io/ai-news-digest` loads the digest page.
- Check Discord received a short embed with the link (not the full text).
- Check `https://github.com/danektran/ai-news-digest/tree/main/docs` shows `index.html` and `digests/YYYY-MM-DD.html`.
