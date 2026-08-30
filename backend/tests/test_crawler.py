"""爬虫模块测试：HTML 转文本 / RSS 解析 / 去重入库 / 手动触发接口。
测试不发起真实 HTTP 请求，fetcher 注入固定的样例 RSS"""
from sqlalchemy import func, select

import crawler.rss_service as rss_service
from crawler.rss_service import crawl_all, parse_feed, strip_html
from models.news import Category, News

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>测试源</title>
    <item>
      <title>第一条新闻</title>
      <link>http://example.com/a</link>
      <description>&lt;p&gt;这是&lt;b&gt;摘要A&lt;/b&gt;&lt;/p&gt;&lt;img src="http://img.example/a.jpg"/&gt;</description>
      <author>作者A</author>
      <pubDate>Mon, 01 Jan 2024 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>第二条新闻</title>
      <link>http://example.com/b</link>
      <description>摘要B</description>
      <media:thumbnail url="http://img.example/b.jpg"/>
    </item>
    <item>
      <title></title>
      <link>http://example.com/c</link>
      <description>无标题条目应被丢弃</description>
    </item>
  </channel>
</rss>"""


async def make_category(session_factory, name="科技") -> int:
    async with session_factory() as db:
        category = Category(name=name, sort_order=99)
        db.add(category)
        await db.commit()
        return category.id


async def test_strip_html():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert strip_html("") == ""
    assert strip_html(None) == ""


async def test_parse_feed():
    drafts = parse_feed(SAMPLE_RSS, category_id=1)
    # 无标题条目被丢弃
    assert len(drafts) == 2

    first = drafts[0]
    assert first["title"] == "第一条新闻"
    assert first["description"] == "这是摘要A"
    assert first["image"] == "http://img.example/a.jpg"  # 从摘要 img 标签提取
    assert first["author"] == "作者A"
    assert first["category_id"] == 1
    assert first["publish_time"].year == 2024

    second = drafts[1]
    assert second["image"] == "http://img.example/b.jpg"  # media:thumbnail 优先
    assert second["author"] == "网络来源"  # 缺失作者回退默认值
    assert second["content"] == "摘要B"


async def test_crawl_dedup_on_second_run(session_factory, monkeypatch):
    """第一次抓取全量入库，第二次抓取相同源时按 (标题, 分类) 去重，新增为 0"""
    category_id = await make_category(session_factory)

    async def fake_fetcher(client, url):
        return SAMPLE_RSS

    sources = [{"url": "test://feed", "category": "科技"}]

    async with session_factory() as db:
        first = await crawl_all(db, sources=sources, fetcher=fake_fetcher)
    assert first["fetched"] == 2
    assert first["inserted"] == 2
    assert first["skipped"] == 0
    assert first["failed_sources"] == []

    async with session_factory() as db:
        second = await crawl_all(db, sources=sources, fetcher=fake_fetcher)
    assert second["fetched"] == 2
    assert second["inserted"] == 0
    assert second["skipped"] == 2

    async with session_factory() as db:
        total = (await db.execute(
            select(func.count(News.id)).where(News.category_id == category_id))).scalar_one()
        assert total == 2


async def test_crawl_failed_source_is_skipped(session_factory):
    """抓取失败的源只记入 failed_sources，不影响其他源入库"""
    await make_category(session_factory, name="财经")

    async def fake_fetcher(client, url):
        return SAMPLE_RSS if url == "test://good" else None

    sources = [
        {"url": "test://good", "category": "财经"},
        {"url": "test://bad", "category": "财经"},
    ]

    async with session_factory() as db:
        stats = await crawl_all(db, sources=sources, fetcher=fake_fetcher)

    assert stats["failed_sources"] == ["test://bad"]
    assert stats["inserted"] == 2


async def test_crawl_skips_unknown_category(session_factory):
    """源配置的分类在库里不存在时直接跳过"""
    async def fake_fetcher(client, url):
        raise AssertionError("不应发起抓取")

    async with session_factory() as db:
        stats = await crawl_all(db, sources=[{"url": "test://x", "category": "不存在的分类"}],
                                fetcher=fake_fetcher)
    assert stats["fetched"] == 0


async def test_crawler_endpoint(client, session_factory, monkeypatch):
    """POST /api/crawler/run：需登录，返回统计"""
    from tests.conftest import auth_headers

    await make_category(session_factory)

    async def fake_fetcher(client_, url):
        return SAMPLE_RSS

    monkeypatch.setattr(rss_service, "fetch_feed_xml", fake_fetcher)

    unauthorized = await client.post("/api/crawler/run")
    assert unauthorized.status_code == 400  # 未带 Authorization

    headers = await auth_headers(client)
    response = await client.post("/api/crawler/run", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["inserted"] == 2
