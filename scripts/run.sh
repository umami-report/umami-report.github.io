#!/bin/bash
set -e
echo "Fetching RSS feeds..."

# Economy
curl -sL 'https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%E7%B5%8C%E6%B8%88+%E5%9B%BD%E5%86%85+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_domestic.xml
curl -sL 'https://news.google.com/rss/search?q=%E4%B8%96%E7%95%8C%E7%B5%8C%E6%B8%88+%E3%82%B0%E3%83%AD%E3%83%BC%E3%83%90%E3%83%AB+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_world.xml
curl -sL 'https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD+AI+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_ai.xml

# Food major (industry-wide topics)
curl -sL 'https://news.google.com/rss/search?q=%E9%A3%9F%E5%93%81%E6%A5%AD%E7%95%8C+%E5%B8%82%E5%A0%B4+%E5%8B%95%E5%90%91+%E4%BC%81%E6%A5%AD&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_food_major.xml

# Confectionery (new products, openings, trends)
curl -sL 'https://news.google.com/rss/search?q=%E8%8F%93%E5%AD%90+%E6%96%B0%E5%95%86%E5%93%81+%E3%82%B9%E3%82%A4%E3%83%BC%E3%83%84+%E6%96%B0%E7%99%BA%E5%A3%B2+%E6%96%B0%E5%BA%97&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_confectionery.xml

# Chocolate
curl -sL 'https://news.google.com/rss/search?q=%E3%83%81%E3%83%A7%E3%82%B3%E3%83%AC%E3%83%BC%E3%83%88+%E6%96%B0%E5%95%86%E5%93%81+%E6%96%B0%E7%99%BA%E5%A3%B2+%E3%83%88%E3%83%AC%E3%83%B3%E3%83%89&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_chocolate.xml

# Patents (chocolate + fat-based confectionery)
curl -sL 'https://patents.google.com/rss?q=%E3%83%81%E3%83%A7%E3%82%B3%E3%83%AC%E3%83%BC%E3%83%88+%E6%B2%B9%E6%80%A7%E8%8F%93%E5%AD%90&hl=ja&num=10' > /tmp/patents.xml 2>/dev/null \
  || printf '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>' > /tmp/patents.xml

pip install edge-tts -q
python3 scripts/parse.py
echo "=== DONE ==="
