from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users
from models.users import User
from schemas.response import APIResponse
from schemas.users import (
    UserAuthResponse,
    UserChangePasswordRequest,
    UserInfoResponse,
    UserLoginRequest,
    UserRequest,
    UserUpdateRequest,
)
from utils.auth import get_current_user
from utils.rate_limit import check_login_rate_limit, reset_login_attempts

router = APIRouter(prefix="/api/user", tags=["users"])


@router.post("/register", response_model=APIResponse[UserAuthResponse])
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 注册逻辑：验证用户是否存在 -> 创建用户 → 生成 Token  → 响应结果
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")
    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    return {
        "code": 200,
        "message": "注册成功",
        "data": UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user)),
    }


@router.post("/login", response_model=APIResponse[UserAuthResponse])
async def login(user_data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑：限流检查 -> 验证用户是否存在 -> 验证密码 -> 生成 Token  → 响应结果
    check_login_rate_limit(user_data.username)
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    reset_login_attempts(user_data.username)
    token = await users.create_token(db, user.id)
    return {
        "code": 200,
        "message": "登录成功啦",
        "data": UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user)),
    }


# 查Token查用户 → 封装crud → 功能整合成一个工具函数 → 路由导入使用: 依赖注入
@router.get("/info", response_model=APIResponse[UserInfoResponse])
async def get_user_info(user: User = Depends(get_current_user)):
    return {"code": 200, "message": "获取用户信息成功", "data": UserInfoResponse.model_validate(user)}


# 修改用户信息：验证Token → 更新（用户输入数据 put 提交 → 请求体参数 → 定义Pydantic模型类） → 响应结果
@router.put("/update", response_model=APIResponse[UserInfoResponse])
async def update_user_info(user_data: UserUpdateRequest, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    user = await users.update_user(db, user.username, user_data)
    return {"code": 200, "message": "更新用户信息成功", "data": UserInfoResponse.model_validate(user)}


@router.put("/password", response_model=APIResponse)
async def update_password(
        password_data: UserChangePasswordRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:
        # 旧密码错误属于客户端输入问题，返回 400 而非 500
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")
    return {"code": 200, "message": "修改密码成功", "data": None}
