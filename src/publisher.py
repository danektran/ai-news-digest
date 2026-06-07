"""Converts text digest to newspaper-style HTML and writes to docs/."""

from __future__ import annotations

import html
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
  h2 { font-size: 13px; letter-spacing: 2px; text-transform: uppercase; color: #78716c; border-bottom: 1px solid #e7e5e4; padding-bottom: 4px; margin: 20px 0 10px; }
  p { font-size: 15px; line-height: 1.7; margin: 0 0 12px; }
  a { color: #1c1917; }
  .archive { margin-top: 40px; border-top: 2px solid #1c1917; padding-top: 12px; }
  .archive h2 { margin-top: 0; }
  .archive ul { list-style: none; padding: 0; margin: 0; }
  .archive li { font-size: 13px; padding: 4px 0; border-bottom: 1px solid #e7e5e4; }
"""


def _digest_to_html_body(digest: str) -> str:
    """Convert markdown-like digest text to HTML paragraphs and headings."""
    lines = digest.splitlines()
    html_lines: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line = html.escape(line)
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
