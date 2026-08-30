"""收藏模块接口测试：添加 / 去重 / 检查 / 删除 / 清空"""
from tests.conftest import auth_headers

ADD_PATH = "/api/favorite/add"
REMOVE_PATH = "/api/favorite/remove"
CHECK_PATH = "/api/favorite/check"
CLEAR_PATH = "/api/favorite/clear"
LIST_PATH = "/api/favorite/list"


async def test_favorite_full_flow(client, seed_news):
    headers = await auth_headers(client)
    news_id = seed_news["news_ids"][0]

    added = await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    assert added.status_code == 200
    assert added.json()["data"]["newsId"] == news_id

    checked = await client.get(CHECK_PATH, params={"newsId": news_id}, headers=headers)
    assert checked.json()["data"]["isFavorite"] is True

    listed = await client.get(LIST_PATH, headers=headers)
    assert listed.json()["data"]["total"] == 1

    removed = await client.delete(REMOVE_PATH, params={"newsId": news_id}, headers=headers)
    assert removed.status_code == 200

    checked_again = await client.get(CHECK_PATH, params={"newsId": news_id}, headers=headers)
    assert checked_again.json()["data"]["isFavorite"] is False


async def test_duplicate_favorite_returns_friendly_error(client, seed_news):
    """重复收藏触发 user_news_unique 唯一约束 → 全局处理器映射为可读文案"""
    headers = await auth_headers(client)
    news_id = seed_news["news_ids"][0]

    await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    duplicate = await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    assert duplicate.status_code == 400
    assert duplicate.json()["message"] == "已收藏过该新闻"


async def test_remove_missing_favorite_404(client, seed_news):
    headers = await auth_headers(client)
    response = await client.delete(REMOVE_PATH, params={"newsId": 99999}, headers=headers)
    assert response.status_code == 404
    assert response.json()["message"] == "收藏记录不存在"


async def test_clear_favorites(client, seed_news, session_factory):
    from models.favorite import Favorite

    headers = await auth_headers(client)
    async with session_factory() as db:
        db.add_all([
            Favorite(user_id=1, news_id=seed_news["news_ids"][0]),
            Favorite(user_id=1, news_id=seed_news["news_ids"][1]),
        ])
        await db.commit()

    cleared = await client.delete(CLEAR_PATH, headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["message"] == "清空了2条记录"

    listed = await client.get(LIST_PATH, headers=headers)
    assert listed.json()["data"]["total"] == 0


async def test_favorite_requires_auth(client, seed_news):
    response = await client.post(ADD_PATH, json={"newsId": seed_news["news_ids"][0]})
    assert response.status_code == 400  # 缺少 Authorization 请求头
