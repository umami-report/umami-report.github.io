import xml.etree.ElementTree as ET, json, re, urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
cutoff = now - timedelta(days=30)
days_ja = "月火水木金土日"

def fetch_excerpt(url, chars=600):
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
    except Exception as e:
        return ""

def parse_rss(fp, mx=10):
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
                    if dt<cutoff: continue
                    pub=dt.astimezone(JST).strftime("%m/%d %H:%M")
                except: pass
            raw=t.text or ""; src=s.text if s is not None else ""
            surl=s.get("url","") if s is not None else ""
            link=l.text or "#" if l is not None else "#"
            clean=raw
            if src and clean.endswith(" - "+src): clean=clean[:-len(" - "+src)].strip()
            clean=re.sub(r"[]【】《》[〔〕]","",clean).strip()
            fav="https://www.google.com/s2/favicons?domain="+surl+"&sz=64" if surl else ""
            items.append({"title":clean,"raw":raw,"source":src,"source_url":surl,"link":link,"date":pub,"favicon":fav,"excerpt":""})
            if len(items)>=mx: break
    except Exception as e: print("err",fp,e)
    return items

dom=parse_rss("/tmp/news_domestic.xml",5)
wld=parse_rss("/tmp/news_world.xml",5)
ai=parse_rss("/tmp/news_ai.xml",5)
f1=parse_rss("/tmp/news_food1.xml",6)
f2=parse_rss("/tmp/news_food2.xml",4)
seen=set(); food=[]
for x in f1+f2:
    if x["title"] not in seen: seen.add(x["title"]); food.append(x)
food=food[:10]

print("=== 記事本文取得中（各カテゴリ上位2件）===")
for cat_items in [dom,wld,ai,food]:
    for a in cat_items[:2]:
        print(f"  取得: {a['title'][:30]}")
        a["excerpt"]=fetch_excerpt(a["link"])
        print(f"  -> {len(a['excerpt'])}文字" if a["excerpt"] else "  -> 取得失敗")

out={"domestic":dom,"world":wld,"ai":ai,"food":food,
     "date":now.strftime("%Y-%m-%d"),
     "date_str":now.strftime("%Y年%m月%d日")+"("+days_ja[now.weekday()]+")",
     "time_str":now.strftime("%Y/%m/%d %H:%M")}
with open("/tmp/articles.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
print("=== 記事一覧 ===")
for cat,items in [("国内経済",dom),("世界経済",wld),("AIテクノロジー",ai),("食品業界",food)]:
    print(f"\n【{cat}】{len(items)}件")
    for i,a in enumerate(items,1):
        ex=f" [本文{len(a['excerpt'])}字]" if a["excerpt"] else ""
        print(f"  {i}. {a['title']} ({a['source']}){ex}")
print(f"\n合計: {len(dom)+len(wld)+len(ai)+len(food)}件")
