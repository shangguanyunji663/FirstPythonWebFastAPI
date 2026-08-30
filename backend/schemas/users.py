from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class UserRequest(BaseModel):
    """注册请求：强校验（与 user 表列定义对齐）。登录走 UserLoginRequest 宽松规则，
    避免历史用户名不满足新规则时被锁在门外"""

    username: str = Field(..., min_length=4, max_length=20, pattern=r"^[a-zA-Z0-9_]+$",
                          description="用户名：4-20位字母/数字/下划线")
    password: str = Field(..., min_length=6, max_length=32, description="密码：6-32位")


class UserLoginRequest(BaseModel):
    """登录请求：仅要求非空，长度/格式规则只约束新注册"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=64, description="密码")


# user_info 对应的类：基础类 + Info 类（id、用户名）
class UserInfoBase(BaseModel):
    """
    用户信息基础数据模型
    """
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserInfoResponse(UserInfoBase):
    id: int
    username: str

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# data 数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias / 字段名兼容
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# 更新用户信息的模型类：校验与数据库列定义对齐，gender 限定枚举值
class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[Literal["male", "female", "unknown"]] = Field(None, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")


class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword", description="旧密码")
    new_password: str = Field(..., min_length=6, alias="newPassword", description="新密码")
