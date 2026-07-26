"""每日新闻采集 — 支持个性化权重排序"""
import logging, asyncio, json, re
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


def _get_user_interest_keywords() -> list:
    """从记忆里读取用户兴趣关键词，返回关键词列表"""
    conn = get_connection()
    keywords = []

    # 1. 从 memories 中提取兴趣相关条目
    interest_rows = conn.execute(
        """SELECT content FROM memories
           WHERE tags LIKE '%interest%' OR tags LIKE '%hobby%' OR tags LIKE '%preference%'
              OR category = 'interest' OR category = 'preference' OR category = 'hobby'
           ORDER BY created_at DESC LIMIT 20"""
    ).fetchall()

    for row in interest_rows:
        content = row["content"]
        # 提取关键词（单个词 > 2 个中文字符的）
        words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        keywords.extend(words)

    # 2. 从近期聊天中提取——高频词作为兴趣线索
    recent_rows = conn.execute(
        """SELECT content FROM conversations
           WHERE role = 'user' AND content IS NOT NULL
           ORDER BY created_at DESC LIMIT 50"""
    ).fetchall()

    # 统计用户消息中的高频词
    word_freq = {}
    for row in recent_rows:
        content = row["content"] or ""
        words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1

    # 出现 3 次以上的算兴趣词
    high_freq = [w for w, c in word_freq.items() if c >= 3]
    keywords.extend(high_freq)

    # 3. 去重
    unique = list(set(keywords))
    logger.info(f"用户兴趣关键词: {unique[:20]}")
    return unique[:20]  # 最多 20 个


def _score_item(item: dict, interest_keywords: list) -> int:
    """计算新闻条目的兴趣分数"""
    if not interest_keywords:
        return 0

    score = 0
    title = (item.get("title") or "") + " " + (item.get("summary") or "")

    # 按来源加权
    source_weights = {
        "开发者": 3,
        "科技": 2,
        "科技商业": 2,
    }
    source_weight = source_weights.get(item.get("category", ""), 1)

    for kw in interest_keywords:
        if kw.lower() in title.lower():
            score += source_weight * 2
        elif any(kw in (item.get("source") or "") for kw in interest_keywords):
            score += source_weight

    return score


@router.get("/today")
async def get_today_news(limit: int = 20):
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    cached = conn.execute("SELECT data FROM news_cache WHERE date = ?", (today,)).fetchone()
    if cached:
        news = json.loads(cached["data"])
    else:
        all_news = await _fetch_all()
        seen = set()
        unique = []
        for item in all_news:
            key = item["title"][:30]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        # 缓存全部新闻（不截断）
        conn.execute("INSERT OR REPLACE INTO news_cache (date, data) VALUES (?, ?)",
                     (today, json.dumps(unique, ensure_ascii=False)))
        conn.commit()
        news = unique

    # 个性化加权排序
    interest_kw = _get_user_interest_keywords()
    if interest_kw:
        for item in news:
            item["_score"] = _score_item(item, interest_kw)
        news.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # 截取限制条数（加权后高分排前）
    result = news[:limit]
    # 清理内部分数
    for item in result:
        item.pop("_score", None)

    return {"news": result, "cached": cached is not None, "date": today, "total": len(news)}

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
    # 每家最多取3条
    max_per = 3
    pooled = []
    for items in by_source.values():
        pooled.extend(items[:max_per])
    pooled.sort(key=lambda x: x.get("time", ""), reverse=True)
    return pooled
