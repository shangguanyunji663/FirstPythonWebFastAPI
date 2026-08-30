import hashlib

from passlib.context import CryptContext

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 密码加密
def get_hash_password(password: str):
    return pwd_context.hash(password)


# 密码验证: verify 返回值是布尔型
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# 令牌摘要：数据库只存 SHA-256，泄露库也不会直接暴露可用的会话凭证
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
