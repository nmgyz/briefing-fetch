#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 GitHub Actions 海外 runner 上抓取境外 RSS，输出 data/news.json。

本地简报系统通过 GitHub API 读取结果，即可不挂 VPN 获取外媒一手消息。
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# 最大最权威的境外新闻源（海外 runner 可直连）
SOURCES = [
    ("BBC中文", "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Google News", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"),
    ("卫报", "https://www.theguardian.com/world/rss"),
    ("CNN", "https://rss.cnn.com/rss/edition_world.rss"),
    ("纽约时报", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("半岛电视台", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("德国之声", "https://rss.dw.com/rdf/rss-en-top"),
    ("France24", "https://www.france24.com/en/rss"),
    # 路透官方 RSS 已停用，改用 Google News 站点搜索中转（内容均来自 reuters.com）
    ("路透", "https://news.google.com/rss/search?q=site:reuters.com&hl=en-US&gl=US&ceid=US:en"),
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def fetch():
    items = []
    for name, url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read().decode("utf-8", "ignore")
            raw = re.sub(r"^\s*<\?xml[^>]*\?>", "", raw.strip())
            root = ET.fromstring(raw)
            cnt = 0
            for it in root.iter("item"):
                title = strip_tags(it.findtext("title") or "")
                desc = strip_tags(it.findtext("description") or "")
                link = (it.findtext("link") or "").strip()
                pub = (it.findtext("pubDate") or "").strip()
                if not title:
                    continue
                # 清理「标题 - 来源」后缀（BBC/NYT 习惯带 " - BBC News"）
                title = re.sub(r"\s*[-|–—]\s*[^-|–—]{2,20}$", "", title).strip() or title
                items.append({"title": title, "desc": desc, "link": link,
                              "pub": pub, "source": name})
                cnt += 1
            print("OK   %s: %d" % (name, cnt))
        except Exception as e:
            print("FAIL %s: %s" % (name, e))
    return items


def main():
    items = fetch()
    data = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "count": len(items),
        "items": items,
    }
    with open("data/news.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1))
    print("TOTAL %d items -> data/news.json" % len(items))


if __name__ == "__main__":
    main()
