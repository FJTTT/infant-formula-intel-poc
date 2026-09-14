from __future__ import annotations

import json
import sqlite3


def rebuild_campaigns(conn: sqlite3.Connection) -> int:
    conn.execute("delete from campaigns")
    groups = conn.execute(
        """
        select campaign_key, company, brand, product, age_segment, campaign_name,
               min(event_date) as start_date, max(event_date) as end_date,
               count(*) as event_count
        from events
        where campaign_key is not null
        group by campaign_key, company, brand, product, age_segment, campaign_name
        """
    ).fetchall()
    count = 0
    for g in groups:
        events = conn.execute("select id, summary, source_documents_json from events where campaign_key=?", (g["campaign_key"],)).fetchall()
        event_ids = [int(e["id"]) for e in events]
        doc_ids: set[int] = set()
        summaries = []
        for e in events:
            summaries.append(e["summary"])
            for doc_id in json.loads(e["source_documents_json"]):
                doc_ids.add(int(doc_id))
        summary = summaries[0][:400] if summaries else ""
        conn.execute(
            """
            insert into campaigns
            (campaign_key, company, brand, product, age_segment, campaign_name, start_date, end_date,
             event_count, document_count, summary, event_ids_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g["campaign_key"],
                g["company"],
                g["brand"],
                g["product"],
                g["age_segment"],
                g["campaign_name"],
                g["start_date"],
                g["end_date"],
                int(g["event_count"]),
                len(doc_ids),
                summary,
                json.dumps(event_ids, ensure_ascii=False),
            ),
        )
        count += 1
    conn.commit()
    return count

