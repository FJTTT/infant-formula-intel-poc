# 乳幼児用ミルク競合マーケティング情報収集PoC

Windowsローカルで、明治「ほほえみ」「ステップ」と競合商品の公開Web情報を収集し、Document、Event、Campaignに整理するPoCです。

## セットアップ

```powershell
uv sync
```

## バックフィル

```powershell
uv run python -m src.backfill --from 2026-01-01 --to 2026-08-31
```

ネットワーク検索が制限される環境でもPoCを評価できるよう、`--use-sample` でサンプル実データ投入もできます。

```powershell
uv run python -m src.backfill --from 2026-01-01 --to 2026-08-31 --use-sample
```

## UI

```powershell
uv run streamlit run app.py
```

## 主な出力

- `output/documents.csv`
- `output/events.csv`
- `output/campaigns.csv`
- `POC_REPORT.md`

