from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.collectors.base import Collector
from src.collectors.http import HttpClient
from src.models import Document, ProductConfig, now_iso, today_iso
from src.utils import compact_text, parse_date, text_from_html


LP_KEYWORDS = ["campaign", "cmp", "lp", "present", "event", "movie", "cm", "キャンペーン", "応募", "プレゼント", "動画"]
BANNER_KEYWORDS = ["banner", "bnr", "main", "kv", "hero", "campaign", "cmp", "visual", "mv"]
LOW_VALUE_IMAGE_HINTS = ["icon", "logo", "menu", "arrow", "close", "search", "external", "plus", "minus", ".svg"]


class OfficialSiteCollector(Collector):
    source_type = "official_site"

    def __init__(self, max_pages_per_product: int = 3) -> None:
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
            visual_assets = extract_visual_assets(soup, url)
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
                    metadata={"visual_assets": visual_assets, "visual_asset_count": len(visual_assets)},
                )
            )
            for a in soup.select("a[href]"):
                href = urljoin(url, a["href"])
                parsed = urlparse(href)
                if parsed.netloc not in allowed_hosts:
                    continue
                label = a.get_text(" ", strip=True)
                haystack = f"{href} {label}"
                if is_lp_candidate(haystack):
                    clean = re.sub(r"#.*$", "", href)
                    if clean not in visited and clean not in queue:
                        queue.append(clean)
        return docs


def is_lp_candidate(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in LP_KEYWORDS)


def image_confidence(asset_url: str, alt_text: str, width: int | None, height: int | None) -> float:
    haystack = f"{asset_url} {alt_text}".lower()
    score = 0.45
    if any(k in haystack for k in BANNER_KEYWORDS):
        score += 0.25
    if width and height and width >= 500 and height >= 150:
        score += 0.2
    if alt_text:
        score += 0.05
    return min(score, 0.95)


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def extract_visual_assets(soup: BeautifulSoup, page_url: str) -> list[dict]:
    assets: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(asset_type: str, asset_url: str, alt_text: str = "", creative_text: str = "", width: int | None = None, height: int | None = None, lp: bool = False, confidence: float | None = None) -> None:
        absolute = urljoin(page_url, asset_url)
        if not absolute.startswith("http"):
            return
        key = (asset_type, absolute)
        if key in seen:
            return
        seen.add(key)
        assets.append(
            {
                "asset_type": asset_type,
                "asset_url": absolute,
                "alt_text": compact_text(alt_text, 240),
                "creative_text": compact_text(creative_text, 300),
                "width": width,
                "height": height,
                "is_landing_page_candidate": lp,
                "confidence": confidence if confidence is not None else image_confidence(absolute, alt_text, width, height),
                "metadata": {"page_url": page_url},
            }
        )

    for prop in ["og:image", "twitter:image"]:
        tag = soup.select_one(f'meta[property="{prop}"], meta[name="{prop}"]')
        if tag and tag.get("content"):
            add(prop.replace(":", "_"), tag["content"], creative_text="OG/Twitter preview image", confidence=0.85)

    for img in soup.select("img[src], source[srcset]")[:80]:
        src = img.get("src") or (img.get("srcset", "").split(",")[0].split(" ")[0])
        if not src:
            continue
        alt = img.get("alt") or img.get("aria-label") or ""
        width = parse_int(img.get("width"))
        height = parse_int(img.get("height"))
        asset_type = "banner_image" if image_confidence(src, alt, width, height) >= 0.7 else "page_image"
        add(asset_type, src, alt_text=alt, width=width, height=height)

    for a in soup.select("a[href]"):
        href = urljoin(page_url, a["href"])
        label = a.get_text(" ", strip=True)
        if is_lp_candidate(f"{href} {label}"):
            add("landing_page", href, creative_text=label, lp=True, confidence=0.75)

    return assets


