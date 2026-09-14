from __future__ import annotations

from bs4 import BeautifulSoup

from src.collectors.base import Collector
from src.collectors.http import HttpClient
from src.config import load_query_terms
from src.models import Document, ProductConfig, now_iso, today_iso
from src.utils import compact_text, ddg_url, normalize_url


class SearchCollector(Collector):
    source_type = "web_search"

    def __init__(self, max_results_per_query: int = 3) -> None:
        self.http = HttpClient()
        self.query_terms = load_query_terms()
        self.max_results_per_query = max_results_per_query

    def collect(self, product: ProductConfig, start_date: str, end_date: str) -> list[Document]:
        docs: list[Document] = []
        seen: set[str] = set()
        for alias in product.aliases[:1]:
            queries = [f'"{alias}" after:{start_date} before:{end_date}']
            queries += [f'"{alias}" {term} after:{start_date} before:{end_date}' for term in self.query_terms[:2]]
            for query in queries:
                resp = self.http.get(ddg_url(query))
                if not resp:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                anchors = soup.select("a.result-link") or soup.select("a[href]")
                count = 0
                for a in anchors:
                    href = a.get("href") or ""
                    title = a.get_text(" ", strip=True)
                    if not href.startswith("http") or not title:
                        continue
                    norm = normalize_url(href)
                    if norm in seen:
                        continue
                    seen.add(norm)
                    docs.append(
                        Document(
                            title=title,
                            url=href,
                            source_name="DuckDuckGo Lite",
                            source_type=self.source_type,
                            published_at=None,
                            first_seen_at=today_iso(),
                            collected_at=now_iso(),
                            company=product.company,
                            brand=product.brand,
                            product=product.product,
                            age_segment=product.age_segment,
                            snippet=compact_text(title),
                            metadata={"query": query},
                        )
                    )
                    count += 1
                    if count >= self.max_results_per_query:
                        break
        return docs
