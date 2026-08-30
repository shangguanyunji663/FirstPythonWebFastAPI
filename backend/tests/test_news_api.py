"""新闻模块接口测试：分类 / 列表分页 / 计数缓存回写 / 详情与后台浏览量 / 相关新闻 / 缓存穿透"""
from sqlalchemy import select

from cache.news_cache import NEWS_COUNT_PREFIX, NEWS_DETAIL_PREFIX
from models.news import News
from tests.conftest import auth_headers

CATEGORIES_PATH = "/api/news/categories"
LIST_PATH = "/api/news/list"
DETAIL_PATH = "/api/news/detail"


async def test_categories(client, seed_news):
    response = await client.get(CATEGORIES_PATH)
    assert response.status_code == 200
    names = [c["name"] for c in response.json()["data"]]
    assert "科技" in names


async def test_news_list_pagination(client, seed_news):
    first = await client.get(LIST_PATH, params={"categoryId": seed_news["category_id"], "page": 1, "pageSize": 10})
    assert first.status_code == 200
    body = first.json()["data"]
    assert len(body["list"]) == 10
    assert body["total"] == 15
    assert body["hasMore"] is True

    second = await client.get(LIST_PATH, params={"categoryId": seed_news["category_id"], "page": 2, "pageSize": 10})
    body2 = second.json()["data"]
    assert len(body2["list"]) == 5
    assert body2["hasMore"] is False


async def test_news_count_cache_write_back(client, seed_news, fake_redis):
    """修复验证：列表请求后分类总数必须回写缓存，后续请求不再执行 count(*)"""
    key = f"{NEWS_COUNT_PREFIX}{seed_news['category_id']}"
    assert await fake_redis.get(key) is None  # 请求前缓存为空

    await client.get(LIST_PATH, params={"categoryId": seed_news["category_id"], "page": 1, "pageSize": 10})
    cached = await fake_redis.get(key)
    assert cached is not None
    assert cached == "15"

    # 第二次请求命中缓存，响应数据一致
    again = await client.get(LIST_PATH, params={"categoryId": seed_news["category_id"], "page": 1, "pageSize": 10})
    assert again.json()["data"]["total"] == 15


async def test_news_detail_and_related(client, seed_news):
    response = await client.get(DETAIL_PATH, params={"id": seed_news["news_ids"][0]})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["title"] == "测试新闻00"
    # 同分类的另外 14 条都是相关新闻，最多返回 5 条
    assert 0 < len(body["relatedNews"]) <= 5


async def test_news_detail_increments_views_in_background(client, seed_news, session_factory):
    """浏览量自增移到响应后的后台任务：响应立即返回，任务完成后库中 views +1"""
    news_id = seed_news["news_ids"][0]
    response = await client.get(DETAIL_PATH, params={"id": news_id})
    assert response.status_code == 200

    async with session_factory() as db:
        news = (await db.execute(select(News).where(News.id == news_id))).scalar_one()
        assert news.views == 1  # 种子数据 views=0，详情访问一次后 +1


async def test_news_detail_not_found(client, seed_news, fake_redis):
    response = await client.get(DETAIL_PATH, params={"id": 99999})
    assert response.status_code == 404
    assert response.json()["message"] == "新闻不存在"

    # 缓存穿透防护：不存在的新闻缓存了空值占位，重复请求不再打库
    empty_key = f"{NEWS_DETAIL_PREFIX}99999"
    cached = await fake_redis.get(empty_key)
    assert cached is not None
    assert "__empty__" in cached


async def test_empty_category_list_not_leak_marker(client, seed_news, fake_redis):
    """回归：空值占位读写不对称会让 marker 泄漏给客户端。
    空分类第一次请求写入占位缓存，第二次请求命中占位也必须返回空列表而非 __empty__ 结构"""
    params = {"categoryId": 999, "page": 1, "pageSize": 10}
    first = await client.get(LIST_PATH, params=params)
    assert first.status_code == 200
    assert first.json()["data"]["list"] == []
    assert first.json()["data"]["total"] == 0

    again = await client.get(LIST_PATH, params=params)
    assert again.status_code == 200
    assert again.json()["data"]["list"] == []


async def test_categories_cached_empty_marker_not_leaked(client, seed_news, fake_redis):
    """回归：分类缓存里是占位 marker 时，接口应返回空列表而不是 marker 本身"""
    from cache.news_cache import CATEGORIES_KEY

    await fake_redis.set(CATEGORIES_KEY, '[{"__empty__": true}]')
    response = await client.get(CATEGORIES_PATH)
    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_favorite_news_shows_in_list(client, seed_news, session_factory):
    """收藏列表联表分页（对应 /api/favorite 接口，新闻数据由本文件种子提供）"""
    from models.favorite import Favorite

    headers = await auth_headers(client)
    async with session_factory() as db:
        db.add(Favorite(user_id=1, news_id=seed_news["news_ids"][0]))
        await db.commit()

    response = await client.get("/api/favorite/list", headers=headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] == 1
    assert body["list"][0]["id"] == seed_news["news_ids"][0]
