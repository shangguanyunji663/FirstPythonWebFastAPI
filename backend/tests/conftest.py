"""pytest 全局夹具：
- 内存 SQLite（StaticPool 共享连接）替代 MySQL，每个测试独立建表
- fakeredis 替代真实 Redis，缓存行为可断言且不污染开发环境
- 覆盖 get_db 依赖与后台任务用的会话工厂，全部指向测试引擎
"""
import pytest_asyncio
from fakeredis import aioredis as fakeredis_aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import config.cache_conf
import crud.news_cache
from config.db_conf import get_db
from main import app  # noqa: F401  导入即注册全部模型到 Base.metadata
from models.base import Base
from utils import rate_limit

REGISTER_PATH = "/api/user/register"
LOGIN_PATH = "/api/user/login"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,  # 内存库必须共享同一连接，多个会话才能看到彼此的数据
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def fake_redis():
    client = fakeredis_aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def patched_environment(session_factory, fake_redis, monkeypatch):
    """每个测试自动执行：缓存层/后台任务的 Redis 与会话工厂全部指向测试环境，
    限流器（进程级全局状态）在测试间清空"""
    monkeypatch.setattr(config.cache_conf, "redis_client", fake_redis)
    monkeypatch.setattr(crud.news_cache, "AsyncSessionLocal", session_factory)
    rate_limit._attempts.clear()
    yield


@pytest_asyncio.fixture
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_news(session_factory):
    """预置 1 个分类 + 15 条新闻（足够验证分页与相关新闻）"""
    from datetime import datetime

    from models.news import Category, News

    async with session_factory() as db:
        category = Category(name="科技", sort_order=1)
        db.add(category)
        await db.flush()  # 拿到自增 id

        now = datetime.now()
        news_list = [
            News(title=f"测试新闻{i:02d}", content=f"测试内容{i}", description=f"简介{i}",
                 author="测试作者", category_id=category.id, views=i, publish_time=now)
            for i in range(15)
        ]
        db.add_all(news_list)
        await db.commit()
        return {"category_id": category.id, "news_ids": [n.id for n in news_list]}


async def register_user(client, username="testuser01", password="pass123456"):
    """注册并返回响应"""
    return await client.post(REGISTER_PATH, json={"username": username, "password": password})


async def auth_headers(client, username="testuser01", password="pass123456"):
    """注册拿 token，返回带 Authorization 的请求头"""
    response = await register_user(client, username, password)
    assert response.status_code == 200, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
