from __future__ import annotations

import json
import re
import sqlite3

from src.models import Event
from src.utils import content_hash, parse_date


KEYWORDS = [
    ("リニューアル|刷新|パッケージ", "PRODUCT_RENEWAL", 4),
    ("新発売|発売|新商品", "PRODUCT_LAUNCH", 4),
    ("キャンペーン|プレゼント|応募", "CAMPAIGN_LAUNCH", 4),
    ("CM|広告|動画|YouTube|ムービー", "ADVERTISING", 3),
    ("サンプリング|試供品|店頭", "SAMPLING", 3),
    ("イベント|セミナー|フェア", "EVENT", 3),
    ("コラボ|共同", "COLLABORATION", 3),
    ("タレント|俳優|起用|インフルエンサー", "TALENT_INFLUENCER", 3),
    ("ニュースリリース|PR TIMES|発表", "PR_ACTIVITY", 2),
]


def classify_document(row: sqlite3.Row) -> Event:
    text = " ".join([row["title"] or "", row["snippet"] or "", row["body"] or ""])
    event_type = "OTHER"
    importance = 1
    confidence = 0.45
    for pattern, candidate, score in KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            event_type = candidate
            importance = score
            confidence = 0.72 if candidate != "OTHER" else 0.45
            break
    event_date = row["published_at"] or parse_date(text)
    campaign_name = extract_campaign_name(text)
    channel = infer_channel(row["source_type"], text)
    fact = {
        "title": row["title"],
        "url": row["url"],
        "source_type": row["source_type"],
        "published_at": row["published_at"],
        "matched_text": text[:500],
    }
    inference = {
        "method": "heuristic_keyword_classifier",
        "event_type_reason": f"Matched keywords for {event_type}" if event_type != "OTHER" else "No strong keyword match",
        "marketing_intent_note": "Inference, not a verified fact.",
    }
    summary = summarize(row["title"], text)
    intent = infer_marketing_intent(event_type, text)
    key_base = campaign_name or re.sub(r"\s+", " ", row["title"])[:60]
    campaign_key = content_hash(row["product"], event_type, key_base)[:16]
    return Event(
        company=row["company"],
        brand=row["brand"],
        product=row["product"],
        age_segment=row["age_segment"],
        event_type=event_type,
        event_date=event_date,
        campaign_name=campaign_name,
        summary=summary,
        target=infer_target(text),
        message=extract_message(text),
        talent=extract_talent(text),
        channel=channel,
        marketing_intent=intent,
        importance=importance,
        confidence=confidence,
        fact_json=json.dumps(fact, ensure_ascii=False),
        inference_json=json.dumps(inference, ensure_ascii=False),
        source_documents=[row["id"]],
        campaign_key=campaign_key,
    )


def extract_events(conn: sqlite3.Connection) -> int:
    rows = conn.execute("select * from documents order by published_at, id").fetchall()
    count = 0
    from src.db import insert_event

    for row in rows:
        source_marker = f"[{row['id']}]"
        existing = conn.execute(
            "select id from events where source_documents_json = ?",
            (source_marker,),
        ).fetchone()
        if existing:
            continue
        event = classify_document(row)
        event_id = insert_event(conn, event)
        if event_id:
            count += 1
    return count


def extract_campaign_name(text: str) -> str | None:
    patterns = [r"「([^」]{3,40}(?:キャンペーン|プロジェクト|フェア)[^」]*)」", r"『([^』]{3,40})』"]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return None


def infer_channel(source_type: str, text: str) -> str:
    if source_type == "youtube" or "YouTube" in text or "動画" in text:
        return "YouTube/Web動画"
    if "店頭" in text or "サンプリング" in text:
        return "店頭/サンプリング"
    if source_type == "news_pr":
        return "ニュース/PR"
    if source_type == "official_site":
        return "公式サイト"
    return "Web"


def infer_target(text: str) -> str | None:
    if "0歳" in text or "母乳" in text or "新生児" in text:
        return "0-1歳児の保護者"
    if "1歳" in text or "3歳" in text or "フォローアップ" in text:
        return "1-3歳児の保護者"
    return "乳幼児の保護者"


def extract_talent(text: str) -> str | None:
    m = re.search(r"([一-龥ぁ-んァ-ヶA-Za-z ]{2,20})さん", text)
    return m.group(1).strip() if m else None


def extract_message(text: str) -> str | None:
    m = re.search(r"「([^」]{8,80})」", text)
    return m.group(1) if m else None


def infer_marketing_intent(event_type: str, text: str) -> str:
    mapping = {
        "PRODUCT_RENEWAL": "商品理解の更新、品質・成分・利便性の再訴求",
        "CAMPAIGN_LAUNCH": "応募や体験機会を通じたブランド接触の拡大",
        "ADVERTISING": "認知拡大とブランド想起の獲得",
        "SAMPLING": "試用促進と購入前不安の低減",
        "EVENT": "育児接点での信頼形成",
        "COLLABORATION": "外部ブランドや企画の話題性活用",
    }
    return mapping.get(event_type, "公開情報からの接触機会維持または企業情報発信")


def summarize(title: str, text: str) -> str:
    body = re.sub(r"\s+", " ", text).strip()
    if len(body) > 180:
        body = body[:180] + "..."
    return f"{title}: {body}" if body and body != title else title


