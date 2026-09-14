import sqlite3

import pytest


@pytest.fixture
def sqlite_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        create table documents (
          id integer, title text, url text, source_type text, published_at text,
          company text, brand text, product text, age_segment text, snippet text, body text
        )
        """
    )
    conn.execute(
        "insert into documents values (1, '育児応援キャンペーン開始', 'https://example.com', 'news_pr', '2026-03-01', '明治', 'ほほえみ', '明治ほほえみ', '0-1', 'キャンペーン', '')"
    )
    return conn.execute("select * from documents").fetchone()
