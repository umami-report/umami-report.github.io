#!/bin/bash
echo "Fetching RSS feeds..."

TMPD="${NEWS_TMP:-/tmp}"
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
BASE='https://news.google.com/rss/search'

fetch_news() {
  curl -sLk --max-time 20 -A "$UA" -G "$BASE" \
    --data-urlencode 'hl=ja' --data-urlencode 'gl=JP' --data-urlencode 'ceid=JP:ja' \
    --data-urlencode "q=$1" > "$2" || true
}

# カテゴリ別クエリ。クエリで絞り切れない分は parse.py 側のキーワードフィルタで除去する
fetch_news '"日本経済" OR 日銀 OR 東証 OR 国内景気 OR 円相場 when:7d' "$TMPD/news_domestic.xml"
fetch_news '世界経済 OR 国際金融 OR 米経済 OR 欧州経済 OR 中国経済 when:7d' "$TMPD/news_world.xml"
fetch_news 'AI 人工知能 テクノロジー when:7d' "$TMPD/news_ai.xml"
fetch_news '食品業界 OR 食品メーカー when:7d' "$TMPD/news_food_major.xml"
fetch_news 'スイーツ OR 菓子 新商品 when:7d' "$TMPD/news_confectionery.xml"
fetch_news 'チョコレート OR ショコラ OR カカオ when:7d' "$TMPD/news_chocolate.xml"

# Debug: write feed sizes and item counts to log
{
  echo "=== RSS Fetch Debug $(date -u) ==="
  for f in news_domestic news_world news_ai news_food_major news_confectionery news_chocolate; do
    sz=$(wc -c < "$TMPD/${f}.xml" 2>/dev/null || echo "missing")
    echo "${f}: size=${sz}"
  done
} > "$TMPD/debug_run.txt"

echo "Feed item counts:"
for f in news_domestic news_world news_ai news_food_major news_confectionery news_chocolate; do
  count=$(python3 -c "import xml.etree.ElementTree as ET; root=ET.parse('${TMPD}/${f}.xml').getroot(); ch=root.find('channel'); print(len(ch.findall('item')) if ch else 0)" 2>/dev/null || echo "parse-err")
  echo "  $f: $count"
  echo "  $f: $count" >> "$TMPD/debug_run.txt"
done

python3 scripts/parse.py
echo "=== DONE ==="
