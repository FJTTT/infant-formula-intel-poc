from __future__ import annotations

from src.collectors.search import SearchCollector
from src.models import Document, ProductConfig


class YouTubeCollector(SearchCollector):
    source_type = "youtube"

    def collect(self, product: ProductConfig, start_date: str, end_date: str) -> list[Document]:
        original_terms = self.query_terms
        self.query_terms = ["site:youtube.com/watch 公式", "site:youtube.com/watch CM", "site:youtube.com/watch 動画"]
        docs = super().collect(product, start_date, end_date)
        self.query_terms = original_terms
        for doc in docs:
            doc.source_type = self.source_type
            doc.source_name = "YouTube via Web Search"
        return docs

