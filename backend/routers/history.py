from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import history
from models.users import User
from schemas.history import HistoryAddRequest, HistoryAddResponse, HistoryListResponse, HistoryNewsItemResponse
from schemas.response import APIResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/add", response_model=APIResponse[HistoryAddResponse])
async def add_history(data: HistoryAddRequest,
                      user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """
    添加历史记录
    """
    result = await history.add_history(db, user.id, data.news_id)
    return {"code": 200, "message": "添加成功", "data": HistoryAddResponse.model_validate(result)}


@router.get("/list", response_model=APIResponse[HistoryListResponse])
async def get_history_list(page: int = Query(1, ge=1),
                           page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """
    获取历史记录列表
    """
    rows, total = await history.get_history_list(db, user.id, page, page_size)

    has_more = total > page * page_size

    # 显式字段映射（不展开 ORM __dict__，避免带出 _sa_instance_state 等内部属性）
    history_list = [
        HistoryNewsItemResponse.model_validate({
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "image": n.image,
            "author": n.author,
            "category_id": n.category_id,
            "views": n.views,
            "publish_time": n.publish_time,
            "history_id": hid,
            "view_time": vt,
        })
        for n, vt, hid in rows
    ]

    data = HistoryListResponse(list=history_list, total=total, hasMore=has_more)

    return {"code": 200, "message": "success", "data": data}


@router.delete("/delete/{history_id}", response_model=APIResponse)
async def delete_history(history_id: int,
                         user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    """
    删除历史记录
    """
    result = await history.delete_history(db, user.id, history_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="历史记录不存在")
    return {"code": 200, "message": "删除成功", "data": None}


@router.delete("/clear", response_model=APIResponse)
async def clear_history(user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """
    清空历史记录
    """
    count = await history.clear_history(db, user.id)
    return {"code": 200, "message": f"清空成功，共{count}条", "data": None}
