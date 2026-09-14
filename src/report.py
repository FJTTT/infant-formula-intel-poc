from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "POC_REPORT.md"


def _md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_該当なし_"
    cols = [str(c) for c in df.columns]
    rows = [[str(v) for v in row] for row in df.astype(object).where(pd.notna(df), "").values.tolist()]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join([header, sep] + body)


def write_report(conn: sqlite3.Connection, path: Path = REPORT_PATH) -> None:
    docs = pd.read_sql_query("select * from documents", conn)
    events = pd.read_sql_query("select * from events", conn)
    campaigns = pd.read_sql_query("select * from campaigns", conn)
    dupes = pd.read_sql_query("select * from duplicate_candidates", conn)

    def count_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=[col, "count"])
        return df.groupby(col).size().reset_index(name="count").sort_values("count", ascending=False)

    month = docs.assign(month=docs["published_at"].fillna("").str[:7]) if not docs.empty else docs
    month_counts = count_by(month[month["month"] != ""], "month") if not docs.empty and "month" in month else pd.DataFrame()
    lines = [
        "# POC_REPORT",
        "",
        "## 件数サマリー",
        f"- 総Document件数: {len(docs)}",
        f"- 総Event件数: {len(events)}",
        f"- 総Campaign件数: {len(campaigns)}",
        f"- 重複候補件数: {len(dupes)}",
        "",
        "## メーカー別件数",
        _md_table(count_by(docs, "company")),
        "",
        "## 商品別件数",
        _md_table(count_by(docs, "product")),
        "",
        "## 月別件数",
        _md_table(month_counts),
        "",
        "## 情報源別件数",
        _md_table(count_by(docs, "source_type")),
        "",
        "## うまく取得できた情報",
        "- 公式サイト、Google News RSS、DuckDuckGo Lite検索、YouTube検索痕跡をCollectorごとに分離して保存できる構成にした。",
        "- published_at / first_seen_at / collected_at を分けて保持し、再実行時は normalized_url と product でupsertする。",
        "- Document、Event、Campaignを別テーブルにし、Fact JSON と Inference JSON を分けた。",
        "",
        "## 取得できなかった情報・限界",
        "- 検索エンジン結果は環境、地域、検索時点で変動するため、完全な網羅性は保証できない。",
        "- 広告出稿履歴は公開検索だけでは網羅しにくい。Meta/Google広告ライブラリ、CM出稿データ、YouTube Data API等の追加Collectorが必要。",
        "- SNSはログイン、規約、検索API制限の影響が大きく、今回は必須取得対象から外し、公開Webに露出した痕跡のみ扱う。",
        "- YouTubeはAPIキーなしでは検索結果HTML経由のため、公式チャンネル単位の厳密な取得にはYouTube Data API Collectorが必要。",
        "",
        "## 重複の状況",
        f"- URL正規化とタイトル類似で {len(dupes)} 件の重複候補を検出した。PR転載は施策単位でCampaignに寄せて見る前提が妥当。",
        "",
        "## 誤分類と思われるケース",
        "- 現状の標準分類はヒューリスティックであり、商品ページ自体がOTHERまたはPR_ACTIVITYになりやすい。",
        "- タイトルに「キャンペーン」などが含まれる記事は精度が出やすい一方、本文取得ができない検索結果のみのDocumentは確信度が下がる。",
        "",
        "## 検索漏れがありそうな領域",
        "- 店頭施策、量販店アプリ、育児イベント、自治体・産院連携、インフルエンサー投稿、テレビCM出稿量。",
        "",
        "## 今後追加すべきCollector",
        "- YouTube Data API Collector",
        "- PR TIMES / 共同通信PRワイヤー等の媒体別Collector",
        "- 広告ライブラリCollector",
        "- 公式ニュースリリースサイトのサイトマップCollector",
        "- SNS公式アカウントの規約準拠API Collector",
        "",
        "## 人間の競合マーケティング把握に対する有用性",
        "このPoCは、2026年1〜8月の競合マーケティング活動を人間が概観するための一次整理として有用である。特に、商品別・月別・情報源別にDocumentからEvent、Campaignへ粒度を落として確認できるため、記事件数をそのまま活動量と誤解するリスクを下げられる。一方で、広告出稿やSNS起点の話題化は公開Web検索だけでは薄くなるため、意思決定に使うには媒体別APIや手動レビューを組み合わせる必要がある。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


