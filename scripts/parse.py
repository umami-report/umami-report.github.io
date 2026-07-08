import xml.etree.ElementTree as ET, json, re, urllib.request, ssl, csv, io, os, unicodedata
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Bypass SSL verification (CCR environment uses SSL inspection with self-signed certs)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

TMP = os.environ.get("NEWS_TMP", "/tmp")
JST = timezone(timedelta(hours=9))
now = datetime.now(timezone.utc).astimezone(JST)
cutoff = now - timedelta(days=14)
days_ja = "月火水木金土日"

# 市場調査レポートの宣伝・株価データページ・クチコミページなど、全カテゴリ共通で除外するノイズ
SPAM = re.compile(r"市場規模|分析レポート|調査レポート|市場調査|世界市場|グローバル市場|レポートを発表|リサーチ会社"
                  r"|株価・株式情報|クチコミ\d*件|経済指標|写真・画像")

def norm_title(t):
    """タイトルの表記ゆれ（全角/半角・空白・記号）を吸収して重複判定用キーを作る"""
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"[\W_]", "", t).lower()

def bigrams(s):
    return {s[i:i+2] for i in range(len(s)-1)}

def similar(a, b, threshold=0.45):
    """タイトルの文字バイグラム重複率で同一トピックの言い換え記事を検出する"""
    A, B = bigrams(a), bigrams(b)
    if not A or not B: return a == b
    return len(A & B) / min(len(A), len(B)) > threshold

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

def parse_rss(fp, mx=5, require=None, exclude=None):
    """RSSを読み、ゴミタイトル除去・カテゴリフィルタ・重複除去をかけて日付降順の上位 mx 件を返す。
    require: タイトルが必ずマッチすべき正規表現 / exclude: マッチしたら除外する正規表現"""
    items = []
    seen = set()
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
            # 末尾の「（配信元名）」を除去（Yahoo!ニュース転載などで同一記事が別タイトルになるのを防ぐ）
            clean=re.sub(r"[\s　]*[（(][^（()）]{2,25}[)）]\s*$","",clean).strip()
            # ゴミタイトル除去: メールアドレス・極端に短いもの・「〜た。」等の文（機械翻訳系メディアに多い）
            if "@" in clean: continue
            if len(clean) < 8: continue
            if clean.endswith("。"): continue
            if SPAM.search(clean): continue
            if require and not re.search(require, clean): continue
            if exclude and re.search(exclude, clean): continue
            key = norm_title(clean)
            if key in seen: continue
            seen.add(key)
            fav="https://www.google.com/s2/favicons?domain="+surl+"&sz=64" if surl else ""
            items.append({"title":clean,"raw":raw,"source":src,"source_url":surl,
                          "link":link,"date":pub,"favicon":fav,"excerpt":"","_dt":dt_sort,"_key":key})
        # 日付降順に並べ、言い換え重複と同一ソース偏りを避けながら上位 mx 件を選ぶ
        items.sort(key=lambda x: x["_dt"], reverse=True)
        picked=[]; src_count={}
        for a in items:
            if src_count.get(a["source"],0) >= 2: continue
            if any(similar(a["_key"], p["_key"]) for p in picked): continue
            picked.append(a)
            src_count[a["source"]] = src_count.get(a["source"],0)+1
            if len(picked) >= mx: break
        items = picked
        for a in items:
            del a["_dt"]; del a["_key"]
    except Exception as e: print("err",fp,e)
    return items

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
        sz = os.path.getsize(fp)
        root = ET.parse(fp).getroot(); ch = root.find("channel")
        cnt = len(ch.findall("item")) if ch else 0
        return {"size": sz, "items": cnt}
    except Exception as e:
        return {"size": 0, "items": 0, "err": str(e)}

debug_feeds = {k: raw_count(f"{TMP}/news_{v}.xml") for k,v in {
    "domestic": "domestic",
    "world": "world",
    "ai": "ai",
    "food_major": "food_major",
    "conf": "confectionery",
    "choco": "chocolate",
}.items()}
print("DEBUG feed raw counts:", debug_feeds)

# Parse all feeds
# 国内経済: 海外市場・海外企業単独の話題を除外
dom = parse_rss(f"{TMP}/news_domestic.xml",
                exclude=r"米企業|米国株|米株|NYダウ|ナスダック|ウォール街|韓国|中国経済|中国株|欧州経済|欧州株|FRB|ECB|台湾|インド")
wld = parse_rss(f"{TMP}/news_world.xml")
ai  = parse_rss(f"{TMP}/news_ai.xml")
# 食品業界: 業界・企業動向に限定（個別スイーツ紹介・飲食店プロモはCONFECTIONERYや対象外へ）
food_major = parse_rss(f"{TMP}/news_food_major.xml",
                       exclude=r"スイーツ|フィナンシェ|パフェ|ケーキ|クレープ|かき氷|食べ放題|飲み放題|クーポン|福袋")
# チョコレート: タイトルにチョコ関連語を必須にする（カカオトーク=韓国アプリは除外）
choco = parse_rss(f"{TMP}/news_chocolate.xml", mx=30,
                  require=r"チョコ|ショコラ|カカオ|ガトー",
                  exclude=r"カカオトーク")
# 菓子・スイーツ: スイーツ関連語を必須、チョコ系はCHOCOLATE欄に譲る
conf  = parse_rss(f"{TMP}/news_confectionery.xml", mx=30,
                  require=r"菓子|スイーツ|ケーキ|クッキー|ビスケット|アイス|デザート|パフェ|プリン|ドーナツ|タルト|マカロン|大福|饅頭|羊羹|パンケーキ",
                  exclude=r"チョコ|ショコラ")

# De-duplicate across food sub-categories (表記ゆれを吸収して比較)
used = set(norm_title(a["title"]) for a in food_major)
choco = [a for a in choco if norm_title(a["title"]) not in used][:5]
used.update(norm_title(a["title"]) for a in choco)
conf  = [a for a in conf  if norm_title(a["title"]) not in used][:5]

# Fetch excerpts only for top 2 of main categories (token efficiency)
print("Fetching excerpts (main categories only)...")
for cat in [dom, wld, ai, food_major]:
    for a in cat[:2]:
        print(f"  {a['title'][:28]}")
        a["excerpt"] = fetch_excerpt(a["link"])
        print(f"  -> {len(a['excerpt'])}c" if a["excerpt"] else "  -> fail")

out = {"domestic":dom,"world":wld,"ai":ai,
       "food_major":food_major,"confectionery":conf,"chocolate":choco,
       "markets":markets,
       "date":now.strftime("%Y-%m-%d"),
       "date_str":now.strftime("%Y年%m月%d日")+"("+days_ja[now.weekday()]+")",
       "time_str":now.strftime("%Y/%m/%d %H:%M")}
with open(f"{TMP}/articles.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

print("\n=== Summary ===")
for lbl,items in [("国内",dom),("世界",wld),("AI",ai),
                  ("食品",food_major),("菓子",conf),("チョコ",choco)]:
    ex = sum(1 for a in items if a["excerpt"])
    print(f"  {lbl}: {len(items)}件 (excerpt:{ex})")
print(f"  合計: {len(dom)+len(wld)+len(ai)+len(food_major)+len(conf)+len(choco)}件")
