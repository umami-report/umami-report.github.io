#!/bin/bash
# Umami Report - Daily News Digest Generator
set -e

# STEP 1: Fetch RSS feeds
curl -sL 'https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%E7%B5%8C%E6%B8%88+%E5%9B%BD%E5%86%85+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_domestic.xml
curl -sL 'https://news.google.com/rss/search?q=%E4%B8%96%E7%95%8C%E7%B5%8C%E6%B8%88+%E3%82%B0%E3%83%AD%E3%83%BC%E3%83%90%E3%83%AB+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_world.xml
curl -sL 'https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD+AI+%E6%9C%80%E6%96%B0&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_ai.xml
curl -sL 'https://news.google.com/rss/search?q=%E9%A3%9F%E5%93%81+%E6%96%B0%E8%A3%BD%E5%93%81+%E3%83%88%E3%83%AC%E3%83%B3%E3%83%89&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_food1.xml
curl -sL 'https://news.google.com/rss/search?q=%E9%A3%9F%E5%93%81%E6%A5%AD%E7%95%8C+%E4%BC%81%E6%A5%AD+%E5%8B%95%E5%90%91&hl=ja&gl=JP&ceid=JP:ja' > /tmp/news_food2.xml
pip install edge-tts -q

# STEP 2: Parse articles and fetch excerpts
python3 scripts/parse.py

echo "=== STEP 2 DONE: articles.json created ==="
