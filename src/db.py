from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.models import Document, Event
from src.utils import content_hash, normalize_url


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "poc.sqlite"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists documents (
          id integer primary key autoincrement,
          title text not null,
          url text not null,
          normalized_url text not null,
          source_name text not null,
          source_type text not null,
          published_at text,
          first_seen_at text not null,
          collected_at text not null,
          company text not null,
          brand text not null,
          product text not null,
          age_segment text not null,
          body text,
          snippet text,
          content_hash text not null,
          metadata_json text default '{}',
          unique(normalized_url, product)
        );
        create table if not exists duplicate_candidates (
          id integer primary key autoincrement,
          document_id integer not null,
          duplicate_of_document_id integer not null,
          reason text not null,
          score real not null
        );
        create table if not exists events (
          id integer primary key autoincrement,
          company text not null,
          brand text not null,
          product text not null,
          age_segment text not null,
          event_type text not null,
          event_date text,
          campaign_name text,
          summary text not null,
          target text,
          message text,
          talent text,
          channel text,
          marketing_intent text,
          importance integer,
          confidence real,
          fact_json text not null,
          inference_json text not null,
          source_documents_json text not null,
          campaign_key text,
          unique(product, event_type, event_date, summary)
        );
        create table if not exists campaigns (
          id integer primary key autoincrement,
          campaign_key text not null unique,
          company text not null,
          brand text not null,
          product text not null,
          age_segment text not null,
          campaign_name text,
          start_date text,
          end_date text,
          event_count integer not null,
          document_count integer not null,
          summary text not null,
          event_ids_json text not null
        );
        """
    )
    conn.commit()


def upsert_document(conn: sqlite3.Connection, doc: Document) -> int:
    doc.normalized_url = normalize_url(doc.url)
    doc.content_hash = content_hash(doc.title, doc.body, doc.snippet)
    existing = conn.execute(
        "select id, first_seen_at from documents where normalized_url = ? and product = ?",
        (doc.normalized_url, doc.product),
    ).fetchone()
    if existing:
        conn.execute(
            """
            update documents
            set title=?, source_name=?, source_type=?, published_at=coalesce(?, published_at),
                collected_at=?, company=?, brand=?, age_segment=?, body=?, snippet=?,
                content_hash=?, metadata_json=?
            where id=?
            """,
            (
                doc.title,
                doc.source_name,
                doc.source_type,
                doc.published_at,
                doc.collected_at,
                doc.company,
                doc.brand,
                doc.age_segment,
                doc.body,
                doc.snippet,
                doc.content_hash,
                json.dumps(doc.metadata, ensure_ascii=False),
                existing["id"],
            ),
        )
        conn.commit()
        return int(existing["id"])
    cur = conn.execute(
        """
        insert into documents
        (title, url, normalized_url, source_name, source_type, published_at, first_seen_at,
         collected_at, company, brand, product, age_segment, body, snippet, content_hash, metadata_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc.title,
            doc.url,
            doc.normalized_url,
            doc.source_name,
            doc.source_type,
            doc.published_at,
            doc.first_seen_at,
            doc.collected_at,
            doc.company,
            doc.brand,
            doc.product,
            doc.age_segment,
            doc.body,
            doc.snippet,
            doc.content_hash,
            json.dumps(doc.metadata, ensure_ascii=False),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def insert_event(conn: sqlite3.Connection, event: Event) -> int:
    cur = conn.execute(
        """
        insert or ignore into events
        (company, brand, product, age_segment, event_type, event_date, campaign_name, summary,
         target, message, talent, channel, marketing_intent, importance, confidence,
         fact_json, inference_json, source_documents_json, campaign_key)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.company,
            event.brand,
            event.product,
            event.age_segment,
            event.event_type,
            event.event_date,
            event.campaign_name,
            event.summary,
            event.target,
            event.message,
            event.talent,
            event.channel,
            event.marketing_intent,
            event.importance,
            event.confidence,
            event.fact_json,
            event.inference_json,
            json.dumps(event.source_documents, ensure_ascii=False),
            event.campaign_key,
        ),
    )
    conn.commit()
    if cur.lastrowid:
        return int(cur.lastrowid)
    row = conn.execute(
        "select id from events where product=? and event_type=? and coalesce(event_date,'')=coalesce(?,'') and summary=?",
        (event.product, event.event_type, event.event_date, event.summary),
    ).fetchone()
    return int(row["id"]) if row else 0

