from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import AsyncSessionLocal
from cache.news_cache import (
    EMPTY,
    get_cached_categories,
    set_cache_categories,
    get_cache_news_list,
    set_cache_news_list,
    get_cached_news_detail,
    cache_news_detail,
    get_cached_related_news,
    cache_related_news,
    get_cached_news_count,
    set_cache_news_count,
    invalidate_news_caches,
    invalidate_category_caches,
)
from models.news import Category, News
from schemas.base import NewsItemBase
from schemas.news import NewsDetailResponse, RelatedNewsResponse


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取数据（EMPTY 表示缓存过“空分类”，直接返回空列表防穿透）
    cached_categories = await get_cached_categories()
    if cached_categories is EMPTY:
        return []
    if cached_categories:
        return cached_categories

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()  # ORM

    # 写入缓存（空结果也会写短 TTL 占位防穿透，见 cache 层）
    if categories:
        categories = jsonable_encoder(categories)
    await set_cache_categories(categories)

    # 返回数据
    return categories


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 先尝试从缓存获取新闻列表
    # 跳过的数量skip = (页码 -1) * 每页数量 → 页码 = 跳过的数量 // 每页数量 + 1
    # await get_cache_news_list(分类id, 页码, 每页数量)
    page = skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)  # 缓存数据 json
    if cached_list is EMPTY:
        return []
    if cached_list:
        return [News(**item) for item in cached_list]

    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    # 写入缓存（空结果写短 TTL 占位防穿透）
    # by_alias=False 不使用别名：Redis 数据是给后端用的，保存 Python 风格字段名
    news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
    await set_cache_news_list(category_id, page, limit, news_data)

    return news_list


async def get_news_count_cached(db: AsyncSession, category_id: int):
    # 分类新闻总数也走缓存，避免列表命中缓存后仍每次执行 count(*)
    cached_count = await get_cached_news_count(category_id)
    if cached_count is not None:
        return cached_count

    # 查询的是指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    count = result.scalar_one()  # 只能有一个结果，否则报错

    # 回写缓存：0 也是合法缓存值（读取侧以 None 区分未命中），不写的话缓存永远冰冷
    await set_cache_news_count(category_id, count)

    return count


async def get_news_detail(db: AsyncSession, news_id: int):
    # 先尝试从缓存获取（EMPTY 表示缓存过“新闻不存在”的占位）
    cached_news = await get_cached_news_detail(news_id)
    if cached_news is EMPTY:
        return None
    if cached_news:
        return News(**cached_news)

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    # 存入缓存（不使用别名，保持数据库字段名；空结果写短 TTL 占位防穿透）
    if news:
        news_dict = NewsDetailResponse.model_validate(news).model_dump(
            by_alias=False, mode="json", exclude={'related_news'}
        )
    else:
        news_dict = {}
    await cache_news_detail(news_id, news_dict)

    return news


async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()

    # 写库成功后失效详情与相关新闻缓存（写后失效策略），否则客户端会一直读到旧浏览量
    if result.rowcount > 0:
        await invalidate_news_caches(news_id)

    # 更新 → 检查数据库是否真的命中了数据 → 命中了返回True
    return result.rowcount > 0


async def increase_news_views_in_background(news_id: int) -> None:
    """后台任务入口：自建独立会话执行浏览量自增。
    BackgroundTasks 在响应发出后才运行，此时请求级会话已关闭，必须新建会话"""
    async with AsyncSessionLocal() as db:
        try:
            await increase_news_views(db, news_id)
        except Exception:
            await db.rollback()


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    cached_related = await get_cached_related_news(news_id, category_id)
    if cached_related:
        # 缓存数据是字典列表，直接返回
        return cached_related
    # order_by 排序 → 浏览量和发布时间
    stmt = select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),  # 默认是升序，desc 表示降序
        News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()

    # 转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        related_data = [
            RelatedNewsResponse.model_validate(news).model_dump(by_alias=False, mode="json")
            for news in related_news
        ]
        await cache_related_news(news_id, category_id, related_data)
        return related_data

    # 没有相关新闻，返回空列表
    return []
    # 列表推导式 推导出新闻的核心数据，然后再 return
    # return [{
    #     "id": news_detail.id,
    #     "title": news_detail.title,
    #     "content": news_detail.content,
    #     "image": news_detail.image,
    #     "author": news_detail.author,
    #     "publishTime": news_detail.publish_time,
    #     "categoryId": news_detail.category_id,
    #     "views": news_detail.views
    # } for news_detail in related_news]
