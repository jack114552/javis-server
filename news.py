"""每日新闻采集"""
import logging, asyncio, json
from datetime import datetime
from fastapi import APIRouter
from db.database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])

NEWS_SOURCES = [
    {"name": "36氪", "url": "https://36kr.com/feed", "category": "科技"},
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "category": "科技商业"},
    {"name": "Solidot", "url": "https://www.solidot.org/index.rss", "category": "科技"},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage", "category": "科技"},
    {"name": "知乎日报", "url": "https://feeds.feedburner.com/zhihu-daily", "category": "综合"},
    {"name": "极客公园", "url": "https://www.geekpark.net/rss", "category": "科技"},
    {"name": "稀土掘金", "url": "https://rsshub.app/juejin/trending", "category": "开发者"},
    {"name": "开源中国", "url": "https://rsshub.app/oschina/news", "category": "开发者"},
    {"name": "InfoQ", "url": "https://rsshub.app/infoq", "category": "科技"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "国际"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "category": "科技"},
    {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "category": "科技"},
]

@router.get("/today")
async def get_today_news(limit: int = 20):
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    cached = conn.execute("SELECT data FROM news_cache WHERE date = ?", (today,)).fetchone()
    if cached:
        return {"news": json.loads(cached["data"]), "cached": True, "date": today}

    all_news = await _fetch_all()
    seen = set()
    unique = []
    for item in all_news:
        key = item["title"][:30]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    conn.execute("INSERT OR REPLACE INTO news_cache (date, data) VALUES (?, ?)",
                 (today, json.dumps(unique[:limit], ensure_ascii=False)))
    conn.commit()
    return {"news": unique[:limit], "cached": False, "date": today, "total": len(unique)}

async def _fetch_all():
    import xml.etree.ElementTree as ET
    import urllib.request
    import asyncio

    async def fetch_one(source):
        items = []
        try:
            def _sync():
                req = urllib.request.Request(source["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    return resp.read()
            raw = await asyncio.to_thread(_sync)
            text = raw.decode("utf-8", errors="replace")
            root = ET.fromstring(text)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                if title and link:
                    items.append({
                        "title": title.strip(), "url": link.strip(),
                        "summary": desc.strip()[:200],
                        "source": source["name"], "category": source["category"], "time": "",
                    })
            logger.info(f"新闻 [{source['name']}]: {len(items)} 条")
        except Exception as e:
            logger.warning(f"新闻抓取失败 [{source['name']}]: {e}")
        return items

    tasks = [fetch_one(s) for s in NEWS_SOURCES]
    results = await asyncio.gather(*tasks)
    all_news = []
    for r in results:
        all_news.extend(r)
    # 轮转混合（确保不同来源交替出现，而不是一家独占前20）
    by_source = {}
    for item in all_news:
        by_source.setdefault(item["source"], []).append(item)
    # 每家最多取5条后轮转
    # 每家最多取3条，凑够10+源
    max_per = 3
    pooled = []
    for items in by_source.values():
        pooled.extend(items[:max_per])
    pooled.sort(key=lambda x: x.get("time", ""), reverse=True)
    return pooled
