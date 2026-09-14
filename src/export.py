from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"


def export_csv(conn: sqlite3.Connection, output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(exist_ok=True)
    for table in ["documents", "events", "campaigns", "visual_assets"]:
        df = pd.read_sql_query(f"select * from {table}", conn)
        df.to_csv(output_dir / f"{table}.csv", index=False, encoding="utf-8-sig")


