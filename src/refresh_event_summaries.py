from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.repair_encoding import mojibake_score, repair_text
from src.utils import content_hash

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "poc.sqlite"


def first_doc_id(source_documents_json: str) -> int | None:
    try:
        ids = json.loads(source_documents_json)
    except json.JSONDecodeError:
        return None
    return int(ids[0]) if ids else None


def clean_display_text(*parts: str) -> str:
    cleaned = []
    for part in parts:
        fixed = repair_text(part or "") or ""
        if fixed and mojibake_score(fixed) == 0:
            cleaned.append(fixed.strip())
    if not cleaned:
        return ""
    # Avoid duplicating title/body prefixes in timeline cells.
    out = cleaned[0]
    for extra in cleaned[1:]:
        if extra and extra not in out and out not in extra:
            out = f"{out}: {extra[:160]}"
            break
    return out[:360]


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    changed = 0
    events = conn.execute("select * from events").fetchall()
    for event in events:
        doc_id = first_doc_id(event["source_documents_json"])
        if not doc_id:
            continue
        doc = conn.execute("select * from documents where id=?", (doc_id,)).fetchone()
        if not doc:
            continue
        summary = clean_display_text(doc["title"], doc["snippet"])
        if not summary:
            summary = repair_text(event["summary"]) or event["summary"]
        try:
            fact = json.loads(event["fact_json"])
        except json.JSONDecodeError:
            fact = {}
        fact.update(
            {
                "title": doc["title"],
                "url": doc["url"],
                "source_type": doc["source_type"],
                "published_at": doc["published_at"],
                "matched_text": summary,
            }
        )
        campaign_key = content_hash(event["product"], event["event_type"], event["campaign_name"] or doc["title"][:60])[:16]
        conn.execute(
            "update events set summary=?, fact_json=?, campaign_key=? where id=?",
            (summary, json.dumps(fact, ensure_ascii=False), campaign_key, event["id"]),
        )
        changed += 1
    conn.commit()
    print({"events_refreshed": changed})


if __name__ == "__main__":
    main()
