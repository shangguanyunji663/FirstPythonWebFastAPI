"""RSS 新闻抓取服务：抓取公开源 → 解析 → 按 (标题, 分类) 去重入库 → 失效分类缓存。
不依赖具体调用方：定时任务（main.py lifespan）与手动触发接口（routers/crawler.py）共用。
入库依赖 news 表的 (title, category_id) 唯一索引兜底，查询预过滤负责跳过已存在的标题。"""
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

import feedparser
import httpx
from selectolax.parser import HTMLParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import invalidate_category_caches
from crawler.sources import RSS_SOURCES
from models.news import Category, News

logger = logging.getLogger("app.crawler")

FETCH_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
MAX_ITEMS_PER_FEED = 20
CONTENT_MAX_LENGTH = 5000
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 FoundGoldenNews-Crawler/1.0")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str | None, limit: int = 500) -> str:
    """RSS 的 summary/content 常内嵌 HTML 标签，转纯文本并把连续空白折叠为单个空格。
    strip=False 保留节点自身空白（如 "Hello <b>world</b>" 的空格），相邻标签间不额外插空格"""
    if not text:
        return ""
    try:
        plain = HTMLParser(text).text(separator="", strip=False)
    except Exception:
        plain = text
    return _WHITESPACE_RE.sub(" ", plain).strip()[:limit]


def extract_image(entry) -> str | None:
    """封面图：优先 media 命名空间的缩略图，其次取摘要里的第一张 <img>"""
    for key in ("media_thumbnail", "media_content"):
        media = entry.get(key) or []
        if media and media[0].get("url"):
            return media[0]["url"]

    html = entry.get("summary", "") or ""
    try:
        node = HTMLParser(html).css_first("img")
    except Exception:
        return None
    return node.attrs.get("src") if node else None


def parse_entry_time(entry) -> datetime:
    """pubDate/updated 缺失时退回当前时间，保证 publish_time 非空"""
    for key in ("published_parsed", "updated_parsed"):
        struct = entry.get(key)
        if struct:
            return datetime(*struct[:6])
    return datetime.now()


def parse_feed(xml_text: str, category_id: int, limit: int = MAX_ITEMS_PER_FEED) -> list[dict[str, Any]]:
    """RSS/Atom XML → 新闻草稿列表。纯函数不碰数据库，方便单测"""
    feed = feedparser.parse(xml_text)
    drafts = []
    for entry in feed.entries[:limit]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue

        summary = entry.get("summary", "") or ""
        content_field = entry.get("content")
        content_html = content_field[0].get("value", "") if content_field else summary

        drafts.append({
            "title": title[:255],  # 与 news.title 列宽对齐
            "description": strip_html(summary) or title[:255],
            "content": strip_html(content_html, CONTENT_MAX_LENGTH) or title,
            "image": extract_image(entry),
            "author": ((entry.get("author") or "").strip() or "网络来源")[:50],
            "category_id": category_id,
            "publish_time": parse_entry_time(entry),
            "views": 0,
        })
    return drafts


async def fetch_feed_xml(client: httpx.AsyncClient, url: str) -> str | None:
    """抓取单个源；任何失败只记日志返回 None，由调用方跳过"""
    try:
        response = await client.get(url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning("抓取失败 %s：%s", url, e)
        return None


async def crawl_all(
        db: AsyncSession,
        sources: list[dict] | None = None,
        fetcher: Callable[[httpx.AsyncClient, str], Awaitable[str | None]] | None = None,
) -> dict[str, Any]:
    """抓取全部源并入库，返回统计：{"fetched", "inserted", "skipped", "failed_sources"}。
    fetcher 参数用于测试注入，生产传 None 走真实 HTTP 抓取"""
    sources = sources if sources is not None else RSS_SOURCES
    fetcher = fetcher or fetch_feed_xml
    stats: dict[str, Any] = {"fetched": 0, "inserted": 0, "skipped": 0, "failed_sources": []}

    # 分类名 → id 一次查出，循环内不再查库
    result = await db.execute(select(Category))
    category_map = {c.name: c.id for c in result.scalars().all()}

    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
        for source in sources:
            category_id = category_map.get(source["category"])
            if category_id is None:
                logger.warning("分类 %s 不存在，跳过源 %s", source["category"], source["url"])
                continue

            xml_text = await fetcher(client, source["url"])
            if xml_text is None:
                stats["failed_sources"].append(source["url"])
                continue

            drafts = parse_feed(xml_text, category_id)
            stats["fetched"] += len(drafts)

            # 同分类下按标题预过滤，避免重复入库；并发写入由唯一索引兜底
            titles = [d["title"] for d in drafts]
            existing = await db.execute(
                select(News.title).where(News.category_id == category_id, News.title.in_(titles))
            )
            existing_titles = {row[0] for row in existing}

            new_rows = [News(**d) for d in drafts if d["title"] not in existing_titles]
            if new_rows:
                db.add_all(new_rows)
            stats["inserted"] += len(new_rows)
            stats["skipped"] += len(drafts) - len(new_rows)

    await db.commit()

    # 入库后失效受影响分类的列表与总数缓存
    for source in sources:
        category_id = category_map.get(source["category"])
        if category_id is not None:
            await invalidate_category_caches(category_id)

    return stats
