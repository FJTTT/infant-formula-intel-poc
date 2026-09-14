from __future__ import annotations

import difflib
import sqlite3


def find_duplicate_candidates(conn: sqlite3.Connection) -> int:
    conn.execute("delete from duplicate_candidates")
    docs = conn.execute(
        "select id, title, product, published_at, content_hash from documents order by product, published_at"
    ).fetchall()
    inserted = 0
    for i, a in enumerate(docs):
        for b in docs[i + 1 :]:
            if a["product"] != b["product"]:
                continue
            title_score = difflib.SequenceMatcher(None, a["title"], b["title"]).ratio()
            same_month = (a["published_at"] or "")[:7] and (a["published_at"] or "")[:7] == (b["published_at"] or "")[:7]
            if a["content_hash"] == b["content_hash"] or title_score >= 0.86 or (title_score >= 0.72 and same_month):
                conn.execute(
                    "insert into duplicate_candidates (document_id, duplicate_of_document_id, reason, score) values (?, ?, ?, ?)",
                    (b["id"], a["id"], "title/content/date/product similarity", title_score),
                )
                inserted += 1
    conn.commit()
    return inserted

