from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


EVENT_TYPES = [
    "PRODUCT_LAUNCH",
    "PRODUCT_RENEWAL",
    "CAMPAIGN_LAUNCH",
    "ADVERTISING",
    "CREATIVE_CHANGE",
    "PR_ACTIVITY",
    "EVENT",
    "SAMPLING",
    "RETAIL_PROMOTION",
    "COLLABORATION",
    "TALENT_INFLUENCER",
    "CONTENT",
    "CORPORATE_NEWS",
    "OTHER",
]


@dataclass(frozen=True)
class ProductConfig:
    company: str
    brand: str
    product: str
    age_segment: str
    role: str
    aliases: list[str]
    official_urls: list[str] = field(default_factory=list)


@dataclass
class Document:
    title: str
    url: str
    source_name: str
    source_type: str
    published_at: str | None
    first_seen_at: str
    collected_at: str
    company: str
    brand: str
    product: str
    age_segment: str
    body: str = ""
    snippet: str = ""
    normalized_url: str = ""
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    id: int | None = None


@dataclass
class Event:
    company: str
    brand: str
    product: str
    age_segment: str
    event_type: str
    event_date: str | None
    campaign_name: str | None
    summary: str
    target: str | None
    message: str | None
    talent: str | None
    channel: str | None
    marketing_intent: str | None
    importance: int
    confidence: float
    fact_json: str
    inference_json: str
    source_documents: list[int]
    campaign_key: str | None = None
    id: int | None = None


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()

