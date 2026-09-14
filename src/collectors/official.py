from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.collectors.base import Collector
from src.collectors.http import HttpClient
from src.models import Document, ProductConfig, now_iso, today_iso
from src.utils import compact_text, parse_date, text_from_html


class OfficialSiteCollector(Collector):
    source_type = "official_site"

    def __init__(self, max_pages_per_product: int = 1) -> None:
        self.http = HttpClient()
        self.max_pages_per_product = max_pages_per_product

    def collect(self, product: ProductConfig, start_date: str, end_date: str) -> list[Document]:
        docs: list[Document] = []
        visited: set[str] = set()
        queue = list(product.official_urls)
        allowed_hosts = {urlparse(url).netloc for url in product.official_urls}
        while queue and len(visited) < self.max_pages_per_product:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            resp = self.http.get(url)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            title = (soup.title.get_text(" ", strip=True) if soup.title else url).strip()
            body = compact_text(text_from_html(resp.text), 2400)
            published = None
            for selector in ["time", "[datetime]", "[date]"]:
                tag = soup.select_one(selector)
                if tag:
                    published = parse_date(tag.get("datetime") or tag.get_text(" ", strip=True))
                    if published:
                        break
            if not published:
                published = parse_date(body)
            docs.append(
                Document(
                    title=title,
                    url=url,
                    source_name=urlparse(url).netloc,
                    source_type=self.source_type,
                    published_at=published,
                    first_seen_at=today_iso(),
                    collected_at=now_iso(),
                    company=product.company,
                    brand=product.brand,
                    product=product.product,
                    age_segment=product.age_segment,
                    body=body,
                    snippet=body[:300],
                )
            )
            for a in soup.select("a[href]"):
                href = urljoin(url, a["href"])
                parsed = urlparse(href)
                if parsed.netloc not in allowed_hosts:
                    continue
                label = a.get_text(" ", strip=True)
                haystack = f"{href} {label}"
                if any(k in haystack for k in ["news", "campaign", "cm", "movie", "release", "イベント", "キャンペーン", "お知らせ"]):
                    clean = re.sub(r"#.*$", "", href)
                    if clean not in visited and clean not in queue:
                        queue.append(clean)
        return docs



