#!/bin/bash
echo "Fetching RSS feeds..."

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
fetch() { curl -sLk --max-time 20 -A "$UA" "$@"; }

# All feeds via Google News (globally accessible CDN, not geo-restricted)
BASE='https://news.google.com/rss/search?hl=ja&gl=JP&ceid=JP:ja&q='

fetch "${BASE}%E6%97%A5%E6%9C%AC+%E7%B5%8C%E6%B8%88+%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%B9+when%3A7d" > /tmp/news_domestic.xml || true
fetch "${BASE}%E4%B8%96%E7%95%8C+%E7%B5%8C%E6%B8%88+%E5%9B%BD%E9%9A%9B+when%3A7d" > /tmp/news_world.xml || true
fetch "${BASE}AI+%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD+%E3%83%86%E3%82%AF%E3%83%8E%E3%83%AD%E3%82%B8%E3%83%BC+when%3A7d" > /tmp/news_ai.xml || true
fetch "${BASE}%E9%A3%9F%E5%93%81%E6%A5%AD%E7%95%8C+%E5%B8%82%E5%A0%B4+%E5%8B%95%E5%90%91+%E4%BC%81%E6%A5%AD+when%3A7d" > /tmp/news_food_major.xml || true
fetch "${BASE}%E8%8F%93%E5%AD%90+%E3%82%B9%E3%82%A4%E3%83%BC%E3%83%84+when%3A7d" > /tmp/news_confectionery.xml || true
fetch "${BASE}%E3%83%81%E3%83%A7%E3%82%B3%E3%83%AC%E3%83%BC%E3%83%88+%E6%96%B0%E5%95%86%E5%93%81+%E6%96%B0%E7%99%BA%E5%A3%B2+%E3%83%88%E3%83%AC%E3%83%B3%E3%83%89+when%3A7d" > /tmp/news_chocolate.xml || true

# Fallback empty XML for patents
printf '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>' > /tmp/patents.xml

# Debug: write feed sizes and first 300 bytes to log
{
  echo "=== RSS Fetch Debug $(date -u) ==="
  for f in news_domestic news_world news_ai news_food_major news_confectionery news_chocolate; do
    sz=$(wc -c < /tmp/${f}.xml 2>/dev/null || echo "missing")
    first=$(head -c 300 /tmp/${f}.xml 2>/dev/null | tr '\n' ' ')
    echo "${f}: size=${sz}"
    echo "  first300: ${first}"
  done
} > /tmp/debug_run.txt

echo "Feed item counts:"
for f in news_domestic news_world news_ai news_food_major news_confectionery news_chocolate; do
  count=$(python3 -c "import xml.etree.ElementTree as ET; root=ET.parse('/tmp/${f}.xml').getroot(); ch=root.find('channel'); print(len(ch.findall('item')) if ch else 0)" 2>/dev/null || echo "parse-err")
  echo "  $f: $count"
  echo "  $f: $count" >> /tmp/debug_run.txt
done

pip install playwright -q
python3 -m playwright install chromium --with-deps -q 2>/dev/null || true
python3 scripts/parse.py
echo "=== DONE ==="
