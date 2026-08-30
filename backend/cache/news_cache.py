# 新闻相关的缓存方法：缓存键规则、读写与失效
# key - value
import random
from typing import Any

from config.cache_conf import (
    delete_cache,
    delete_cache_pattern,
    get_json_cache,
    set_cache,
)

CATEGORIES_KEY = "news:categories"
NEWS_LIST_PREFIX = "news_list:"
NEWS_DETAIL_PREFIX = "news:detail:"
RELATED_NEWS_PREFIX = "news:related:"
NEWS_COUNT_PREFIX = "news:count:"

# 空结果占位：缓存空值，防止不存在的 id/分类反复穿透到数据库（缓存穿透）
EMPTY_MARKER = {"__empty__": True}
EMPTY = object()  # 内存哨兵：getter 返回它表示“缓存命中但数据为空”
EMPTY_TTL = 60  # 空结果占位的短过期时间（秒），新数据写入后最多延迟 1 分钟可见


def _detect_empty(data):
    """识别空值占位：写侧有两种形态——裸 marker（详情）与 [marker]（分类/列表包一层保持结构一致）。
    读取侧统一在这里还原成 EMPTY 哨兵，避免占位数据泄漏给调用方"""
    if data == EMPTY_MARKER:
        return True
    return isinstance(data, list) and len(data) == 1 and data[0] == EMPTY_MARKER


def _with_jitter(expire: int) -> int:
    """TTL 加 ±10% 随机抖动：同类 key 过期时间错开，避免同一时刻集中失效（缓存雪崩）"""
    return int(expire * random.uniform(0.9, 1.1))


# ---------- 新闻分类 ----------
async def get_cached_categories():
    data = await get_json_cache(CATEGORIES_KEY)
    if _detect_empty(data):
        return EMPTY
    return data


async def set_cache_categories(data: list[dict[str, Any]], expire: int = 7200):
    # 数据越稳定缓存越久：分类 7200；列表 1800；详情 300
    if not data:
        data = [EMPTY_MARKER]
        expire = EMPTY_TTL
    return await set_cache(CATEGORIES_KEY, data, _with_jitter(expire))


# ---------- 新闻列表 key = news_list:分类id:页码:每页数量 ----------
def _list_key(category_id: int | None, page: int, size: int) -> str:
    category_part = category_id if category_id is not None else "all"
    return f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"


async def get_cache_news_list(category_id: int | None, page: int, size: int):
    data = await get_json_cache(_list_key(category_id, page, size))
    if _detect_empty(data):
        return EMPTY
    return data


async def set_cache_news_list(category_id: int | None, page: int, size: int,
                              news_list: list[dict[str, Any]], expire: int = 1800):
    if not news_list:
        news_list = [EMPTY_MARKER]
        expire = EMPTY_TTL
    return await set_cache(_list_key(category_id, page, size), news_list, _with_jitter(expire))


# ---------- 新闻详情 ----------
async def get_cached_news_detail(news_id: int) -> dict[str, Any] | None:
    data = await get_json_cache(f"{NEWS_DETAIL_PREFIX}{news_id}")
    if _detect_empty(data):
        return EMPTY
    return data


async def cache_news_detail(news_id: int, news_data: dict[str, Any], expire: int = 300) -> bool:
    if not news_data:
        news_data = EMPTY_MARKER
        expire = EMPTY_TTL
    return await set_cache(f"{NEWS_DETAIL_PREFIX}{news_id}", news_data, _with_jitter(expire))


# ---------- 相关新闻 ----------
async def cache_related_news(news_id: int, category_id: int,
                             related_list: list[dict[str, Any]], expire: int = 1800) -> bool:
    return await set_cache(f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}",
                           related_list, _with_jitter(expire))


async def get_cached_related_news(news_id: int, category_id: int) -> list[dict[str, Any]] | None:
    return await get_json_cache(f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}")


# ---------- 分类新闻总数（列表分页用，避免每次请求都 count(*)） ----------
async def get_cached_news_count(category_id: int) -> int | None:
    """返回缓存的总数；未命中返回 None（0 是合法缓存值，不会与未命中混淆）"""
    return await get_json_cache(f"{NEWS_COUNT_PREFIX}{category_id}")


async def set_cache_news_count(category_id: int, count: int, expire: int = 1800) -> bool:
    return await set_cache(f"{NEWS_COUNT_PREFIX}{category_id}", count, _with_jitter(expire))


# ---------- 失效（写后删缓存，保持“缓存失效”策略） ----------
async def invalidate_news_caches(news_id: int) -> None:
    """新闻数据变更后失效相关缓存：详情 + 该新闻的相关新闻列表。
    列表缓存保留 TTL 内的旧浏览量（列表允许短暂滞后，避免每次浏览都清空全部列表缓存）"""
    await delete_cache(f"{NEWS_DETAIL_PREFIX}{news_id}")
    await delete_cache_pattern(f"{RELATED_NEWS_PREFIX}{news_id}:*")


async def invalidate_category_caches(category_id: int) -> None:
    """新闻增删后失效该分类的列表与总数缓存（浏览量变更走 invalidate_news_caches）"""
    await delete_cache(f"{NEWS_COUNT_PREFIX}{category_id}")
    await delete_cache_pattern(f"{NEWS_LIST_PREFIX}{category_id}:*")
