"""缓存层单元测试：fakeredis 上验证读写、空值占位、TTL 抖动、模式删除"""
from cache.news_cache import (
    EMPTY,
    _with_jitter,
    get_cached_categories,
    get_cached_news_count,
    get_json_cache,
    set_cache,
    set_cache_categories,
    set_cache_news_count,
)
from config.cache_conf import delete_cache, delete_cache_pattern


async def test_json_roundtrip(fake_redis):
    assert await set_cache("unit:key", {"hello": "世界", "n": 1})
    assert await get_json_cache("unit:key") == {"hello": "世界", "n": 1}
    assert await get_json_cache("unit:missing") is None


async def test_empty_marker_prevents_penetration(fake_redis):
    """空分类写入短 TTL 占位；读取侧返回 EMPTY 哨兵而不是空列表/None"""
    await set_cache_categories([])
    assert await get_cached_categories() is EMPTY


async def test_count_cache_zero_is_valid(fake_redis):
    """总数为 0 也是合法缓存值，不能与未命中（None）混淆"""
    assert await get_cached_news_count(1) is None
    await set_cache_news_count(1, 0)
    assert await get_cached_news_count(1) == 0
    await set_cache_news_count(1, 42)
    assert await get_cached_news_count(1) == 42


def test_ttl_jitter_bounds():
    """TTL 抖动必须落在 ±10% 区间内（防缓存雪崩）"""
    expire = 1800
    for _ in range(50):
        assert int(expire * 0.9) <= _with_jitter(expire) <= int(expire * 1.1)


async def test_delete_cache_pattern_only_matches_prefix(fake_redis):
    await fake_redis.set("news_list:1:1:10", "a")
    await fake_redis.set("news_list:1:2:10", "b")
    await fake_redis.set("news_list:2:1:10", "c")
    await fake_redis.set("news:detail:1", "d")

    deleted = await delete_cache_pattern("news_list:1:*")
    assert deleted == 2
    assert await fake_redis.get("news_list:2:1:10") == "c"
    assert await fake_redis.get("news:detail:1") == "d"


async def test_delete_single_key(fake_redis):
    await fake_redis.set("some:key", "v")
    assert await delete_cache("some:key") is True
    assert await fake_redis.get("some:key") is None
