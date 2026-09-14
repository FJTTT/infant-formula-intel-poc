from __future__ import annotations

from pathlib import Path

import pandas as pd
import sqlite3
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "poc.sqlite"


st.set_page_config(page_title="乳幼児ミルク競合Marketing Intel PoC", layout="wide")
st.title("乳幼児ミルク競合Marketing Intel PoC")

if not DB_PATH.exists():
    st.warning("DBがありません。先に `uv run python -m src.backfill --from 2026-01-01 --to 2026-08-31` を実行してください。")
    st.stop()

conn = sqlite3.connect(DB_PATH)
docs = pd.read_sql_query("select * from documents", conn)
events = pd.read_sql_query("select * from events", conn)
campaigns = pd.read_sql_query("select * from campaigns", conn)

if docs.empty:
    st.info("Documentがまだありません。")
    st.stop()

docs["month"] = docs["published_at"].fillna("").str[:7]
events["month"] = events["event_date"].fillna("").str[:7]

with st.sidebar:
    st.header("Filters")
    companies = st.multiselect("メーカー", sorted(docs["company"].dropna().unique()))
    brands = st.multiselect("ブランド", sorted(docs["brand"].dropna().unique()))
    products = st.multiselect("商品", sorted(docs["product"].dropna().unique()))
    ages = st.multiselect("対象年齢", sorted(docs["age_segment"].dropna().unique()))
    months = st.multiselect("月", sorted([m for m in docs["month"].dropna().unique() if m]))
    event_types = st.multiselect("Event Type", sorted(events["event_type"].dropna().unique()) if not events.empty else [])


def apply_filters(df: pd.DataFrame, include_event_type: bool = False) -> pd.DataFrame:
    out = df.copy()
    if companies:
        out = out[out["company"].isin(companies)]
    if brands:
        out = out[out["brand"].isin(brands)]
    if products:
        out = out[out["product"].isin(products)]
    if ages:
        out = out[out["age_segment"].isin(ages)]
    if months and "month" in out:
        out = out[out["month"].isin(months)]
    if include_event_type and event_types:
        out = out[out["event_type"].isin(event_types)]
    return out


fd = apply_filters(docs)
fe = apply_filters(events, include_event_type=True)
fc = apply_filters(campaigns)

col1, col2, col3 = st.columns(3)
col1.metric("Documents", len(fd))
col2.metric("Events", len(fe))
col3.metric("Campaigns", len(fc))

tab_timeline, tab_events, tab_campaigns, tab_sources, tab_month = st.tabs(
    ["Timeline", "Event一覧", "Campaign一覧", "元ソース", "月別活動件数"]
)

with tab_timeline:
    show = fe.sort_values(["event_date", "company", "product"], na_position="last")
    st.dataframe(
        show[["event_date", "company", "brand", "product", "age_segment", "event_type", "campaign_name", "summary", "confidence"]],
        width="stretch",
        hide_index=True,
    )

with tab_events:
    st.dataframe(
        fe[[
            "event_date",
            "company",
            "brand",
            "product",
            "event_type",
            "summary",
            "target",
            "message",
            "talent",
            "channel",
            "marketing_intent",
            "confidence",
            "fact_json",
            "inference_json",
        ]],
        width="stretch",
        hide_index=True,
    )

with tab_campaigns:
    cols = ["start_date", "end_date", "company", "brand", "product", "campaign_name", "event_count", "document_count", "summary"]
    st.dataframe(fc[cols], width="stretch", hide_index=True)

with tab_sources:
    source_cols = ["published_at", "company", "brand", "product", "source_type", "source_name", "title", "url", "snippet"]
    st.dataframe(fd[source_cols], width="stretch", hide_index=True, column_config={"url": st.column_config.LinkColumn("url")})

with tab_month:
    if fe.empty:
        st.info("Eventがありません。")
    else:
        counts = fe.groupby(["month", "product"]).size().reset_index(name="events")
        st.bar_chart(counts, x="month", y="events", color="product")
        st.dataframe(counts, width="stretch", hide_index=True)


