"""浏览历史模块接口测试：添加 / 重复浏览去重更新 / 列表 / 删除归属校验 / 清空"""
from tests.conftest import auth_headers

ADD_PATH = "/api/history/add"
LIST_PATH = "/api/history/list"
CLEAR_PATH = "/api/history/clear"


def _delete_path(history_id: int) -> str:
    return f"/api/history/delete/{history_id}"


async def test_add_and_list_history(client, seed_news):
    headers = await auth_headers(client)
    news_id = seed_news["news_ids"][0]

    added = await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    assert added.status_code == 200
    assert added.json()["data"]["newsId"] == news_id

    # 重复浏览同一条 → 更新浏览时间，不新增行
    again = await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    assert again.status_code == 200
    assert again.json()["data"]["id"] == added.json()["data"]["id"]

    listed = await client.get(LIST_PATH, headers=headers)
    body = listed.json()["data"]
    assert body["total"] == 1
    assert body["list"][0]["historyId"] == added.json()["data"]["id"]
    assert body["list"][0]["id"] == news_id


async def test_delete_own_history(client, seed_news):
    headers = await auth_headers(client)
    news_id = seed_news["news_ids"][0]
    added = await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)
    history_id = added.json()["data"]["id"]

    deleted = await client.delete(_delete_path(history_id), headers=headers)
    assert deleted.status_code == 200

    # 删完再删同一条 → 404
    missing = await client.delete(_delete_path(history_id), headers=headers)
    assert missing.status_code == 404
    assert missing.json()["message"] == "历史记录不存在"


async def test_delete_history_horizontal_authorization(client, seed_news):
    """水平越权防护：只能删除自己的历史记录，删他人的返回 404"""
    owner_headers = await auth_headers(client, username="hist_owner1")
    added = await client.post(
        ADD_PATH, json={"newsId": seed_news["news_ids"][0]}, headers=owner_headers)
    history_id = added.json()["data"]["id"]

    stranger_headers = await auth_headers(client, username="hist_stranger1")
    stranger_delete = await client.delete(_delete_path(history_id), headers=stranger_headers)
    assert stranger_delete.status_code == 404

    # 属主本人仍能删除
    owner_delete = await client.delete(_delete_path(history_id), headers=owner_headers)
    assert owner_delete.status_code == 200


async def test_clear_history(client, seed_news):
    headers = await auth_headers(client)
    for news_id in seed_news["news_ids"][:2]:
        await client.post(ADD_PATH, json={"newsId": news_id}, headers=headers)

    cleared = await client.delete(CLEAR_PATH, headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["message"] == "清空成功，共2条"

    listed = await client.get(LIST_PATH, headers=headers)
    assert listed.json()["data"]["total"] == 0


async def test_history_requires_auth(client, seed_news):
    response = await client.post(ADD_PATH, json={"newsId": seed_news["news_ids"][0]})
    assert response.status_code == 400  # 缺少 Authorization 请求头


async def test_history_list_scoped_to_user(client, seed_news):
    """历史列表只包含当前用户自己的记录"""
    user_a = await auth_headers(client, username="hist_user_a1")
    user_b = await auth_headers(client, username="hist_user_b1")

    await client.post(
        ADD_PATH, json={"newsId": seed_news["news_ids"][0]}, headers=user_a)

    listed_b = await client.get(LIST_PATH, headers=user_b)
    assert listed_b.json()["data"]["total"] == 0
