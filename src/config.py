from __future__ import annotations

import json
from pathlib import Path

from src.models import ProductConfig


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "products.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_products(path: Path = CONFIG_PATH) -> list[ProductConfig]:
    data = load_config(path)
    return [ProductConfig(**item) for item in data["products"]]


def load_query_terms(path: Path = CONFIG_PATH) -> list[str]:
    return load_config(path)["query_terms"]


def month_tokens(start: str, end: str) -> list[str]:
    from datetime import date

    y, m, _ = map(int, start.split("-"))
    ey, em, _ = map(int, end.split("-"))
    out: list[str] = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out

