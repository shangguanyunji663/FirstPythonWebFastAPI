import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.db_conf import AsyncSessionLocal
from crawler.rss_service import crawl_all
from crawler.sources import CRAWL_INTERVAL_HOURS, CRAWLER_ENABLED_ENV
from routers import ai, crawler, favorite, history, news, users
from utils.exception_handlers import register_exception_handlers

# 日志配置：级别走环境变量（DEBUG/INFO/WARNING...），默认 INFO
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

crawler_logger = logging.getLogger("app.crawler")
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def crawl_job():
    """定时抓取任务：自建会话；失败只记日志，不影响下一轮调度"""
    try:
        async with AsyncSessionLocal() as db:
            stats = await crawl_all(db)
        crawler_logger.info("定时抓取完成：%s", stats)
    except Exception:
        crawler_logger.exception("定时抓取任务失败")


@asynccontextmanager
async def lifespan(app):
    """应用启动时注册定时抓取（先抓一次，之后按固定间隔轮询）；
    设置 CRAWLER_ENABLED=false 可整体关闭（如开发环境反复热重载时）"""
    if os.getenv(CRAWLER_ENABLED_ENV, "true").lower() == "true":
        scheduler.add_job(
            crawl_job, "interval", hours=CRAWL_INTERVAL_HOURS,
            id="news_crawler", next_run_time=datetime.now(),
        )
        scheduler.start()
        crawler_logger.info("定时抓取已启动，间隔 %s 小时", CRAWL_INTERVAL_HOURS)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

# 注册异常处理器
register_exception_handlers(app)


# 开发环境放开所有源；生产环境必须配置 CORS_ORIGINS 白名单（逗号分隔）
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    cors_origins = ["*"]
    cors_credentials = False  # 通配源不允许携带凭证，二者不可同时开启
else:
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # 允许的源
    allow_credentials=cors_credentials,  # 是否允许携带cookie
    allow_methods=["*"],     # 允许的请求方法
    allow_headers=["*"],     # 允许的请求头
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "ok"}

# 挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(ai.router)
app.include_router(crawler.router)
