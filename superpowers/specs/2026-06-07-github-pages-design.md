# GitHub Pages Web + Discord Notification — Design Spec

Date: 2026-06-07

## Overview

Extend the weekly AI digest pipeline to publish a styled static web page on GitHub Pages (newspaper style) and replace the full Discord digest with a short link notification. An archive of all past digests is accessible on the site.

## Architecture

No changes to fetching or summarisation. A new `publisher.py` module wraps the existing text digest in HTML after Claude generates it. The workflow then commits and pushes the generated HTML before sending the Discord notification.

```
fetch → summarise (Claude) → publish HTML → git commit/push → Discord link
```

## Components

### `src/publisher.py` (new)

- Takes the text digest string and a date string as input.
- Generates two files:
  - `docs/index.html` — latest digest, always overwritten.
  - `docs/digests/YYYY-MM-DD.html` — archival copy for this week.
- Reads existing `docs/index.html` to extract previous archive links, then appends the new entry to the archive list in the new `index.html`.
- HTML style: newspaper layout (option C from mockup) — serif font, prominent headline article, short sidebar list, warm off-white background (`#fafaf9`), stone colour palette.
- No external CSS frameworks or JS — pure static HTML, self-contained per file.

### `src/notifier.py` (modified)

- `send_digest(digest)` replaced by `send_notification(url)`.
- Sends a single Discord embed: title `🗞️ Nový týdenní AI digest` + description with the GitHub Pages URL.
- Removes all chunking logic (no longer needed).

### `src/main.py` (modified)

- After `summarise()`, calls `publisher.publish(digest, date)` to write HTML files.
- Then calls `notifier.send_notification(url)` with the GitHub Pages URL.

### `.github/workflows/daily-digest.yml` (modified)

- After running `python src/main.py`, adds a step that commits and pushes `docs/` changes:
  ```yaml
  - name: Publish to GitHub Pages
    run: |
      git config user.name "github-actions[bot]"
      git config user.email "github-actions[bot]@users.noreply.github.com"
      git add docs/
      git diff --cached --quiet || git commit -m "digest: $(date +%Y-%m-%d)"
      git push
  ```
- Requires `contents: write` permission on the job.

## GitHub Pages Setup

- Source: `docs/` folder on `main` branch.
- Must be enabled manually once in repo Settings → Pages → Source: Deploy from branch → `main` / `docs`.
- Public URL: `https://danektran.github.io/ai-news-digest`

## Archive

- `docs/index.html` always shows the latest digest and a footer archive list.
- `docs/digests/` holds one file per week: `2026-06-07.html`, `2026-06-14.html`, etc.
- Archive links are extracted from the existing `index.html` on each run so no separate state file is needed.

## Error Handling

- If `docs/index.html` does not exist yet (first run), archive list starts empty.
- If the git push fails, the workflow fails — no silent data loss.
- Discord notification is sent only after a successful publish and push.

## Out of Scope

- Search functionality.
- RSS feed for the web.
- Authentication or private access.
