# AI News Digest

Runs every day at 07:00 UTC as a GitHub Actions job. Fetches the latest AI news from RSS feeds, summarises them in Czech using Claude (claude-haiku-4-5), and posts the digest to a Discord channel via webhook.

## What it does

1. Fetches articles published in the last 24 hours from configured RSS feeds.
2. Sends them to Claude, which groups and summarises them in Czech.
3. Posts the result to Discord — first chunk as a rich embed, the rest as plain messages.

## Setup

### 1. Fork or push this repository to GitHub

### 2. Add repository secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (https://console.anthropic.com) |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL (channel → Edit Channel → Integrations → Webhooks) |

### 3. Enable GitHub Actions

Actions are enabled by default. The workflow at `.github/workflows/daily-digest.yml` will trigger automatically at 07:00 UTC each day.

### 4. Manual test

Go to **Actions → Daily AI Digest → Run workflow** to trigger a run immediately.

## RSS sources

| Source | URL |
|---|---|
| Anthropic Blog | https://www.anthropic.com/rss.xml |
| OpenAI Blog | https://openai.com/blog/rss.xml |
| The Verge AI | https://www.theverge.com/ai-artificial-intelligence/rss/index.xml |
| VentureBeat AI | https://venturebeat.com/category/ai/feed/ |
| Ars Technica | https://feeds.arstechnica.com/arstechnica/technology-lab |
| Google DeepMind | https://deepmind.google/blog/rss.xml |
| Hugging Face | https://huggingface.co/blog/feed.xml |

Add or remove feeds by editing `config.yaml`.

## Configuration

Edit `config.yaml` to adjust:

- `feeds` — list of RSS feeds (name + url)
- `max_articles_per_feed` — how many recent articles to include per feed (default: 5)
- `lookback_hours` — how far back to look for articles (default: 24)
- `language` — output language hint (default: czech)

## Local development

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
python src/main.py
```
