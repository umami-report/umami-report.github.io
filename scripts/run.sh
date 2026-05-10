#!/bin/bash
set -e
echo "Fetching RSS feeds..."

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

# Economy - NHK (reliable from server IPs)
curl -sL 'https://www.nhk.or.jp/rss/news/cat4.xml' > /tmp/news_domestic.xml
curl -sL 'https://www.nhk.or.jp/rss/news/cat5.xml' > /tmp/news_world.xml

# AI/Technology - Yahoo Japan IT
curl -sL 'https://news.yahoo.co.jp/rss/topics/it.xml' > /tmp/news_ai.xml

# Food major (industry-wide topics) - Google News with browser UA
curl -sL -A "$UA" 'https://news.google.com/rss/search?q=%E9%A3%9F%E5%93%81%E6%A5%AD%E7%95%8C+%E5%B8%82%E5%A0%B4+%E5%8B%95%E5%90%91+%E4%BC%81%E6%A5%AD+when%3A7d&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_food_major.xml

# Confectionery - Google News with browser UA
curl -sL -A "$UA" 'https://news.google.com/rss/search?q=%E8%8F%93%E5%AD%90+%E6%96%B0%E5%95%86%E5%93%81+%E3%82%B9%E3%82%A4%E3%83%BC%E3%83%84+%E6%96%B0%E7%99%BA%E5%A3%B2+%E6%96%B0%E5%BA%97+when%3A7d&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_confectionery.xml

# Chocolate - Google News with browser UA
curl -sL -A "$UA" 'https://news.google.com/rss/search?q=%E3%83%81%E3%83%A7%E3%82%B3%E3%83%AC%E3%83%BC%E3%83%88+%E6%96%B0%E5%95%86%E5%93%81+%E6%96%B0%E7%99%BA%E5%A3%B2+%E3%83%88%E3%83%AC%E3%83%B3%E3%83%89+when%3A7d&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_chocolate.xml

# Patents (chocolate + fat-based confectionery)
curl -sL -A "$UA" 'https://patents.google.com/rss?q=%E3%83%81%E3%83%A7%E3%82%B3%E3%83%AC%E3%83%BC%E3%83%88+%E6%B2%B9%E6%80%A7%E8%8F%93%E5%AD%90&hl=ja&num=10' > /tmp/patents.xml 2>/dev/null \
  || printf '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>' > /tmp/patents.xml

# Debug: count items in each feed
echo "Feed item counts:"
for f in news_domestic news_world news_ai news_food_major news_confectionery news_chocolate; do
  count=$(python3 -c "import xml.etree.ElementTree as ET; root=ET.parse('/tmp/${f}.xml').getroot(); ch=root.find('channel'); print(len(ch.findall('item')) if ch else 0)" 2>/dev/null || echo "err")
  echo "  $f: $count"
done

pip install edge-tts playwright -q
apt-get install -y ffmpeg -qq 2>/dev/null || true
python3 -m playwright install chromium --with-deps -q 2>/dev/null || true
python3 scripts/parse.py
echo "=== DONE ==="
