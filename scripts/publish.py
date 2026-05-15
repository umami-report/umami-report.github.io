import json, base64, urllib.request, os
import html as hl
TOKEN=os.environ.get("GITHUB_TOKEN","")
REPO="umami-report/umami-report.github.io"
with open("/tmp/articles.json",encoding="utf-8") as f: data=json.load(f)
today=data["date"]; date_str=data["date_str"]; time_str=data["time_str"]
dom=data["domestic"]; wld=data["world"]; ai=data["ai"]
food_major=data["food_major"]; conf=data["confectionery"]; choco=data["chocolate"]
patents=data.get("patents",[])
markets=data.get("markets",{})
def ghget(p):
    r=urllib.request.Request(f"https://api.github.com/repos/{REPO}/{p}",headers={"Authorization":f"token {TOKEN}","User-Agent":"py"})
    with urllib.request.urlopen(r) as x: return json.loads(x.read())
def ghput(p,b,m):
    sha=""
    try: sha=ghget(f"contents/{p}").get("sha","")
    except: pass
    body={"message":m,"content":base64.b64encode(b).decode()}
    if sha: body["sha"]=sha
    r=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{p}",data=json.dumps(body).encode(),method="PUT",headers={"Authorization":f"token {TOKEN}","User-Agent":"py","Content-Type":"application/json"})
    with urllib.request.urlopen(r) as x: return json.loads(x.read()).get("commit",{}).get("sha","?")[:8]
def mk_archive():
    try:
        cs=ghget("contents/")
        past=sorted([f["name"] for f in cs if len(f["name"])==15 and f["name"].endswith(".html") and f["name"][:4].isdigit()],reverse=True)
        links="".join([f'<a href="{n}" class="archive-link">{n[:-5]}</a>' for n in past])
        return f'<section class="archive-section" id="archive"><h2 class="section-label">ARCHIVE</h2><div class="archive-links">{links}</div></section>'
    except: return ""
def mk_cards(items,tag,color):
    if not items: return f'<p style="font-size:.82rem;color:#999;padding:8px 0">該当記事なし</p>'
    rows=[]
    for a in items:
        fav=f'<img src="{a["favicon"]}" class="card-favicon" alt="" loading="lazy">' if a.get("favicon") else ""
        rows.append(f'<article class="card"><a href="{hl.escape(a["link"])}" target="_blank" rel="noopener" class="card-link"><div class="card-tag" style="color:{color}">{tag}</div><h3 class="card-title">{hl.escape(a["title"])}</h3><div class="card-meta">{fav}<span>{hl.escape(a["source"])}</span></div></a></article>')
    return "".join(rows)
def mk_sparkline(prices, w=180, h=52):
    if not prices or len(prices)<2: return ""
    mn,mx=min(prices),max(prices)
    rng=mx-mn or 1
    pts=" ".join(f"{i/(len(prices)-1)*w:.1f},{h-2-((v-mn)/rng)*(h-4):.1f}" for i,v in enumerate(prices))
    up=prices[-1]>=prices[0]
    c="#16a34a" if up else "#dc2626"
    # fill area under line
    first_x="0"; last_x=f"{w:.1f}"
    first_y=f"{h-2-((prices[0]-mn)/rng)*(h-4):.1f}"; last_y=f"{h-2-((prices[-1]-mn)/rng)*(h-4):.1f}"
    fill_pts=f"0,{h} "+pts+f" {w},{h}"
    fc="#16a34a22" if up else "#dc262622"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block">'
            f'<polygon points="{fill_pts}" fill="{fc}"/>'
            f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
            f'</svg>')
def fmt_price(price,currency):
    if currency=="JPY": return f"¥{price:,.0f}"
    if currency=="GBP": return f"£{price:,.0f}"
    if currency=="USD": return f"${price:.2f}"
    return f"{price:,.2f}"
def mk_market_strip(mkt):
    defs=[("nikkei","日経平均","JPY","#1a1a2e"),("cocoa","カカオ (London GBP)","GBP","#92400e"),("orcan","MSCI ACWI","USD","#2563eb"),("silver","シルバー","USD","#6b7280")]
    cards=[]
    for key,label,def_cur,accent in defs:
        m=mkt.get(key) if mkt else None
        if not m: continue
        prices=m.get("prices",[]);price=m.get("price",0);chg=m.get("change_pct",0);cur=m.get("currency",def_cur)
        if m.get("_label"): label=m["_label"]  # override (e.g. NY cocoa fallback)
        fetched=m.get("fetched_at","")
        sign="+" if chg>=0 else ""; cc="#16a34a" if chg>=0 else "#dc2626"
        arrow="▲" if chg>=0 else "▼"
        cards.append(
            f'<div class="mkt-card">'
            f'<div class="mkt-label" style="color:{accent}">{label}</div>'
            f'<div class="mkt-price">{fmt_price(price,cur)}</div>'
            f'<div class="mkt-chg" style="color:{cc}">{arrow} {sign}{chg:.2f}%</div>'
            f'<div class="mkt-chart">{mk_sparkline(prices)}</div>'
            f'<div class="mkt-time">{fetched} JST</div>'
            f'</div>'
        )
    if not cards: return ""
    return f'<div class="mkt-strip" id="markets">{"".join(cards)}</div>'
def mk_patent_list(items):
    if not items: return '<p style="font-size:.82rem;color:#999;padding:8px 0">該当特許なし</p>'
    rows=[]
    for p in items:
        date_str2=f' ({p["date"]})' if p.get("date") else ""
        rows.append(f'<div class="patent-item"><a href="{hl.escape(p["link"])}" target="_blank" rel="noopener" class="patent-link">{hl.escape(p["title"])}</a><div class="patent-meta">J-PlatPat{date_str2}</div></div>')
    return f'<div class="patent-list">{"".join(rows)}</div>'
css="*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}:root{--black:#111;--charcoal:#333;--mid:#666;--light:#999;--border:#e5e5e5;--bg:#fff;--bg2:#f9f9f9}body{font-family:'Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN',sans-serif;background:var(--bg);color:var(--charcoal);line-height:1.7;font-size:15px}header{position:sticky;top:0;z-index:100;background:var(--bg);border-bottom:1px solid var(--border)}.header-inner{max-width:1100px;margin:0 auto;padding:0 24px;height:56px;display:flex;align-items:center;gap:24px}.logo{font-size:1.05rem;font-weight:800;letter-spacing:.12em;color:var(--black);text-decoration:none}.logo span{color:#dc2626}nav a{font-size:.68rem;font-weight:700;letter-spacing:.1em;color:var(--mid);text-decoration:none;padding:4px 12px}nav a:hover{color:var(--black)}.header-date{margin-left:auto;font-size:.68rem;color:var(--light)}.hero{background:var(--black);color:#fff;padding:44px 24px;text-align:center}.hero h1{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900;letter-spacing:.15em}.hero h1 span{color:#dc2626}.hero p{margin-top:10px;font-size:.75rem;color:rgba(255,255,255,.4);letter-spacing:.12em}.container{max-width:1100px;margin:0 auto;padding:52px 24px}.news-section{margin-bottom:60px}.section-header{display:flex;align-items:baseline;gap:14px;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid var(--black)}.section-label{font-size:.68rem;font-weight:800;letter-spacing:.15em;color:var(--black)}.section-count{font-size:.65rem;color:var(--light)}.bar{width:28px;height:3px;border-radius:2px;flex-shrink:0}.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1px;background:var(--border);border:1px solid var(--border)}.card{background:var(--bg);transition:background .15s}.card:hover{background:var(--bg2)}.card-link{display:flex;flex-direction:column;padding:18px 20px;height:100%;text-decoration:none;color:inherit}.card-tag{font-size:.63rem;font-weight:800;letter-spacing:.13em;margin-bottom:8px}.card-title{font-size:.86rem;font-weight:600;line-height:1.55;margin-bottom:auto;color:var(--black);flex:1}.card-link:hover .card-title{color:#dc2626}.card-meta{display:flex;align-items:center;gap:6px;margin-top:10px;font-size:.7rem;color:var(--light)}.card-favicon{width:14px;height:14px;border-radius:2px;object-fit:contain;flex-shrink:0}.food-sub{margin-bottom:24px}.food-sub-label{font-size:.65rem;font-weight:800;letter-spacing:.12em;color:var(--mid);padding:6px 0 8px;border-bottom:1px solid var(--border);margin-bottom:10px}.patent-list{display:flex;flex-direction:column;gap:6px;margin-top:4px}.patent-item{background:var(--bg);border:1px solid var(--border);padding:10px 14px;transition:background .15s}.patent-item:hover{background:var(--bg2)}.patent-link{font-size:.84rem;font-weight:500;color:var(--black);text-decoration:none;line-height:1.45;display:block}.patent-link:hover{color:#7c3aed}.patent-meta{font-size:.63rem;color:var(--light);margin-top:3px}.economy-wrapper{display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-bottom:60px}.archive-section{border-top:1px solid var(--border);padding-top:40px;margin-top:8px}.archive-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.archive-link{font-size:.7rem;font-weight:600;color:var(--charcoal);text-decoration:none;border:1px solid var(--border);padding:5px 12px;border-radius:2px;transition:all .15s}.archive-link:hover{background:var(--black);color:#fff;border-color:var(--black)}footer{border-top:1px solid var(--border);padding:28px 24px;text-align:center}footer p{font-size:.7rem;color:var(--light)}footer a{color:var(--charcoal);text-decoration:none}.mkt-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:48px}.mkt-card{background:var(--bg);padding:18px 20px 12px}.mkt-label{font-size:.6rem;font-weight:800;letter-spacing:.14em;margin-bottom:6px}.mkt-price{font-size:1.15rem;font-weight:800;color:var(--black);letter-spacing:-.02em;margin-bottom:2px}.mkt-chg{font-size:.72rem;font-weight:700;margin-bottom:10px}.mkt-chart{line-height:0;opacity:.9}.mkt-time{font-size:.6rem;color:var(--light);margin-top:5px}@media(max-width:900px){.mkt-strip{grid-template-columns:repeat(2,1fr)}}@media(max-width:768px){.economy-wrapper{grid-template-columns:1fr}.header-date{display:none}.mkt-strip{grid-template-columns:1fr}}@media(max-width:600px){.card-grid{grid-template-columns:1fr}.hero{padding:28px 16px}.container{padding:32px 16px}}"
arc=mk_archive()
mkt_strip=mk_market_strip(markets)
total_food=len(food_major)+len(conf)+len(choco)
total_pat=len(patents)
html=("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'>"
    f"<title>UMAMI REPORT | 食品・AI・経済ニュース</title><style>{css}</style></head><body>"
    "<header><div class='header-inner'><a href='/' class='logo'>UMAMI <span>REPORT</span></a>"
    "<nav><a href='#markets'>MARKET</a><a href='#economy'>ECONOMY</a><a href='#ai'>AI</a><a href='#food'>FOOD</a><a href='#patents'>PATENT</a><a href='#archive'>ARCHIVE</a></nav>"
    f"<span class='header-date'>{date_str}</span></div></header>"
    "<div class='hero'><h1>UMAMI <span>REPORT</span></h1><p>FOOD &middot; AI &middot; ECONOMY &middot; DAILY DIGEST</p></div>"
    "<div class='container'>"
    f"{mkt_strip}"
    "<div class='economy-wrapper' id='economy'>"
    f"<div class='economy-col'><div class='section-header'><div class='bar' style='background:#1a1a2e'></div><h2 class='section-label'>DOMESTIC - 国内主要経済</h2><span class='section-count'>{len(dom)} STORIES</span></div><div class='card-grid'>{mk_cards(dom,'DOMESTIC','#1a1a2e')}</div></div>"
    f"<div class='economy-col'><div class='section-header'><div class='bar' style='background:#374151'></div><h2 class='section-label'>GLOBAL - 世界経済</h2><span class='section-count'>{len(wld)} STORIES</span></div><div class='card-grid'>{mk_cards(wld,'GLOBAL','#374151')}</div></div>"
    "</div>"
    f"<section class='news-section' id='ai'><div class='section-header'><div class='bar' style='background:#2563eb'></div><h2 class='section-label'>AI &amp; TECHNOLOGY - 最新動向</h2><span class='section-count'>{len(ai)} STORIES</span></div><div class='card-grid'>{mk_cards(ai,'AI','#2563eb')}</div></section>"
    f"<section class='news-section' id='food'><div class='section-header'><div class='bar' style='background:#dc2626'></div><h2 class='section-label'>FOOD INDUSTRY - 食品業界ニュース</h2><span class='section-count'>{total_food} STORIES</span></div>"
    f"<div class='food-sub'><div class='food-sub-label'>MAJOR TOPICS - 業界全体</div><div class='card-grid'>{mk_cards(food_major,'FOOD','#dc2626')}</div></div>"
    f"<div class='food-sub'><div class='food-sub-label'>CONFECTIONERY - 菓子業界 新製品・トレンド</div><div class='card-grid'>{mk_cards(conf,'SWEETS','#b45309')}</div></div>"
    f"<div class='food-sub'><div class='food-sub-label'>CHOCOLATE - チョコレート</div><div class='card-grid'>{mk_cards(choco,'CHOCO','#92400e')}</div></div>"
    "</section>"
    f"<section class='news-section' id='patents'><div class='section-header'><div class='bar' style='background:#7c3aed'></div><h2 class='section-label'>PATENT - 菓子関連特許 (J-PlatPat)</h2><span class='section-count'>{total_pat} PATENTS (30日以内)</span></div>"
    f"{mk_patent_list(patents)}</section>"
    f"{arc}</div>"
    f"<footer><div><p>Auto-generated by Claude - 最終更新: {time_str} JST</p></div></footer>"
    "</body></html>")
with open("/tmp/index.html","w",encoding="utf-8") as f: f.write(html)
with open(f"/tmp/{today}.html","w",encoding="utf-8") as f: f.write(html)
uploads=[("index.html","/tmp/index.html",f"Daily digest {today}"),(f"{today}.html",f"/tmp/{today}.html",f"Archive {today}")]
if os.path.exists("/tmp/debug_run.txt"):
    uploads.append(("debug.txt","/tmp/debug_run.txt",f"Debug {today}"))
for path,fp,msg in uploads:
    with open(fp,"rb") as f: c=f.read()
    print(f"{path}:", ghput(path,c,msg))
print("Done!")
