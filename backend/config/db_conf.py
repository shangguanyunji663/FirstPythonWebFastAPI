import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

load_dotenv()  # 读取 toutiao_backend/.env（该文件不入库，模板见 .env.example）

# 数据库连接配置：从环境变量读取，避免凭据硬编码入库
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "news_app")

# 数据库URL
ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # 输出SQL日志，默认关闭
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20  # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
