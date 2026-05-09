import json, base64, urllib.request, os, asyncio
import html as hl
import edge_tts
TOKEN=os.environ.get("GITHUB_TOKEN","")
REPO="umami-report/umami-report.github.io"
with open("/tmp/articles.json",encoding="utf-8") as f: data=json.load(f)
with open("/tmp/script.txt",encoding="utf-8") as f: script=f.read()
today=data["date"]; date_str=data["date_str"]; time_str=data["time_str"]
dom=data["domestic"]; wld=data["world"]; ai=data["ai"]; food=data["food"]
print("Script chars:",len(script))
mp3=f"/tmp/{today}.mp3"
print("Generating audio...")
async def go():
    await edge_tts.Communicate(script,"ja-JP-NanamiNeural").save(mp3)
asyncio.run(go())
print("MP3:",os.path.getsize(mp3)//1024,"KB")
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
    if not items: return f'<div class="card"><div class="card-tag" style="color:{color}">{tag}</div><p style="font-size:.85rem;color:#999;padding:8px 0">該当記事なし</p></div>'
    rows=[]
    for a in items:
        fav=f'<img src="{a["favicon"]}" class="card-favicon" alt="" loading="lazy">' if a.get("favicon") else ""
        rows.append(f'<article class="card"><a href="{hl.escape(a["link"])}" target="_blank" rel="noopener" class="card-link"><div class="card-tag" style="color:{color}">{tag}</div><h3 class="card-title">{hl.escape(a["title"])}</h3><div class="card-meta">{fav}<span>{hl.escape(a["source"])}</span></div></a></article>')
    return "".join(rows)
css="*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}:root{--black:#111;--charcoal:#333;--mid:#666;--light:#999;--border:#e5e5e5;--bg:#fff;--bg2:#f9f9f9}body{font-family:'Helvetica Neue',Arial,'Hiragino Kaku Gothic ProN',sans-serif;background:var(--bg);color:var(--charcoal);line-height:1.7;font-size:15px}header{position:sticky;top:0;z-index:100;background:var(--bg);border-bottom:1px solid var(--border)}.header-inner{max-width:1100px;margin:0 auto;padding:0 24px;height:56px;display:flex;align-items:center;gap:24px}.logo{font-size:1.05rem;font-weight:800;letter-spacing:.12em;color:var(--black);text-decoration:none}.logo span{color:#dc2626}nav a{font-size:.68rem;font-weight:700;letter-spacing:.1em;color:var(--mid);text-decoration:none;padding:4px 12px}nav a:hover{color:var(--black)}.header-date{margin-left:auto;font-size:.68rem;color:var(--light)}.hero{background:var(--black);color:#fff;padding:44px 24px;text-align:center}.hero h1{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900;letter-spacing:.15em}.hero h1 span{color:#dc2626}.hero p{margin-top:10px;font-size:.75rem;color:rgba(255,255,255,.4);letter-spacing:.12em}.podcast-bar{background:#f0f0f0;border-bottom:1px solid var(--border);padding:16px 24px}.podcast-inner{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}.podcast-label{font-size:.68rem;font-weight:800;letter-spacing:.12em;color:var(--black);white-space:nowrap}.podcast-player{flex:1;min-width:200px}.podcast-player audio{width:100%;height:36px}.podcast-note{font-size:.65rem;color:var(--light)}.container{max-width:1100px;margin:0 auto;padding:52px 24px}.news-section{margin-bottom:60px}.section-header{display:flex;align-items:baseline;gap:14px;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid var(--black)}.section-label{font-size:.68rem;font-weight:800;letter-spacing:.15em;color:var(--black)}.section-count{font-size:.65rem;color:var(--light)}.bar{width:28px;height:3px;border-radius:2px;flex-shrink:0}.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1px;background:var(--border);border:1px solid var(--border)}.card{background:var(--bg);transition:background .15s}.card:hover{background:var(--bg2)}.card-link{display:flex;flex-direction:column;padding:20px 22px;height:100%;text-decoration:none;color:inherit}.card-tag{font-size:.63rem;font-weight:800;letter-spacing:.13em;margin-bottom:8px}.card-title{font-size:.88rem;font-weight:600;line-height:1.55;margin-bottom:auto;color:var(--black);flex:1}.card-link:hover .card-title{color:#dc2626}.card-meta{display:flex;align-items:center;gap:6px;margin-top:12px;font-size:.7rem;color:var(--light)}.card-favicon{width:14px;height:14px;border-radius:2px;object-fit:contain;flex-shrink:0}.economy-wrapper{display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-bottom:60px}.archive-section{border-top:1px solid var(--border);padding-top:40px;margin-top:8px}.archive-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.archive-link{font-size:.7rem;font-weight:600;color:var(--charcoal);text-decoration:none;border:1px solid var(--border);padding:5px 12px;border-radius:2px;transition:all .15s}.archive-link:hover{background:var(--black);color:#fff;border-color:var(--black)}footer{border-top:1px solid var(--border);padding:28px 24px;text-align:center}footer p{font-size:.7rem;color:var(--light)}footer a{color:var(--charcoal);text-decoration:none}@media(max-width:768px){.economy-wrapper{grid-template-columns:1fr}.header-date{display:none}}@media(max-width:600px){.card-grid{grid-template-columns:1fr}.hero{padding:28px 16px}.container{padding:32px 16px}}"
arc=mk_archive()
html=("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'>"
    f"<title>UMAMI REPORT | 食品・AI・経済ニュース</title><style>{css}</style></head><body>"
    "<header><div class='header-inner'><a href='/' class='logo'>UMAMI <span>REPORT</span></a>"
    "<nav><a href='#economy'>ECONOMY</a><a href='#ai'>AI</a><a href='#food'>FOOD</a><a href='#archive'>ARCHIVE</a></nav>"
    f"<span class='header-date'>{date_str}</span></div></header>"
    "<div class='hero'><h1>UMAMI <span>REPORT</span></h1><p>FOOD &middot; AI &middot; ECONOMY &middot; DAILY DIGEST</p></div>"
    "<div class='podcast-bar'><div class='podcast-inner'><span class='podcast-label'>PODCAST</span>"
    f"<div class='podcast-player'><audio controls preload='none'><source src='audio/{today}.mp3' type='audio/mpeg'>再生非対応</audio></div>"
    f"<span class='podcast-note'>Claude要約 x Nanami - {date_str}</span></div></div>"
    "<div class='container'><div class='economy-wrapper' id='economy'>"
    f"<div class='economy-col'><div class='section-header'><div class='bar' style='background:#1a1a2e'></div><h2 class='section-label'>DOMESTIC - 国内主要経済</h2><span class='section-count'>{len(dom)} STORIES</span></div><div class='card-grid'>{mk_cards(dom,'DOMESTIC','#1a1a2e')}</div></div>"
    f"<div class='economy-col'><div class='section-header'><div class='bar' style='background:#374151'></div><h2 class='section-label'>GLOBAL - 世界経済</h2><span class='section-count'>{len(wld)} STORIES</span></div><div class='card-grid'>{mk_cards(wld,'GLOBAL','#374151')}</div></div>"
    "</div>"
    f"<section class='news-section' id='ai'><div class='section-header'><div class='bar' style='background:#2563eb'></div><h2 class='section-label'>AI &amp; TECHNOLOGY - 最新動向</h2><span class='section-count'>{len(ai)} STORIES</span></div><div class='card-grid'>{mk_cards(ai,'AI','#2563eb')}</div></section>"
    f"<section class='news-section' id='food'><div class='section-header'><div class='bar' style='background:#dc2626'></div><h2 class='section-label'>FOOD INDUSTRY - 食品業界ニュース</h2><span class='section-count'>{len(food)} STORIES</span></div><div class='card-grid'>{mk_cards(food,'FOOD','#dc2626')}</div></section>"
    f"{arc}</div><footer><div><p>Auto-generated by Claude - 最終更新: {time_str} JST</p></div></footer></body></html>")
with open("/tmp/index.html","w",encoding="utf-8") as f: f.write(html)
with open(f"/tmp/{today}.html","w",encoding="utf-8") as f: f.write(html)
for path,fp,msg in [("index.html","/tmp/index.html",f"Daily digest {today}"),(f"{today}.html",f"/tmp/{today}.html",f"Archive {today}"),(f"audio/{today}.mp3",mp3,f"Podcast {today}")]:
    with open(fp,"rb") as f: c=f.read()
    print(f"{path}:", ghput(path,c,msg))
print("Done!")
