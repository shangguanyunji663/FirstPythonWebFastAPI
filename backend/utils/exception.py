import os
import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

# 调试模式：开启时异常详情（含堆栈）会返回给客户端，仅限本地开发使用
# 通过环境变量 DEBUG_MODE 控制，默认关闭，避免泄露 SQL、路径等内部信息
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 唯一约束名 -> 用户提示文案（与 database.sql / models 中的约束名对应）
CONSTRAINT_MESSAGES = {
    "username_UNIQUE": "用户名已存在",
    "phone_UNIQUE": "手机号已被注册",
    "token_UNIQUE": "令牌生成冲突，请重试",
    "name_UNIQUE": "分类名称已存在",
    "user_news_unique": "已收藏过该新闻",
    "news_related_unique": "关联新闻记录重复",
}


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 HTTPException 异常
    """
    # HTTPException 通常是业务逻辑主动抛出的，data 保持 None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    处理数据库完整性约束错误
    """
    error_msg = str(exc.orig)

    # 先按具体约束名精确映射，再兜底通用判断
    detail = next((msg for name, msg in CONSTRAINT_MESSAGES.items() if name in error_msg), None)
    if detail is None:
        if "Duplicate entry" in error_msg:
            detail = "数据已存在，请勿重复提交"
        elif "FOREIGN KEY" in error_msg:
            detail = "关联数据不存在"
        else:
            detail = "数据约束冲突，请检查输入"

    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": "IntegrityError",
            "error_detail": error_msg,
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "message": detail,
            "data": error_data
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    处理 SQLAlchemy 数据库错误
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": error_data
        }
    )



