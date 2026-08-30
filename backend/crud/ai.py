from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai import AIChat


# 保存一条对话（用户消息 + AI 回复）
async def save_chat(db: AsyncSession, user_id: int, message: str, response: str):
    record = AIChat(user_id=user_id, message=message, response=response)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# 获取某用户的聊天历史（按时间正序返回，最多 limit 条）
async def get_chat_history(db: AsyncSession, user_id: int, limit: int = 20):
    query = (select(AIChat)
             .where(AIChat.user_id == user_id)
             .order_by(AIChat.created_at.desc(), AIChat.id.desc())
             .limit(limit))
    result = await db.execute(query)
    records = result.scalars().all()
    return list(reversed(records))
