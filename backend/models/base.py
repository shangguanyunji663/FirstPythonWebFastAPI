from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """全项目唯一的 DeclarativeBase：所有模型共用同一个 metadata，
    跨表外键才能正确挂到统一元数据上（也是后续建表/迁移的前提）"""
    pass


class TimestampMixin:
    """通用时间列混入：需要 created_at / updated_at 的表直接继承"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
