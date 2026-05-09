import xml.etree.ElementTree as ET, json, re, urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
cutoff = now - timedelta(days=30)
days_ja = "月火水木金土日"

def fetch_excerpt(url, chars=500):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
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
            if not t: continue
            pub=""
            if p is not None and p.text:
                try:
                    dt=parsedate_to_datetime(p.text)
                    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                    if dt.astimezone(JST) < cutoff: continue
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
                          "link":link,"date":pub,"favicon":fav,"excerpt":""})
            if len(items)>=mx: break
    except Exception as e: print("err",fp,e)
    return items

def parse_patents(fp, mx=3):
    patents = []
    try:
        root = ET.parse(fp).getroot()
        ch = root.find("channel")
        if not ch: return patents
        for it in ch.findall("item"):
            t=it.find("title"); l=it.find("link"); p=it.find("pubDate")
            if not t: continue
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

# Parse all feeds
dom = parse_rss("/tmp/news_domestic.xml")
wld = parse_rss("/tmp/news_world.xml")
ai  = parse_rss("/tmp/news_ai.xml")
food_major = parse_rss("/tmp/news_food_major.xml")
conf  = parse_rss("/tmp/news_confectionery.xml")
choco = parse_rss("/tmp/news_chocolate.xml")
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
       "patents":patents,
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
