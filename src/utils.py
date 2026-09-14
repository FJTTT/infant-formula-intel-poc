from __future__ import annotations

import hashlib
import re
from datetime import datetime
from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse, urlunparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


def normalize_url(url: str) -> str:
    url = unescape(url).strip()
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        qs = parse_qs(parsed.query)
        if qs.get("q"):
            return normalize_url(qs["q"][0])
    query_parts = []
    for part in parsed.query.split("&"):
        if not part:
            continue
        key = part.split("=", 1)[0].lower()
        if key.startswith("utm_") or key in {"fbclid", "gclid", "yclid"}:
            continue
        query_parts.append(part)
    clean = parsed._replace(
        scheme=parsed.scheme.lower() or "https",
        netloc=parsed.netloc.lower(),
        fragment="",
        query="&".join(query_parts),
    )
    path = re.sub(r"/+$", "", clean.path) or "/"
    clean = clean._replace(path=path)
    return urlunparse(clean)


def content_hash(*parts: str) -> str:
    normalized = " ".join(parts).lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()


def text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(value, fuzzy=True)
        return dt.date().isoformat()
    except (ValueError, OverflowError, TypeError):
        match = re.search(r"(20\d{2})[./年-]\s*(\d{1,2})[./月-]\s*(\d{1,2})", value)
        if match:
            y, m, d = map(int, match.groups())
            return f"{y:04d}-{m:02d}-{d:02d}"
    return None


def date_in_window(value: str | None, start: str, end: str) -> bool:
    if not value:
        return True
    return start <= value <= end


def ddg_url(query: str) -> str:
    return f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"


def compact_text(text: str, limit: int = 1200) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:limit]

