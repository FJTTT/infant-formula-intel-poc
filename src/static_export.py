from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"
SITE = OUTPUT / "site"


def load_csv(name: str) -> list[dict]:
    path = OUTPUT / name
    if not path.exists():
        return []
    df = pd.read_csv(path, dtype=str).fillna("")
    return df.to_dict(orient="records")


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    payload = {
        "documents": load_csv("documents.csv"),
        "events": load_csv("events.csv"),
        "campaigns": load_csv("campaigns.csv"),
    }
    html = f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>乳幼児ミルク競合Marketing Intel PoC</title>
  <style>
    :root {{ font-family: Arial, 'Yu Gothic', 'Meiryo', sans-serif; color: #1f2933; background: #f6f7f9; }}
    body {{ margin: 0; }}
    header {{ padding: 20px 28px; background: #ffffff; border-bottom: 1px solid #d8dee7; }}
    h1 {{ margin: 0; font-size: 22px; }}
    main {{ padding: 20px 28px 40px; }}
    .filters {{ display: grid; grid-template-columns: repeat(6, minmax(130px, 1fr)); gap: 10px; margin-bottom: 16px; }}
    label {{ display: grid; gap: 4px; font-size: 12px; font-weight: 700; color: #405064; }}
    select {{ min-height: 34px; border: 1px solid #c5ced9; border-radius: 6px; background: #fff; padding: 5px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }}
    .metric {{ background: #fff; border: 1px solid #d8dee7; border-radius: 8px; padding: 14px; }}
    .metric strong {{ display: block; font-size: 26px; margin-top: 4px; }}
    .tabs {{ display: flex; gap: 8px; margin: 16px 0 10px; flex-wrap: wrap; }}
    button {{ border: 1px solid #b9c4d0; background: #fff; border-radius: 6px; padding: 8px 10px; cursor: pointer; }}
    button.active {{ background: #18324a; color: #fff; border-color: #18324a; }}
    section {{ display: none; }}
    section.active {{ display: block; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #e1e6ed; padding: 8px; vertical-align: top; text-align: left; }}
    th {{ position: sticky; top: 0; background: #eef2f6; z-index: 1; }}
    .table-wrap {{ max-height: 68vh; overflow: auto; border: 1px solid #d8dee7; border-radius: 8px; background: #fff; }}
    a {{ color: #0f5fa8; }}
    .chart {{ display: grid; gap: 8px; background: #fff; border: 1px solid #d8dee7; border-radius: 8px; padding: 12px; }}
    .bar {{ display: grid; grid-template-columns: 82px 1fr 46px; gap: 8px; align-items: center; }}
    .fill {{ height: 18px; background: #2f7d78; border-radius: 4px; }}
    @media (max-width: 900px) {{ .filters, .metrics {{ grid-template-columns: 1fr 1fr; }} }}
    @media (max-width: 560px) {{ main, header {{ padding: 14px; }} .filters, .metrics {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header><h1>乳幼児ミルク競合Marketing Intel PoC</h1></header>
  <main>
    <div class=\"filters\" id=\"filters\"></div>
    <div class=\"metrics\">
      <div class=\"metric\">Documents<strong id=\"docCount\">0</strong></div>
      <div class=\"metric\">Events<strong id=\"eventCount\">0</strong></div>
      <div class=\"metric\">Campaigns<strong id=\"campaignCount\">0</strong></div>
    </div>
    <div class=\"tabs\">
      <button class=\"active\" data-tab=\"timeline\">Timeline</button>
      <button data-tab=\"events\">Event一覧</button>
      <button data-tab=\"campaigns\">Campaign一覧</button>
      <button data-tab=\"sources\">元ソース</button>
      <button data-tab=\"monthly\">月別活動件数</button>
    </div>
    <section id=\"timeline\" class=\"active\"><div class=\"table-wrap\"><table></table></div></section>
    <section id=\"events\"><div class=\"table-wrap\"><table></table></div></section>
    <section id=\"campaigns\"><div class=\"table-wrap\"><table></table></div></section>
    <section id=\"sources\"><div class=\"table-wrap\"><table></table></div></section>
    <section id=\"monthly\"><div class=\"chart\" id=\"chart\"></div></section>
  </main>
  <script id=\"payload\" type=\"application/json\">{json.dumps(payload, ensure_ascii=False)}</script>
  <script>
    const data = JSON.parse(document.getElementById('payload').textContent);
    const state = {{ company:'', brand:'', product:'', age_segment:'', month:'', event_type:'' }};
    const filterDefs = [
      ['company','メーカー'], ['brand','ブランド'], ['product','商品'], ['age_segment','対象年齢'], ['month','月'], ['event_type','Event Type']
    ];
    const monthOf = value => (value || '').slice(0, 7);
    data.documents.forEach(d => d.month = monthOf(d.published_at));
    data.events.forEach(e => e.month = monthOf(e.event_date));
    function values(key) {{
      const rows = key === 'event_type' ? data.events : data.documents;
      return [...new Set(rows.map(r => r[key]).filter(Boolean))].sort();
    }}
    function buildFilters() {{
      const root = document.getElementById('filters');
      root.innerHTML = '';
      filterDefs.forEach(([key,label]) => {{
        const wrap = document.createElement('label');
        wrap.textContent = label;
        const sel = document.createElement('select');
        sel.innerHTML = '<option value="">All</option>' + values(key).map(v => `<option>${{v}}</option>`).join('');
        sel.onchange = () => {{ state[key] = sel.value; render(); }};
        wrap.appendChild(sel);
        root.appendChild(wrap);
      }});
    }}
    function pass(row, includeEventType=false) {{
      for (const key of ['company','brand','product','age_segment','month']) if (state[key] && row[key] !== state[key]) return false;
      if (includeEventType && state.event_type && row.event_type !== state.event_type) return false;
      return true;
    }}
    function table(id, rows, cols) {{
      const el = document.querySelector(`#${{id}} table`);
      const head = '<thead><tr>' + cols.map(c => `<th>${{c}}</th>`).join('') + '</tr></thead>';
      const body = rows.map(r => '<tr>' + cols.map(c => {{
        const val = r[c] || '';
        if (c === 'url' && val) return `<td><a href="${{val}}" target="_blank" rel="noreferrer">${{val}}</a></td>`;
        return `<td>${{String(val).replace(/[&<>]/g, s => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[s]))}}</td>`;
      }}).join('') + '</tr>').join('');
      el.innerHTML = head + '<tbody>' + body + '</tbody>';
    }}
    function renderChart(events) {{
      const grouped = {{}};
      events.forEach(e => {{ if (e.month) grouped[e.month] = (grouped[e.month] || 0) + 1; }});
      const max = Math.max(1, ...Object.values(grouped));
      document.getElementById('chart').innerHTML = Object.entries(grouped).sort().map(([m,c]) =>
        `<div class="bar"><strong>${{m}}</strong><div class="fill" style="width:${{Math.max(4, c / max * 100)}}%"></div><span>${{c}}</span></div>`
      ).join('') || '該当なし';
    }}
    function render() {{
      const docs = data.documents.filter(d => pass(d));
      const events = data.events.filter(e => pass(e, true));
      const campaigns = data.campaigns.filter(c => pass(c));
      docCount.textContent = docs.length; eventCount.textContent = events.length; campaignCount.textContent = campaigns.length;
      table('timeline', events.sort((a,b) => (a.event_date || '').localeCompare(b.event_date || '')), ['event_date','company','brand','product','age_segment','event_type','campaign_name','summary','confidence']);
      table('events', events, ['event_date','company','brand','product','event_type','summary','target','message','talent','channel','marketing_intent','confidence','fact_json','inference_json']);
      table('campaigns', campaigns, ['start_date','end_date','company','brand','product','campaign_name','event_count','document_count','summary']);
      table('sources', docs, ['published_at','company','brand','product','source_type','source_name','title','url','snippet']);
      renderChart(events);
    }}
    document.querySelectorAll('button[data-tab]').forEach(btn => btn.onclick = () => {{
      document.querySelectorAll('button[data-tab], section').forEach(el => el.classList.remove('active'));
      btn.classList.add('active'); document.getElementById(btn.dataset.tab).classList.add('active');
    }});
    buildFilters(); render();
  </script>
</body>
</html>
"""
    (SITE / "index.html").write_text(html, encoding="utf-8")
    print(SITE / "index.html")


if __name__ == "__main__":
    main()
