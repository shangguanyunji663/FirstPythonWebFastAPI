"""密码哈希与令牌摘要工具

bcrypt 直接使用（不经过已停止维护的 passlib）：存量哈希串为 $2b$ 格式，新旧实现完全兼容，
无需迁移数据。verify 对库中非 bcrypt 格式的脏数据返回 False 而不是抛异常。
"""
import hashlib

import bcrypt


# 密码加密：bcrypt 自带盐，同一密码每次哈希结果都不同
def get_hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# 密码验证: verify 返回值是布尔型
def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


# 令牌摘要：数据库只存 SHA-256，泄露库也不会直接暴露可用的会话凭证
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
