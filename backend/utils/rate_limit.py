import time
from collections import defaultdict, deque

from fastapi import HTTPException
from starlette import status

# 轻量登录限流：单进程内存实现，适合教学/单实例部署
# 生产多实例部署需换 Redis 等共享存储
_WINDOW_SECONDS = 60
_MAX_ATTEMPTS = 5

# key -> 最近尝试时间戳队列
_attempts: dict = defaultdict(deque)


def check_login_rate_limit(key: str):
    """同一用户名 60 秒内最多允许 5 次登录尝试，超限抛 429"""
    now = time.monotonic()
    queue = _attempts[key]
    while queue and now - queue[0] > _WINDOW_SECONDS:
        queue.popleft()
    if len(queue) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试过于频繁，请稍后再试"
        )
    queue.append(now)


def reset_login_attempts(key: str):
    """登录成功后清空该用户的尝试记录"""
    _attempts.pop(key, None)
