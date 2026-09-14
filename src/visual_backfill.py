from __future__ import annotations

from src.collectors.http import HttpClient
from src.collectors.official import extract_visual_assets
from src.db import connect
from src.models import Document, now_iso, today_iso
from src.repair_encoding import repair_text
from src.utils import compact_text, parse_date, text_from_html

from bs4 import BeautifulSoup
from urllib.parse import urlparse


def main() -> None:
    conn = connect()
    http = HttpClient(delay_seconds=0.05, timeout=8)
    rows = conn.execute(
        """
        select * from documents
        where source_type = 'official_site'
        order by id
        """
    ).fetchall()
    updated = 0
    total_assets = 0
    from src.db import upsert_document

    for row in rows:
        resp = http.get(row["url"])
        if not resp:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        title = repair_text((soup.title.get_text(" ", strip=True) if soup.title else row["title"]).strip()) or row["title"]
        body = repair_text(compact_text(text_from_html(resp.text), 2400)) or row["body"]
        published = row["published_at"] or parse_date(body)
        assets = extract_visual_assets(soup, row["url"])
        doc = Document(
            id=row["id"],
            title=title,
            url=row["url"],
            source_name=urlparse(row["url"]).netloc,
            source_type=row["source_type"],
            published_at=published,
            first_seen_at=row["first_seen_at"] or today_iso(),
            collected_at=now_iso(),
            company=row["company"],
            brand=row["brand"],
            product=row["product"],
            age_segment=row["age_segment"],
            body=body,
            snippet=body[:300],
            metadata={"visual_assets": assets, "visual_asset_count": len(assets), "visual_backfilled": True},
        )
        upsert_document(conn, doc)
        updated += 1
        total_assets += len(assets)
        print(f"{row['id']}: {title[:60]} assets={len(assets)}", flush=True)
    print({"documents_updated": updated, "visual_assets_seen": total_assets})


if __name__ == "__main__":
    main()
