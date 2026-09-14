from __future__ import annotations

from urllib.parse import quote_plus

import feedparser

from src.collectors.base import Collector
from src.collectors.http import HttpClient
from src.config import load_query_terms
from src.models import Document, ProductConfig, now_iso, today_iso
from src.utils import compact_text, parse_date


class NewsCollector(Collector):
    source_type = "news_pr"

    def __init__(self, max_entries_per_query: int = 4) -> None:
        self.http = HttpClient()
        self.query_terms = load_query_terms()
        self.max_entries_per_query = max_entries_per_query

    def collect(self, product: ProductConfig, start_date: str, end_date: str) -> list[Document]:
        docs: list[Document] = []
        seen: set[str] = set()
        for alias in product.aliases[:1]:
            queries = [
                f'"{alias}" after:{start_date} before:{end_date}',
                f'"{alias}" PR TIMES after:{start_date} before:{end_date}',
            ]
            for query in queries:
                url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"
                resp = self.http.get(url)
                if not resp:
                    continue
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[: self.max_entries_per_query]:
                    link = entry.get("link", "")
                    if not link or link in seen:
                        continue
                    seen.add(link)
                    docs.append(
                        Document(
                            title=entry.get("title", "(no title)"),
                            url=link,
                            source_name=entry.get("source", {}).get("title", "Google News RSS"),
                            source_type=self.source_type,
                            published_at=parse_date(entry.get("published")),
                            first_seen_at=today_iso(),
                            collected_at=now_iso(),
                            company=product.company,
                            brand=product.brand,
                            product=product.product,
                            age_segment=product.age_segment,
                            snippet=compact_text(entry.get("summary", "")),
                            metadata={"query": query},
                        )
                    )
        return docs
