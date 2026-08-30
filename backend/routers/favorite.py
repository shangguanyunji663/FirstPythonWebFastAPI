from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import favorite
from models.users import User
from schemas.favorite import (FavoriteAddRequest, FavoriteAddResponse, FavoriteCheckResponse,
                              FavoriteListResponse, FavoriteNewsItemResponse)
from schemas.response import APIResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/favorite", tags=["favorite"])


@router.get("/check", response_model=APIResponse[FavoriteCheckResponse])
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    is_favorited = await favorite.is_news_favorite(db, user.id, news_id)
    return {"code": 200, "message": "检查收藏状态成功", "data": FavoriteCheckResponse(isFavorite=is_favorited)}


@router.post("/add", response_model=APIResponse[FavoriteAddResponse])
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await favorite.add_news_favorite(db, user.id, data.news_id)
    return {"code": 200, "message": "添加收藏成功", "data": FavoriteAddResponse.model_validate(result)}


@router.delete("/remove", response_model=APIResponse)
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await favorite.remove_news_favorite(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏记录不存在")
    return {"code": 200, "message": "删除收藏成功", "data": None}


@router.get("/list", response_model=APIResponse[FavoriteListResponse])
async def get_favorite_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    # 显式字段映射（不展开 ORM __dict__，避免带出 _sa_instance_state 等内部属性）
    favorite_list = [
        FavoriteNewsItemResponse.model_validate({
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "image": n.image,
            "author": n.author,
            "category_id": n.category_id,
            "views": n.views,
            "publish_time": n.publish_time,
            "favorite_id": fid,
            "favorite_time": ft,
        })
        for n, ft, fid in rows
    ]
    has_more = total > page * page_size

    data = FavoriteListResponse(list=favorite_list, total=total, hasMore=has_more)
    return {"code": 200, "message": "获取收藏列表成功", "data": data}


@router.delete("/clear", response_model=APIResponse)
async def clear_favorite(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    count = await favorite.remove_all_favorites(db, user.id)
    return {"code": 200, "message": f"清空了{count}条记录", "data": None}
