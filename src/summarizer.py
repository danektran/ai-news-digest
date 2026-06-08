"""Summarises AI news articles into a Czech-language digest using Claude."""

from __future__ import annotations

import logging
import os
from datetime import date

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_WORDS = 3000

_SYSTEM_PROMPT = """\
Jsi redaktor specializovaný na umělou inteligenci. Píšeš v češtině.
Dostaneš seznam článků z AI oblasti a tvým úkolem je sestavit přehledný denní souhrn.

Pravidla:
- Piš výhradně česky.
- Seskup zprávy do tematických kategorií: Modely a výzkum / Produkty a launches / Průmyslové zprávy / Ostatní.
- Každý článek shrň 2–3 větami. Piš srozumitelně a jednoduše — čtenář musí pochopit podstatu bez kliknutí na odkaz.
- Na konci každého článku přidej odkaz ve formátu [název článku](url).
- Celkový rozsah nepřesáhne {max_words} slov.
- Na závěr napiš jednu větu s celkovým počtem článků.
- Pokud nejsou žádné články, napiš pouze: "Dnes žádné novinky z oblasti AI."
"""

_USER_TEMPLATE = """\
Dnešní datum: {today}

Zde jsou dnešní AI články:

{articles}

Sestav prosím denní souhrn v češtině.
"""


def _format_articles(articles: list[dict]) -> str:
    lines: list[str] = []
    for i, article in enumerate(articles, start=1):
        lines.append(f"{i}. [{article['source_name']}] {article['title']}")
        lines.append(f"   URL: {article['url']}")
        if article.get("summary"):
            # Truncate long summaries sent to the model to keep tokens reasonable
            snippet = article["summary"][:400]
            lines.append(f"   Popis: {snippet}")
        lines.append("")
    return "\n".join(lines)


def summarise(articles: list[dict]) -> str:
    """Generate a Czech digest from a list of article dicts.

    Args:
        articles: List of article dicts (title, url, summary, source_name, published_date).

    Returns:
        Czech-language digest string.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set")

    client = anthropic.Anthropic(api_key=api_key)

    if not articles:
        return "Dnes žádné novinky z oblasti AI."

    articles_text = _format_articles(articles)
    today_str = date.today().strftime("%d. %m. %Y")

    system = _SYSTEM_PROMPT.format(max_words=MAX_WORDS)
    user = _USER_TEMPLATE.format(today=today_str, articles=articles_text)

    logger.info("Calling Claude (%s) to summarise %d articles…", MODEL, len(articles))

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error: %s", exc)
        raise

    digest = message.content[0].text
    logger.info("Digest generated (%d characters)", len(digest))
    return digest
