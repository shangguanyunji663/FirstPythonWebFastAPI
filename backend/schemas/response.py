from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一响应包络：所有接口返回 {code, message, data} 三键结构"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
