import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
import redis.asyncio as redis

logger = logging.getLogger("app.cache")

load_dotenv()  # 读取 backend/.env（该文件不入库，模板见 .env.example）

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None


# 创建 Redis 的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址
    port=REDIS_PORT,  # Redis 端口号
    db=REDIS_DB,  # Redis 数据库编号，0~15
    password=REDIS_PASSWORD,  # 未设置密码时为 None
    socket_timeout=2,  # 读写超时，避免 Redis 故障时请求长时间挂起
    socket_connect_timeout=2,  # 建连超时
    decode_responses=True  # 是否将字节数据解码为字符串
)


# 设置 和 读取（字符串 和 列表或字典）"[{}]"
# 读取：字符串
async def get_cache(key: str):
    # return await redis_client.get(key)
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning("获取缓存失败：%s", e)
        return None


# 读取：列表或字典
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)  # 序列化
        return None
    except Exception as e:
        logger.warning("获取 JSON 缓存失败：%s", e)
        return None


# 设置缓存 setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        if isinstance(value, (dict, list)):
            # 转字符串再存
            value = json.dumps(value, ensure_ascii=False)  # 中文正常保存
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        logger.warning("设置缓存失败：%s", e)
        return False


# 删除单个缓存 key
async def delete_cache(key: str) -> bool:
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning("删除缓存失败：%s", e)
        return False


# 按前缀批量删除缓存（scan_iter 渐进扫描，不阻塞 Redis）
async def delete_cache_pattern(pattern: str) -> int:
    deleted = 0
    try:
        async for key in redis_client.scan_iter(match=pattern, count=100):
            await redis_client.delete(key)
            deleted += 1
    except Exception as e:
        logger.warning("按前缀删除缓存失败：%s", e)
    return deleted
