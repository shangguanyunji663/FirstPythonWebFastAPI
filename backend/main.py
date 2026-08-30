import logging
import os

from fastapi import FastAPI
from routers import ai, favorite, history, news, users
from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handlers import register_exception_handlers

# 日志配置：级别走环境变量（DEBUG/INFO/WARNING...），默认 INFO
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI()

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
