import json
import logging

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.ai_conf import AI_BASE_URL, AI_HEADERS, AI_MODEL, AI_PROVIDER
from config.db_conf import get_db
from crud import ai as ai_crud
from models.users import User
from schemas.ai import AIChatHistoryResponse, AIChatRecordResponse, AIChatRequest
from schemas.response import APIResponse
from utils.auth import get_current_user

logger = logging.getLogger("app.ai")

router = APIRouter(prefix="/api/ai", tags=["ai"])

# 透传给模型的历史对话上限，控制 token 消耗
HISTORY_LIMIT = 10


def _build_payload(messages):
    payload = {"model": AI_MODEL, "messages": messages, "stream": True}
    # 关闭深度思考，答案直接流式输出（仅智谱 GLM 系列识别该参数）
    if AI_PROVIDER == "zhipu":
        payload["thinking"] = {"type": "disabled"}
    return payload


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(
        data: AIChatRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    AI 问答（SSE 流式）：代理第三方模型服务，密钥由后端 .env 管理，对话落库 ai_chat 表
    """
    history = [m.model_dump() for m in data.history[-HISTORY_LIMIT:]]
    messages = history + [{"role": "user", "content": data.message}]
    payload = _build_payload(messages)

    async def event_stream():
        ai_response = ""
        try:
            timeout = httpx.Timeout(60.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", AI_BASE_URL, headers=AI_HEADERS, json=payload) as resp:
                    if resp.status_code != 200:
                        body = (await resp.aread()).decode("utf-8", "ignore")
                        logger.warning("AI 服务返回 %s：%s", resp.status_code, body[:200])
                        yield _sse({"error": f"AI 服务暂时不可用（{resp.status_code}），请稍后再试"})
                        return
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk_str = line[6:].strip()
                        if chunk_str == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        try:
                            chunk = json.loads(chunk_str)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices") or [{}]
                        content = (choices[0].get("delta") or {}).get("content") or ""
                        if content:
                            ai_response += content
                        yield _sse(chunk)
        except httpx.HTTPError as exc:
            logger.warning("AI 服务连接失败：%s", exc)
            yield _sse({"error": "AI 服务连接失败，请稍后再试"})
            return

        # 流结束后落库（get_db 的会话在响应完成后才关闭，此处可用）
        if ai_response:
            await ai_crud.save_chat(db, user.id, data.message, ai_response)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=APIResponse[AIChatHistoryResponse])
async def get_history(
        limit: int = 20,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """当前用户的 AI 聊天历史（时间正序，最多 limit 条）"""
    records = await ai_crud.get_chat_history(db, user.id, min(max(limit, 1), 100))
    data = AIChatHistoryResponse(
        list=[AIChatRecordResponse.model_validate(r) for r in records],
        total=len(records),
    )
    return {"code": 200, "message": "获取聊天历史成功", "data": data}
