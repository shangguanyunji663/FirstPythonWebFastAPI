from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news as news_crud
from schemas.base import NewsItemBase
from schemas.news import CategoryResponse, NewsDetailResponse, NewsListResponse
from schemas.response import APIResponse

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程
# 1. 模块化路由 → API 接口规范文档
# 2. 定义模型类 → 数据库表（数据库设计文档）
# 3. 在 crud 文件夹里面创建文件，封装操作数据库的方法
# 4. 在路由处理函数里面调用 crud 封装好的方法，响应结果


@router.get("/categories", response_model=APIResponse[list[CategoryResponse]])
async def get_categories(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                         db: AsyncSession = Depends(get_db)):
    # 先获取数据库里面新闻分类数据 → 先定义模型类 → 封装查询数据的方法
    categories = await news_crud.get_categories(db, skip, limit)
    return {"code": 200, "message": "获取新闻分类成功", "data": categories}


@router.get("/list", response_model=APIResponse[NewsListResponse])
async def get_news_list(
        category_id: int = Query(..., alias="categoryId"),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        db: AsyncSession = Depends(get_db)
):
    # 思路：处理分页规则 → 查询新闻列表 → 计算总量 → 计算是否还有更多
    offset = (page - 1) * page_size
    news_list = await news_crud.get_news_list(db, category_id, offset, page_size)
    total = await news_crud.get_news_count_cached(db, category_id)
    # (跳过的 + 当前列表里面的数量) < 总量
    has_more = (offset + len(news_list)) < total
    data = NewsListResponse(
        list=[NewsItemBase.model_validate(item) for item in news_list],
        total=total,
        hasMore=has_more,
    )
    return {"code": 200, "message": "获取新闻列表成功", "data": data}


@router.get("/detail", response_model=APIResponse[NewsDetailResponse])
async def get_news_detail(background_tasks: BackgroundTasks,
                          news_id: int = Query(..., alias="id"),
                          db: AsyncSession = Depends(get_db)):
    # 获取新闻详情 + 浏览量+1（后台异步） + 相关新闻
    news_detail = await news_crud.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 浏览量自增延后到响应之后执行：GET 请求不再阻塞在写库上，
    # 响应中的 views 保持旧行为（取缓存/自增前的值）
    background_tasks.add_task(news_crud.increase_news_views_in_background, news_detail.id)

    related_news = await news_crud.get_related_news(db, news_detail.id, news_detail.category_id)

    data = NewsDetailResponse.model_validate({
        "id": news_detail.id,
        "title": news_detail.title,
        "description": news_detail.description,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
        "relatedNews": related_news,
    })
    return {"code": 200, "message": "success", "data": data}
