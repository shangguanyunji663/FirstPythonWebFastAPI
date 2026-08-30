from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crawler.rss_service import crawl_all
from models.users import User
from schemas.response import APIResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/crawler", tags=["crawler"])


@router.post("/run", response_model=APIResponse)
async def run_crawler(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """手动触发一次 RSS 抓取（需登录）；定时任务由 main.py lifespan 启动"""
    stats = await crawl_all(db)
    return {
        "code": 200,
        "message": f"抓取完成：获取 {stats['fetched']} 条，新增 {stats['inserted']} 条",
        "data": stats,
    }
