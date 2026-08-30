import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security


# 根据用户名查询数据库
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先密码加密处理 → add
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)  # 从数据库读回最新的 user
    return user


# 生成 Token
async def create_token(db: AsyncSession, user_id: int):
    # 生成 Token + 设置过期时间 → 查询数据库当前用户是否有 Token → 有：更新；没有：添加
    token = str(uuid.uuid4())
    # timedelta(days=7, hours=2, minutes=30, seconds=10)
    expires_at = datetime.now() + timedelta(days=7)

    # 顺手清理已过期的令牌，避免 user_token 表无限膨胀
    await db.execute(delete(UserToken).where(UserToken.expires_at < datetime.now()))

    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    # 库里只存令牌摘要，原始 token 仅在登录响应中返回一次
    token_digest = security.hash_token(token)
    if user_token:
        user_token.token = token_digest
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token_digest, expires_at=expires_at)
        db.add(user_token)
    # 两个分支统一显式提交：本函数可能在请求上下文之外复用（脚本/后台任务），
    # 不能依赖 get_db 的收尾 commit，否则更新分支不会落库
    await db.commit()

    return token


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None

    return user


# 根据 Token 查询用户：验证 Token → 查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    # 请求头里的原始 token 摘要后与库中比对
    query = select(UserToken).where(UserToken.token == security.hash_token(token))
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():
        return None

    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息: update更新 → 检查是否命中 → 获取更新后的用户返回（未命中返回 None，由路由层翻译 404）
async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    query = update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result = await db.execute(query)
    await db.commit()

    # 检查更新：0 行命中 = 用户不存在；crud 层不懂 HTTP，不抛 Web 异常
    if result.rowcount == 0:
        return None

    # 获取一下更新后的用户
    updated_user = await get_user_by_username(db, username)
    return updated_user


# 修改密码: 验证旧密码 → 新密码加密 → 修改密码
async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str):
    if not security.verify_password(old_password, user.password):
        return False

    hashed_new_pwd = security.get_hash_password(new_password)
    user.password = hashed_new_pwd
    # 更新: 由SQLAlchemy真正接管这个 User 对象，确保可以 commit
    # 规避 session 过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
