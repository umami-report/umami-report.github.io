import xml.etree.ElementTree as ET, json, re, urllib.request, ssl, csv, io
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Bypass SSL verification (CCR environment uses SSL inspection with self-signed certs)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

JST = timezone(timedelta(hours=9))
now = datetime.now(timezone.utc).astimezone(JST)
cutoff = now - timedelta(days=14)
days_ja = "月火水木金土日"

def fetch_excerpt(url, chars=500):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as r:
            raw = r.read(80000).decode("utf-8", errors="ignore")
        raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL|re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", raw)
        text = " ".join(text.split())
        lines = [p.strip() for p in text.split(".") if len(p.strip()) > 30]
        body = ". ".join(lines)
        return body[200:200+chars] if len(body) > 200 else body[:chars]
    except:
        return ""

def parse_rss(fp, mx=5):
    items = []
    try:
        root = ET.parse(fp).getroot()
        ch = root.find("channel")
        if not ch: return items
        for it in ch.findall("item"):
            t=it.find("title"); l=it.find("link"); p=it.find("pubDate"); s=it.find("source")
            if t is None: continue
            pub=""; dt_sort=datetime.min.replace(tzinfo=timezone.utc)
            if p is not None and p.text:
                try:
                    dt=parsedate_to_datetime(p.text)
                    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                    if dt.astimezone(JST) < cutoff: continue
                    dt_sort=dt
                    pub=dt.astimezone(JST).strftime("%m/%d %H:%M")
                except: pass
            raw=t.text or ""; src=s.text if s is not None else ""
            surl=s.get("url","") if s is not None else ""
            link=l.text or "#" if l is not None else "#"
            clean=raw
            if src and clean.endswith(" - "+src): clean=clean[:-len(" - "+src)].strip()
            clean=re.sub(r"[]【】《》[〔〕]","",clean).strip()
            fav="https://www.google.com/s2/favicons?domain="+surl+"&sz=64" if surl else ""
            items.append({"title":clean,"raw":raw,"source":src,"source_url":surl,
                          "link":link,"date":pub,"favicon":fav,"excerpt":"","_dt":dt_sort})
        # 日付降順でソートして上位 mx 件を返す
        items.sort(key=lambda x: x["_dt"], reverse=True)
        items = items[:mx]
        for a in items: del a["_dt"]
    except Exception as e: print("err",fp,e)
    return items

def search_jplatpat(keyword, mx=5):
    """Search J-PlatPat for recent confectionery patents using Playwright."""
    patents = []
    try:
        from playwright.sync_api import sync_playwright
        import threading

        captured = []
        def run():
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                ctx = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
                page = ctx.new_page()

                def on_response(resp):
                    if "wst0401" in resp.url and resp.status == 200:
                        try:
                            data = resp.json()
                            if data.get("RSLT_INFO", {}).get("RSLT_CD") == 0:
                                captured.extend(data.get("SEARCH_RSLT_LIST") or [])
                        except: pass

                page.on("response", on_response)
                page.goto("https://www.j-platpat.inpit.go.jp/p0100", wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)

                # Type in the simple search box and submit
                try:
                    page.fill("input[type='text']", keyword)
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(5000)
                except: pass

                browser.close()

        t = threading.Thread(target=run)
        t.start(); t.join(timeout=45)

        print(f"J-PlatPat results for '{keyword}': {len(captured)}")
        cutoff_str = cutoff.strftime("%Y%m%d")
        for item in captured[:mx]:
            pub = item.get("PD","") or item.get("publicationDate","") or item.get("AD","") or ""
            pub_display = f"{pub[4:6]}/{pub[6:]}" if len(pub)==8 else pub
            if pub and pub < cutoff_str: continue
            title = item.get("TITL","") or item.get("inventionTitle","") or item.get("TI","") or str(item)[:60]
            app_no = item.get("APNO","") or item.get("applicationNumber","") or ""
            pub_no = item.get("PUBN","") or item.get("publicationNumber","") or ""
            if pub_no:
                link = f"https://www.j-platpat.inpit.go.jp/c1800/PU/{pub_no.replace(' ','-')}/ja"
            elif app_no:
                link = f"https://www.j-platpat.inpit.go.jp/c1800/PU/{app_no}/ja"
            else:
                link = "https://www.j-platpat.inpit.go.jp/p0100"
            patents.append({"title":title,"link":link,"date":pub_display,"source":"J-PlatPat","favicon":"","excerpt":""})
    except Exception as e:
        print(f"J-PlatPat search error: {e}")
    return patents

def parse_patents(fp, mx=3):
    patents = []
    try:
        root = ET.parse(fp).getroot()
        ch = root.find("channel")
        if not ch: return patents
        for it in ch.findall("item"):
            t=it.find("title"); l=it.find("link"); p=it.find("pubDate")
            if t is None: continue
            pub=""
            if p is not None and p.text:
                try:
                    dt=parsedate_to_datetime(p.text)
                    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                    if dt.astimezone(JST) < cutoff: continue
                    pub=dt.astimezone(JST).strftime("%m/%d")
                except: pass
            title=t.text or ""; link=l.text if l is not None else "#"
            patents.append({"title":title,"link":link,"date":pub,"source":"Google Patents",
                            "favicon":"","excerpt":""})
            if len(patents)>=mx: break
    except Exception as e: print("patent err",e)
    return patents

# ── Market data ──────────────────────────────────────────────────
def fetch_yahoo_prices(ticker, range_="3mo"):
    """Yahoo Finance chart API → {prices, price, change_pct, currency}"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range={range_}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as r:
            data = json.loads(r.read())
        res = data["chart"]["result"][0]
        closes = [c for c in (res["indicators"]["quote"][0].get("close") or []) if c is not None]
        meta = res["meta"]
        price = meta.get("regularMarketPrice") or (closes[-1] if closes else 0)
        prev  = meta.get("chartPreviousClose") or (closes[-2] if len(closes) > 1 else price)
        change_pct = ((price - prev) / prev * 100) if prev else 0
        fetched_at = datetime.now(JST).strftime("%m/%d %H:%M")
        return {"prices": closes[-90:], "price": price, "change_pct": change_pct,
                "currency": meta.get("currency", ""), "fetched_at": fetched_at}
    except Exception as e:
        print(f"Yahoo price error {ticker}: {e}"); return None

def fetch_stooq_prices(symbol):
    """Stooq CSV (London Cocoa @cc.b GBP/tonne など) → same format"""
    try:
        url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as r:
            text = r.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        closes = [float(row["Close"]) for row in reader if row.get("Close") not in ("", None, "null")]
        closes = closes[-90:]
        if not closes: return None
        price = closes[-1]; prev = closes[-2] if len(closes) > 1 else price
        change_pct = ((price - prev) / prev * 100) if prev else 0
        fetched_at = datetime.now(JST).strftime("%m/%d %H:%M")
        return {"prices": closes, "price": price, "change_pct": change_pct, "currency": "GBP", "fetched_at": fetched_at}
    except Exception as e:
        print(f"Stooq price error {symbol}: {e}"); return None

print("Fetching market data...")
# London Cocoa GBP (stooq) → fallback NY Cocoa USD (Yahoo CC=F)
cocoa = fetch_stooq_prices("@cc.b")
if not cocoa:
    print("  stooq @cc.b failed, trying Yahoo CC=F...")
    cocoa = fetch_yahoo_prices("CC=F")  # NY Cocoa USD/MT
    if cocoa:
        cocoa["_label"] = "カカオ (NY)"   # override label in publish
markets = {
    "nikkei": fetch_yahoo_prices("^N225"),      # 日経平均 (JPY)
    "cocoa":  cocoa,                             # ロンドンカカオ GBP or NY USD
    "orcan":  fetch_yahoo_prices("ACWI"),        # MSCI All Country World ETF (USD)
    "silver": fetch_yahoo_prices("SI=F"),        # Silver Futures USD/oz
}
for k, v in markets.items():
    print(f"  {k}: {v['price'] if v else 'N/A'}")

# Debug: raw file sizes and item counts before date filter
def raw_count(fp):
    try:
        import os
        sz = os.path.getsize(fp)
        root = ET.parse(fp).getroot(); ch = root.find("channel")
        cnt = len(ch.findall("item")) if ch else 0
        return {"size": sz, "items": cnt}
    except Exception as e:
        return {"size": 0, "items": 0, "err": str(e)}

debug_feeds = {k: raw_count(v) for k,v in {
    "domestic": "/tmp/news_domestic.xml",
    "world": "/tmp/news_world.xml",
    "ai": "/tmp/news_ai.xml",
    "food_major": "/tmp/news_food_major.xml",
    "conf": "/tmp/news_confectionery.xml",
    "choco": "/tmp/news_chocolate.xml",
}.items()}
print("DEBUG feed raw counts:", debug_feeds)

# Parse all feeds
dom = parse_rss("/tmp/news_domestic.xml")
wld = parse_rss("/tmp/news_world.xml")
ai  = parse_rss("/tmp/news_ai.xml")
food_major = parse_rss("/tmp/news_food_major.xml")
conf  = parse_rss("/tmp/news_confectionery.xml", mx=20)
choco = parse_rss("/tmp/news_chocolate.xml", mx=20)
# Search J-PlatPat for confectionery patents (菓子 broadly: チョコ/焼き菓子/和菓子 etc.)
patents = search_jplatpat("菓子 チョコレート", mx=5)
if not patents:
    print("J-PlatPat returned no results, trying parse_patents fallback...")
    patents = parse_patents("/tmp/patents.xml")

# De-duplicate food sub-categories
used = set(a["title"] for a in food_major)
conf  = [a for a in conf  if a["title"] not in used][:5]
used.update(a["title"] for a in conf)
choco = [a for a in choco if a["title"] not in used][:5]

# Fetch excerpts only for top 2 of main categories (token efficiency)
print("Fetching excerpts (main categories only)...")
for cat in [dom, wld, ai, food_major]:
    for a in cat[:2]:
        print(f"  {a['title'][:28]}")
        a["excerpt"] = fetch_excerpt(a["link"])
        print(f"  -> {len(a['excerpt'])}c" if a["excerpt"] else "  -> fail")

out = {"domestic":dom,"world":wld,"ai":ai,
       "food_major":food_major,"confectionery":conf,"chocolate":choco,
       "patents":patents,"markets":markets,
       "date":now.strftime("%Y-%m-%d"),
       "date_str":now.strftime("%Y年%m月%d日")+"("+days_ja[now.weekday()]+")",
       "time_str":now.strftime("%Y/%m/%d %H:%M")}
with open("/tmp/articles.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

print("\n=== Summary ===")
for lbl,items in [("国内",dom),("世界",wld),("AI",ai),
                  ("食品",food_major),("菓子",conf),("チョコ",choco)]:
    ex = sum(1 for a in items if a["excerpt"])
    print(f"  {lbl}: {len(items)}件 (excerpt:{ex})")
print(f"  特許: {len(patents)}件")
print(f"  合計: {len(dom)+len(wld)+len(ai)+len(food_major)+len(conf)+len(choco)}件")
