from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.news import News


class RelatedNews(Base):
    """
    相关新闻关联表ORM模型
    """
    __tablename__ = 'related_news'

    # 创建索引
    __table_args__ = (
        UniqueConstraint('news_id', 'related_news_id', name='news_related_unique'),
        Index('fk_related_news_news_idx', 'news_id'),
        Index('fk_related_news_related_idx', 'related_news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="关联ID")
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="新闻ID")
    related_news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="相关新闻ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<RelatedNews(id={self.id}, news_id={self.news_id}, related_news_id={self.related_news_id})>"
