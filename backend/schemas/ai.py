from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIChatMessage(BaseModel):
    """历史对话中的一条消息：role 白名单防伪造 system 角色注入，content 限长控 token 成本"""
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class AIChatRequest(BaseModel):
    """AI 问答请求体"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    history: list[AIChatMessage] = Field(default_factory=list, description="历史对话，最近若干条")


class AIChatRecordResponse(BaseModel):
    """单条聊天记录响应"""
    id: int
    message: str
    response: str
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AIChatHistoryResponse(BaseModel):
    """聊天历史响应"""
    list: list[AIChatRecordResponse]
    total: int
