from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class AIChatMessage(BaseModel):
    """历史对话中的一条消息"""
    role: str
    content: str


class AIChatRequest(BaseModel):
    """AI 问答请求体"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    history: List[AIChatMessage] = Field(default_factory=list, description="历史对话，最近若干条")


class AIChatRecordResponse(BaseModel):
    """单条聊天记录响应"""
    id: int
    message: str
    response: str
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AIChatHistoryResponse(BaseModel):
    """聊天历史响应"""
    list: List[AIChatRecordResponse]
    total: int
