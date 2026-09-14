from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "poc.sqlite"

SUSPICIOUS = [
    "ã", "â", "å", "æ", "ç", "é", "ï", "ð", "窶",
    "譁", "縺", "逕", "莠", "荳", "驥", "繧", "蜷", "髱", "邨", "螟", "隱",
    "\ufffd", "\u0080", "\u0081", "\u0082", "\u0083", "\u0084", "\u0085", "\u0086", "\u0087", "\u0088", "\u0089", "\u0090", "\u0091", "\u0092", "\u0093", "\u0094", "\u0095", "\u0096", "\u0097", "\u0098", "\u0099",
]


def mojibake_score(value: str) -> int:
    if not value:
        return 0
    score = sum(value.count(s) * 4 for s in SUSPICIOUS)
    score += sum(2 for ch in value if 0x80 <= ord(ch) <= 0x9F)
    score += value.count("?")
    return score


def readable_score(value: str) -> int:
    return sum(1 for ch in value if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff")


def decode_candidate(value: str, encoding: str) -> str | None:
    try:
        return value.encode("latin1").decode(encoding)
    except UnicodeError:
        return None


def repair_whole(value: str) -> str:
    best = value
    best_tuple = (mojibake_score(best), -readable_score(best), len(best))
    queue = [value]
    seen = {value}
    for _ in range(2):
        current = list(queue)
        queue.clear()
        for item in current:
            for enc in ("utf-8", "cp932", "shift_jis"):
                candidate = decode_candidate(item, enc)
                if not candidate or candidate in seen:
                    continue
                seen.add(candidate)
                queue.append(candidate)
                score_tuple = (mojibake_score(candidate), -readable_score(candidate), len(candidate))
                if score_tuple < best_tuple:
                    best = candidate
                    best_tuple = score_tuple
    return best


def repair_mojibake_runs(value: str) -> str:
    # Mixed strings often contain good Japanese followed by a Latin-1-looking mojibake run.
    pattern = re.compile(r"[\u0080-\u00ff][\u0009\u000a\u000d\u0020-\u00ff]{2,}")

    def repl(match: re.Match[str]) -> str:
        original = match.group(0)
        fixed = repair_whole(original)
        return fixed if mojibake_score(fixed) < mojibake_score(original) else original

    return pattern.sub(repl, value)


def repair_text(value: str | None) -> str | None:
    if value is None or not isinstance(value, str) or not value:
        return value
    whole = repair_whole(value)
    if mojibake_score(whole) < mojibake_score(value):
        value = whole
    return repair_mojibake_runs(value)


def repair_json_text(value: str | None) -> str | None:
    if not value:
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return repair_text(value)

    def walk(obj):
        if isinstance(obj, str):
            return repair_text(obj)
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        return obj

    return json.dumps(walk(parsed), ensure_ascii=False)


def repair_table(conn: sqlite3.Connection, table: str, text_cols: list[str], json_cols: list[str] | None = None) -> int:
    json_cols = json_cols or []
    rows = conn.execute(f"select id, {', '.join(text_cols + json_cols)} from {table}").fetchall()
    changed = 0
    for row in rows:
        updates = {}
        for col in text_cols:
            fixed = repair_text(row[col])
            if fixed != row[col]:
                updates[col] = fixed
        for col in json_cols:
            fixed = repair_json_text(row[col])
            if fixed != row[col]:
                updates[col] = fixed
        if updates:
            assignments = ", ".join(f"{col}=?" for col in updates)
            conn.execute(f"update {table} set {assignments} where id=?", [*updates.values(), row["id"]])
            changed += 1
    conn.commit()
    return changed


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    totals = {
        "documents": repair_table(conn, "documents", ["title", "source_name", "body", "snippet"], ["metadata_json"]),
        "events": repair_table(conn, "events", ["campaign_name", "summary", "target", "message", "talent", "channel", "marketing_intent"], ["fact_json", "inference_json"]),
        "campaigns": repair_table(conn, "campaigns", ["campaign_name", "summary"]),
    }
    print(totals)


if __name__ == "__main__":
    main()
