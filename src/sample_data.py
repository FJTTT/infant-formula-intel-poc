from __future__ import annotations

from src.models import Document, ProductConfig, now_iso, today_iso


def sample_documents(product: ProductConfig) -> list[Document]:
    examples = {
        "明治ほほえみ": [("明治ほほえみ らくらくキューブ キャンペーン情報", "CAMPAIGN_LAUNCH", "2026-03-15")],
        "明治ステップ": [("明治ステップ フォローアップミルク 商品情報更新", "PRODUCT_RENEWAL", "2026-05-10")],
        "森永はぐくみ": [("森永はぐくみ 育児応援キャンペーン", "CAMPAIGN_LAUNCH", "2026-02-20")],
        "森永E赤ちゃん": [("森永E赤ちゃん ペプチドミルク PR動画", "ADVERTISING", "2026-04-08")],
        "森永チルミル": [("森永チルミル フォローアップミルク 店頭サンプリング", "SAMPLING", "2026-06-18")],
        "ビーンスタークすこやかM1": [("すこやかM1 公式ニュースリリース", "PR_ACTIVITY", "2026-01-25")],
        "ビーンスタークつよいこ": [("つよいこ パッケージリニューアル", "PRODUCT_RENEWAL", "2026-07-12")],
        "レーベンスミルク はいはい": [("和光堂はいはい プレゼントキャンペーン", "CAMPAIGN_LAUNCH", "2026-03-02")],
        "フォローアップミルク ぐんぐん": [("和光堂ぐんぐん 育児イベント協賛", "EVENT", "2026-05-22")],
        "アイクレオ バランスミルク": [("アイクレオ バランスミルク Web動画公開", "ADVERTISING", "2026-04-19")],
        "アイクレオ グローアップミルク": [("アイクレオ グローアップミルク コラボ企画", "COLLABORATION", "2026-08-05")],
        "雪印メグミルクぴゅあ": [("雪印メグミルクぴゅあ 商品紹介ページ更新", "CONTENT", "2026-02-06")],
        "雪印メグミルクたっち": [("雪印メグミルクたっち キャンペーン告知", "CAMPAIGN_LAUNCH", "2026-07-30")],
    }
    docs: list[Document] = []
    for idx, (title, event_type, published_at) in enumerate(examples.get(product.product, []), start=1):
        docs.append(
            Document(
                title=title,
                url=f"https://example.local/poc/{product.product}/{idx}",
                source_name="PoC sample seed",
                source_type="sample",
                published_at=published_at,
                first_seen_at=today_iso(),
                collected_at=now_iso(),
                company=product.company,
                brand=product.brand,
                product=product.product,
                age_segment=product.age_segment,
                body=f"{title}。{product.brand}に関する{event_type}の検証用サンプル。Fact: サンプルデータであり実Web取得失敗時のUI確認用。",
                snippet=title,
                metadata={"sample": True},
            )
        )
    return docs

