"""用户模块接口测试：注册校验 / 登录 / token 哈希 / 信息查询与更新 / 改密 / 登录限流"""
import hashlib

from sqlalchemy import select

from models.users import User, UserToken
from tests.conftest import LOGIN_PATH, auth_headers, register_user
from utils import security
from utils.rate_limit import _attempts

USER_INFO_PATH = "/api/user/info"
USER_UPDATE_PATH = "/api/user/update"
USER_PASSWORD_PATH = "/api/user/password"


async def test_register_success(client):
    response = await register_user(client)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["token"]
    assert body["data"]["userInfo"]["username"] == "testuser01"


async def test_register_duplicate_username(client):
    await register_user(client)
    response = await register_user(client)
    assert response.status_code == 400
    assert response.json()["message"] == "用户已存在"


async def test_register_rejects_short_username(client):
    response = await register_user(client, username="ab")
    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "长度不足"
    assert body["data"][0]["field"] == "username"


async def test_register_rejects_bad_username_pattern(client):
    response = await register_user(client, username="非法名称!")
    assert response.status_code == 400
    assert response.json()["message"] == "格式不正确"


async def test_register_rejects_short_password(client):
    response = await register_user(client, username="validuser", password="123")
    assert response.status_code == 400
    assert response.json()["data"][0]["field"] == "password"


async def test_login_success_and_wrong_password(client):
    await register_user(client)

    ok = await client.post(LOGIN_PATH, json={"username": "testuser01", "password": "pass123456"})
    assert ok.status_code == 200
    assert ok.json()["data"]["token"]

    bad = await client.post(LOGIN_PATH, json={"username": "testuser01", "password": "wrong-password"})
    assert bad.status_code == 401
    assert bad.json()["message"] == "用户名或密码错误"


async def test_login_is_lenient_for_legacy_username(client, session_factory):
    """历史用户名可以不满足注册新规则：直接建一个 2 位用户名用户，登录应放行"""
    async with session_factory() as db:
        db.add(User(username="ab", password=security.get_hash_password("pass123456")))
        await db.commit()

    response = await client.post(LOGIN_PATH, json={"username": "ab", "password": "pass123456"})
    assert response.status_code == 200


async def test_token_stored_as_sha256_digest(client, session_factory):
    """登录令牌入库只存 SHA-256 摘要，原文不落库"""
    response = await register_user(client)
    raw_token = response.json()["data"]["token"]

    async with session_factory() as db:
        row = (await db.execute(select(UserToken))).scalars().one()
        assert row.token != raw_token
        assert row.token == hashlib.sha256(raw_token.encode()).hexdigest()
        assert len(row.token) == 64


async def test_login_invalidates_previous_token(client):
    """同一用户重新登录后，旧令牌应失效（每用户仅一条有效令牌）"""
    first = (await register_user(client)).json()["data"]["token"]
    second = (await client.post(
        LOGIN_PATH, json={"username": "testuser01", "password": "pass123456"}
    )).json()["data"]["token"]

    old_headers = {"Authorization": f"Bearer {first}"}
    new_headers = {"Authorization": f"Bearer {second}"}

    assert (await client.get(USER_INFO_PATH, headers=old_headers)).status_code == 401
    assert (await client.get(USER_INFO_PATH, headers=new_headers)).status_code == 200


async def test_user_info_requires_auth(client):
    missing = await client.get(USER_INFO_PATH)
    assert missing.status_code == 400  # 缺少请求头 → 参数校验错误（修复前会掉进兜底 500）

    invalid = await client.get(USER_INFO_PATH, headers={"Authorization": "Bearer not-a-token"})
    assert invalid.status_code == 401


async def test_user_info_success(client):
    headers = await auth_headers(client)
    response = await client.get(USER_INFO_PATH, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "testuser01"


async def test_update_user_info_validates_gender(client):
    headers = await auth_headers(client)

    ok = await client.put(USER_UPDATE_PATH, json={"nickname": "新昵称", "gender": "male"}, headers=headers)
    assert ok.status_code == 200
    assert ok.json()["data"]["nickname"] == "新昵称"

    bad = await client.put(USER_UPDATE_PATH, json={"gender": "未知"}, headers=headers)
    assert bad.status_code == 400
    assert bad.json()["message"] == "取值不合法"


async def test_duplicate_phone_maps_to_friendly_message(client, session_factory):
    """撞手机号唯一约束 → IntegrityError 全局处理器 → 400 可读文案"""
    headers_a = await auth_headers(client, username="user_aaa")
    await auth_headers(client, username="user_bbb")

    async with session_factory() as db:
        user_b = (await db.execute(select(User).where(User.username == "user_bbb"))).scalar_one()
        await db.execute(
            User.__table__.update().where(User.id == user_b.id).values(phone="13800138000"))
        await db.commit()

    conflict = await client.put(USER_UPDATE_PATH, json={"phone": "13800138000"}, headers=headers_a)
    assert conflict.status_code == 400
    assert conflict.json()["message"] == "手机号已被注册"


async def test_change_password_flow(client):
    headers = await auth_headers(client)

    wrong_old = await client.put(USER_PASSWORD_PATH, json={
        "oldPassword": "wrong-old", "newPassword": "newpass123"}, headers=headers)
    assert wrong_old.status_code == 400
    assert wrong_old.json()["message"] == "旧密码不正确"

    ok = await client.put(USER_PASSWORD_PATH, json={
        "oldPassword": "pass123456", "newPassword": "newpass123"}, headers=headers)
    assert ok.status_code == 200

    old_login = await client.post(LOGIN_PATH, json={"username": "testuser01", "password": "pass123456"})
    assert old_login.status_code == 401
    new_login = await client.post(LOGIN_PATH, json={"username": "testuser01", "password": "newpass123"})
    assert new_login.status_code == 200


async def test_login_rate_limit(client):
    """同一用户名 60 秒内第 6 次登录尝试 → 429"""
    for _ in range(5):
        await client.post(LOGIN_PATH, json={"username": "rateuser", "password": "bad-pass"})
    sixth = await client.post(LOGIN_PATH, json={"username": "rateuser", "password": "bad-pass"})
    assert sixth.status_code == 429
    assert sixth.json()["message"] == "登录尝试过于频繁，请稍后再试"
    assert "rateuser" in _attempts  # 触发限流后记录仍在
