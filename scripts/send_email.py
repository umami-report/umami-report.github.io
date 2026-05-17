#!/usr/bin/env python3
"""Send daily news digest email from /tmp/articles.json via Gmail SMTP."""
import json, os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "takahashidan0530@gmail.com")
TO_EMAIL   = os.environ.get("TO_EMAIL",   "takahashidan0530@gmail.com")

if not GMAIL_APP_PASSWORD:
    print("GMAIL_APP_PASSWORD not set — skipping email. "
          "Add it as a GitHub secret to enable daily emails.")
    raise SystemExit(0)

with open("/tmp/articles.json", encoding="utf-8") as f:
    data = json.load(f)

date_str  = data.get("date_str", datetime.now().strftime("%Y年%m月%d日"))
time_str  = data.get("time_str", "")
markets   = data.get("markets", {})

# ── helpers ────────────────────────────────────────────────────────────────
def fmt_price(price, currency):
    if currency == "JPY": return f"¥{price:,.0f}"
    if currency == "GBP": return f"£{price:,.0f}"
    return f"${price:.2f}" if price < 1000 else f"${price:,.2f}"

def market_row(key, label, def_cur, url):
    m = markets.get(key)
    if not m: return ""
    price  = m.get("price", 0)
    chg    = m.get("change_pct", 0)
    cur    = m.get("currency", def_cur)
    lbl    = m.get("_label", label)
    sign   = "+" if chg >= 0 else ""
    color  = "#16a34a" if chg >= 0 else "#dc2626"
    arrow  = "▲" if chg >= 0 else "▼"
    fetched = m.get("fetched_at", "")
    return (
        f'<tr>'
        f'<td style="padding:6px 12px;font-weight:bold;color:#555">{lbl}</td>'
        f'<td style="padding:6px 12px;font-size:1.1em;font-weight:bold">{fmt_price(price,cur)}</td>'
        f'<td style="padding:6px 12px;color:{color};font-weight:bold">{arrow} {sign}{chg:.2f}%</td>'
        f'<td style="padding:6px 12px;color:#999;font-size:.8em">{fetched} JST</td>'
        f'<td style="padding:6px 12px"><a href="{url}" style="color:#2563eb;font-size:.8em">詳細 →</a></td>'
        f'</tr>'
    )

def article_rows(items, show_excerpt=False):
    if not items:
        return '<p style="color:#999;font-style:italic;margin:4px 0">記事なし</p>'
    rows = []
    for a in items:
        title   = a.get("title") or a.get("raw", "")
        link    = a.get("link", "#")
        source  = a.get("source", "")
        date    = a.get("date", "")
        excerpt = a.get("excerpt", "")
        fav_url = a.get("favicon", "")
        fav_img = (f'<img src="{fav_url}" width="14" height="14" '
                   f'style="vertical-align:middle;margin-right:4px" alt="">'
                   if fav_url else "")
        meta = " · ".join(filter(None, [source, date]))
        exc_html = (f'<p style="margin:2px 0 4px 0;color:#555;font-size:.82em;line-height:1.4">'
                    f'{excerpt[:200]}</p>' if show_excerpt and excerpt else "")
        rows.append(
            f'<div style="padding:8px 0;border-bottom:1px solid #f0f0f0">'
            f'<a href="{link}" style="color:#1a1a2e;font-weight:bold;text-decoration:none;font-size:.93em">'
            f'{title}</a>'
            f'<br><span style="color:#888;font-size:.78em">{fav_img}{meta}</span>'
            f'{exc_html}'
            f'</div>'
        )
    return "".join(rows)

def section(title, emoji, items, color="#2563eb", show_excerpt=False):
    count = len(items)
    return (
        f'<div style="margin:24px 0">'
        f'<h2 style="margin:0 0 8px 0;padding:8px 12px;background:{color};color:#fff;'
        f'font-size:.95em;border-radius:4px">{emoji} {title} <span style="font-weight:normal;'
        f'font-size:.85em;opacity:.8">{count}件</span></h2>'
        f'<div style="padding:0 4px">{article_rows(items, show_excerpt)}</div>'
        f'</div>'
    )

# ── build HTML ─────────────────────────────────────────────────────────────
market_rows_html = (
    market_row("nikkei", "日経平均",      "JPY", "https://finance.yahoo.com/quote/%5EN225/") +
    market_row("cocoa",  "カカオ London", "GBP", "https://finance.yahoo.com/quote/CC=F/") +
    market_row("orcan",  "MSCI ACWI",     "USD", "https://finance.yahoo.com/quote/ACWI/") +
    market_row("silver", "シルバー",      "USD", "https://finance.yahoo.com/quote/SI=F/")
)

dom   = data.get("domestic", [])
wld   = data.get("world", [])
ai    = data.get("ai", [])
food  = data.get("food_major", [])
conf  = data.get("confectionery", [])
choco = data.get("chocolate", [])
pats  = data.get("patents", [])
total = len(dom)+len(wld)+len(ai)+len(food)+len(conf)+len(choco)+len(pats)

html_body = f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#f9f9f9;margin:0;padding:0;color:#1a1a2e}}
  .wrap{{max-width:680px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden}}
  .header{{background:#1a1a2e;color:#fff;padding:20px 24px}}
  .header h1{{margin:0;font-size:1.3em}}
  .header p{{margin:4px 0 0;color:#aaa;font-size:.82em}}
  .body{{padding:16px 24px 32px}}
  a{{color:#2563eb}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>🍣 ウマミレポート デイリーダイジェスト</h1>
    <p>{date_str}　合計 {total} 件　取得: {time_str} JST</p>
  </div>
  <div class="body">

    <!-- Market Strip -->
    <div style="margin:16px 0">
      <h2 style="margin:0 0 8px 0;padding:8px 12px;background:#374151;color:#fff;
        font-size:.95em;border-radius:4px">📈 マーケット情報</h2>
      <table style="border-collapse:collapse;width:100%;font-size:.88em">
        {market_rows_html}
      </table>
    </div>

    {section("国内ニュース", "🗾", dom, "#1a1a2e", show_excerpt=True)}
    {section("世界ニュース", "🌍", wld, "#1e40af", show_excerpt=True)}
    {section("AI・テクノロジー", "🤖", ai, "#7c3aed", show_excerpt=True)}
    {section("食品業界", "🏭", food, "#065f46", show_excerpt=True)}
    {section("菓子・スイーツ", "🍰", conf, "#b45309")}
    {section("チョコレート新商品", "🍫", choco, "#7c2d12")}
    {section("特許情報", "📄", pats, "#374151")}

    <hr style="border:none;border-top:1px solid #eee;margin:32px 0 16px">
    <p style="color:#aaa;font-size:.75em;text-align:center">
      <a href="https://umami-report.github.io/" style="color:#aaa">ウマミレポート Web版</a>
      　|　配信停止は送信元へご連絡ください
    </p>
  </div>
</div>
</body>
</html>"""

# ── send ───────────────────────────────────────────────────────────────────
msg = MIMEMultipart("alternative")
msg["Subject"] = f"【ウマミレポート】{date_str} デイリーニュース ({total}件)"
msg["From"]    = FROM_EMAIL
msg["To"]      = TO_EMAIL
msg.attach(MIMEText(html_body, "html", "utf-8"))

print(f"Sending to {TO_EMAIL} ...")
with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.login(FROM_EMAIL, GMAIL_APP_PASSWORD)
    smtp.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_bytes())

print("Email sent successfully.")
