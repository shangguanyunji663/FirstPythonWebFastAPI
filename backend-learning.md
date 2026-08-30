# 后端学习文档：从零复现「AI 头条新闻系统」

> **这份文档是写给谁的**：只会 Python 基础语法（变量、函数、类、装饰器听过但未必熟练），没接触过 Web 开发、数据库、缓存的初学者。
>
> **这份文档能做什么**：带你按"如果是你自己从零写这个项目，应该按什么顺序想、按什么顺序写"的逻辑，把 `backend/` 目录下的后端完整复现一遍。每一章都是：**为什么需要它（概念）→ 本项目怎么做的（对照真实代码）→ 你动手写什么（复现要点）**。
>
> **怎么用**：左手开这份文档，右手开编辑器里的 `backend/` 目录，边读边对照。读完一章就自己在空目录里敲出对应的那一层，跑通再进下一章。前端不是重点，只在第 19 章讲"你的后端会被谁调用、怎么调"，其他章节不依赖前端知识。

---

## 目录

- [1. 项目是什么：一个新闻系统的后端](#1-项目是什么一个新闻系统的后端)
- [2. 技术栈地图：每个东西是干嘛的](#2-技术栈地图每个东西是干嘛的)
- [3. 环境搭建与第一次启动](#3-环境搭建与第一次启动)
- [4. 复现路线总览](#4-复现路线总览)
- [5. 第一步：最小的 FastAPI 应用](#5-第一步最小的-fastapi-应用)
- [6. 分层架构：目录设计与一次请求的旅程](#6-分层架构目录设计与一次请求的旅程)
- [7. 配置层：config/](#7-配置层config)
- [8. 模型层：models/](#8-模型层models)
- [9. 校验层：schemas/](#9-校验层schemas)
- [10. 数据访问层：crud/（从 users 开始）](#10-数据访问层crud从-users-开始)
- [11. 密码安全：utils/security.py](#11-密码安全utilsecuritypy)
- [12. 用户路由：routers/users.py 与统一响应](#12-用户路由routersuserspy-与统一响应)
- [13. 认证体系：token 表方案](#13-认证体系token-表方案)
- [14. 新闻模块：关联表、分页与缓存版查询](#14-新闻模块关联表分页与缓存版查询)
- [15. 缓存体系：穿透、雪崩与一致性](#15-缓存体系穿透雪崩与一致性)
- [16. 全局异常处理：utils/exception.py](#16-全局异常处理utilsexceptionpy)
- [17. 收藏与历史模块：join 查询与唯一约束](#17-收藏与历史模块join-查询与唯一约束)
- [18. 组装：main.py（路由、CORS、日志）](#18-组装mainpy路由cors日志)
- [19. 前端对接点速览](#19-前端对接点速览)
- [20. 调试与排错手册](#20-调试与排错手册)
- [21. 已知设计取舍与进阶方向](#21-已知设计取舍与进阶方向)
- [附录 A：复现检查清单](#附录-a复现检查清单)
- [附录 B：术语表](#附录-b术语表)

---

## 1. 项目是什么：一个新闻系统的后端

这是一个仿"今日头条"的新闻系统，**本仓库的主角是它的后端 API 服务**。它对外提供 17 个 HTTP 接口，分为 4 组：

| 模块 | 功能 | 接口数 |
|------|------|--------|
| 用户 | 注册、登录、查信息、改资料、改密码 | 5 |
| 新闻 | 分类列表、新闻列表（分页）、新闻详情（浏览量+1） | 3 |
| 收藏 | 检查/添加/取消/列表/清空 | 5 |
| 历史 | 添加/列表/删除单条/清空 | 4 |

完整的接口定义（路径、参数、响应示例）在 `docs/api-spec.md`，这里是你的"验收标准"——你复现的每个接口都应与它一致。

**一句话概括架构**：浏览器里的 Vue 前端发 HTTP 请求 → FastAPI 接住请求 → 经过校验和认证 → 通过 SQLAlchemy 查 MySQL（能命中 Redis 缓存就不查库）→ 把结果包成统一格式的 JSON 返回。

---

## 2. 技术栈地图：每个东西是干嘛的

零基础最大的困惑是"一坨名词各管什么"。逐个说清：

| 名词 | 它是什么 | 不用它你就要手工做什么 |
|------|----------|------------------------|
| **FastAPI** | Python 的 Web 框架，负责"接收 HTTP 请求、返回响应" | 自己解析 HTTP 报文、自己写路由分发 |
| **uvicorn** | Web 服务器，真正监听 8000 端口的程序，FastAPI 挂在它上面运行 | 自己实现 TCP/HTTP 协议 |
| **Pydantic (v2)** | 数据校验库：声明"这个接口需要什么字段、什么类型"，不符合自动报错 | 请求进来后手动 `if not isinstance(...)` 一层层检查 |
| **MySQL** | 关系型数据库，数据真正存放的地方 | 用文件存数据然后自己维护一致性 |
| **SQLAlchemy (2.0)** | ORM：用 Python 类和对象操作数据库，不用手写 SQL 字符串 | 手写 SQL 拼接并小心 SQL 注入 |
| **aiomysql** | MySQL 的**异步**驱动，SQLAlchemy 通过它发请求 | —— |
| **redis** | 内存键值数据库，本项目用作**缓存**（高频数据先问 Redis，没有再查 MySQL） | 每个请求都打数据库，量大就拖垮 |
| **passlib + bcrypt** | 密码哈希：存"不可逆的指纹"而不是明文密码 | 数据库泄露=全部明文密码泄露 |
| **python-dotenv** | 从 `.env` 文件读配置（数据库密码等），避免写死在代码里 | 密码提交进代码仓库 |

**两个零基础必须先建立的观念**：

1. **同步 vs 异步**：同步代码一行干完再干下一行；`await` 表示"这一步要等 IO（网络/磁盘），等待期间先去处理别的请求"。数据库查询、Redis 读写都是 IO，所以本项目全线 `async def` + `await`。FastAPI 的异步能力 + aiomysql 的异步驱动 + `AsyncSession` 三者配套，缺一个就退化成同步阻塞。
2. **前后端分离**：后端只负责"响应 JSON 数据"，不生成 HTML 页面；页面渲染由独立的前端（Vue）负责。两者之间只靠 HTTP + JSON 交流，所以开发时各自独立启动、靠接口文档对齐。

---

## 3. 环境搭建与第一次启动

> 目标：把别人的项目跑起来，你才有"对照物"。

```bash
# 1. 创建项目内独立的 conda 环境（不污染本机 Anaconda base）
cd backend
conda env create -f environment.yml -p .conda-env

# 2. 配置环境变量：复制模板
cp .env.example .env        # Windows Git Bash 用 cp；PowerShell 用 copy

# 3. 初始化数据库（建 news_app 库 + 8 张表 + 示例数据）
mysql -uroot -p < ../database/database.sql

# 4. 启动
conda activate ./.conda-env
uvicorn main:app --reload
```

打开 `http://127.0.0.1:8000/docs`——这是 FastAPI **自动生成**的交互式接口文档，所有接口可以直接在网页上填参数调试。**它是你复现过程中最重要的自测工具**。

`.env` 里每个变量改了会发生什么，见第 7 章。

---

## 4. 复现路线总览

不要按文件名字母序写，要按**依赖关系**写：被依赖的先写，每写完一层都能独立验证。

| 步骤 | 写什么 | 验证方式 |
|------|--------|----------|
| 1 | `main.py` 最小骨架 | 浏览器访问 `/` 返回 JSON |
| 2 | `config/db_conf.py` | Python 里能建 engine 不报错 |
| 3 | `models/` 全部模型 | import 无报错 |
| 4 | `schemas/` 全部校验模型 | import 无报错 |
| 5 | `utils/`（security/response） | 单独调用函数测哈希 |
| 6 | `crud/users.py` | 用临时脚本调函数，库里能查到新用户 |
| 7 | `routers/users.py` + 挂路由 | `/docs` 里注册登录走通 |
| 8 | `utils/auth.py` | 带/不带 token 调 `/api/user/info` |
| 9 | `models/news.py`、`crud/news_cache.py`、`routers/news.py` | 新闻三接口走通 |
| 10 | `cache/news_cache.py` + Redis 配置 | 断开 Redis 再请求，应降级不报错 |
| 11 | `utils/exception*.py` | 故意插重复用户名，看 400 文案 |
| 12 | `crud/favorite.py`、`history.py` 及路由 | 收藏/历史全流程走通 |
| 13 | `main.py` 收尾（CORS、日志） | 前端能跨域调用 |

**每章末尾的"复现要点"就对应上表的一格。**

---

## 5. 第一步：最小的 FastAPI 应用

**概念**：Web 框架的核心工作就两件——"某个路径的请求来了，执行哪个函数"（路由分发），以及"把函数返回值变成 HTTP 响应"。

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")          # 装饰器：把下面的函数注册为 GET / 的处理器
async def root():
    return {"message": "Hello World"}   # 返回 dict，FastAPI 自动转 JSON
```

四个知识点：

1. `@app.get("/")` 是**装饰器**语法：它把 `root` 函数挂到路由表上。`get` 是 HTTP 方法，还可以 `post`（创建）、`put`（更新）、`delete`（删除）。
2. `async def` 声明异步函数。函数体里凡是 IO 操作（查库、读缓存）都要 `await`。普通计算不需要。
3. 返回 dict 会自动序列化成 JSON，`Content-Type` 自动是 `application/json`。
4. `uvicorn main:app --reload` 的意思是"启动服务器，应用对象在 main.py 里叫 app，代码改动自动重启"。`--reload` 只用于开发。

**复现要点**：新建空目录，写出上面 7 行，`uvicorn main:app` 跑起来，浏览器访问 `http://127.0.0.1:8000/` 和 `/docs`。对照项目 `backend/main.py` 里的 `root()`——一模一样。

---

## 6. 分层架构：目录设计与一次请求的旅程

**为什么要分层**：如果所有代码堆在 main.py，500 行后就没法维护。本项目按"职责"切层：

```
backend/
├── main.py          # 入口：创建 app、装中间件、注册路由
├── routers/         # 路由层：定义 URL、校验入参、调 crud、组织响应（只管"接客"）
├── schemas/         # 校验层：每个接口的入参/出参数据形状（只管"格式"）
├── crud/            # 数据访问层：所有数据库读写（只管"数据怎么来"）
├── models/          # 模型层：数据库表在 Python 里的映射（只管"表长什么样"）
├── cache/           # 缓存键与读写封装（只管"Redis 怎么用"）
├── config/          # 配置：数据库/Redis 连接（只管"连到哪"）
└── utils/           # 横切工具：认证、密码哈希、限流、异常处理
```

**依赖方向必须是单向的**：`routers → crud → models`。反向依赖（crud 里 import routers）是架构坏味道——本项目唯一一处反例是 `crud/users.py:90` 抛了 Web 层的 `HTTPException`，属于历史遗留（见第 21 章）。

**一次"GET /api/news/list?categoryId=1&page=1"的完整旅程**（记住这条线，后面每章都是线上的一站）：

```
浏览器请求
  → main.py 路由表找到 routers/news.py 的 get_news_list
  → FastAPI 校验查询参数（categoryId 必填、page≥1……）
  → 依赖注入系统先准备 db 会话（config/db_conf.py 的 get_db）
  → crud/news_cache.py.get_news_list：先问 Redis（cache/news_cache.py）
       命中 → 直接返回
       未命中 → 查 MySQL（models/news.py 定义的表）→ 结果写回 Redis
  → crud.get_news_count_cached 拿总数
  → 路由层拼 {list, total, hasMore} 返回
  → get_db 收尾：commit / rollback / close
```

**复现要点**：先只建目录和空 `__init__.py`（`touch routers/__init__.py crud/__init__.py ...`）。Python 把含 `__init__.py` 的目录当"包"，这样 `from routers import news` 才是明确的包导入。

---

## 7. 配置层：config/

**概念**：数据库地址、密码这类"因环境而异、且敏感"的信息不该写在代码里——换台机器要改代码、提交仓库会泄露。方案：写在 `.env` 文件里（不进 git），代码启动时读环境变量。

**本项目做法**（`backend/.env` + `backend/.env.example` 模板）：

```bash
# backend/.env（已被 .gitignore 忽略，不会提交）
DEBUG_MODE=false
DB_USER=root
DB_PASSWORD=你的密码
DB_HOST=localhost
DB_PORT=3306
DB_NAME=news_app
SQL_ECHO=false
LOG_LEVEL=INFO
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CORS_ORIGINS=
```

`config/db_conf.py` 读取并创建**异步引擎**：

```python
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

load_dotenv()  # 把 .env 内容加载进环境变量

DB_USER = os.getenv("DB_USER", "root")        # 第二个参数是缺省值
...
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # true 时打印每条 SQL
    pool_size=10,        # 常驻连接数
    max_overflow=20,     # 高峰可临时多开的连接数
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
```

知识点：

- **连接池**：TCP 连接建一次很贵，`pool_size=10` 意思是常备 10 条连接复用，突发流量再临时开最多 20 条。
- **expire_on_commit=False**：commit 之后 ORM 对象属性不立刻"过期"。不关的话，commit 后再访问对象属性会触发一次新的隐式查询，异步下很容易踩坑。
- **`get_db`——FastAPI 的"依赖注入"**：

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session                # 把 session 交给路由函数用
            await session.commit()       # 路由函数正常跑完 → 提交
        except Exception:
            await session.rollback()     # 出错 → 回滚
            raise
        finally:
            await session.close()        # 无论如何 → 归还连接
```

路由里写 `db: AsyncSession = Depends(get_db)`，FastAPI 就会在**每个请求**进来时执行 `get_db` 到 `yield` 为止、把 session 递给你，请求结束后自动执行 yield 之后的收尾。"开头准备、结尾清理"的逻辑全部由框架托管，你不用在每个接口里手动开关连接。

- `config/cache_conf.py` 同理：读 Redis 配置建 `redis_client`，另外加了 `socket_timeout=2`（Redis 挂了 2 秒就失败，别让请求挂着）。

**复现要点**：写出 `.env.example` 模板 → `db_conf.py` → 单独跑 `python -c "from config.db_conf import async_engine; print(async_engine.url)"` 验证连接串拼接正确（此时尚未真正连库，engine 是惰性的）。

---

## 8. 模型层：models/

**概念**：ORM = "表 ↔ Python 类"的映射。一个类 = 一张表，一个对象 = 一行记录，类的属性 = 列。好处：不用手写 SQL、自带防注入（参数自动绑定）、类型有提示。

**语法（SQLAlchemy 2.0 推荐写法）**，以 `models/users.py` 为例：

```python
class User(Base):
    __tablename__ = 'user'                      # 对应表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    gender: Mapped[Optional[str]] = mapped_column(Enum('male', 'female', 'unknown'), default='unknown')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)   # 注意：没有括号！
```

逐个拆解：

- `Mapped[int]`：类型注解，说明这一列在 Python 里是什么类型。
- `mapped_column(...)`：列约束。`primary_key` 主键；`unique=True` 唯一（重复插入报错）；`nullable=False` 不许空；`comment` 写进建表语句的注释；`default` 插入时没给值就用的默认值。
- `Enum('male','female','unknown')`：这列只能是这三个值之一，数据库层面就拦住脏数据。

**本项目的一个关键设计：全项目只有一个 `Base`**（`models/base.py`）：

```python
class Base(DeclarativeBase):
    """所有模型共用同一个 metadata"""
    pass

class TimestampMixin:
    """需要 created_at / updated_at 的表直接继承"""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
```

每个模型文件 `from models.base import Base`。**为什么强调"一个"**：`DeclarativeBase` 子类自带一张"注册表"（metadata），记录它知道的所有表。跨文件的外键（如 favorite 表指向 user、news 表）必须落在同一张 metadata 上才能成立。本项目早期每个文件各建一个 Base，是重构掉的真实坏味道。`TimestampMixin` 则演示了**混入（Mixin）**：把公共列抽出来，`class News(Base, TimestampMixin)` 一继承就带上两个时间列。

**跨表引用**：`models/favorite.py` 里 `ForeignKey(User.id)`、`ForeignKey(News.id)` 直接引用其他文件的模型——这就是统一 metadata 之后才可能的事。`unique=True`、`UniqueConstraint('user_id','news_id', name='user_news_unique')`（多列联合唯一）在数据库层面防止"重复收藏"。

**⚠️ 本项目真实踩过的坑（务必记住）**：

```python
created_at = mapped_column(DateTime, default=datetime.now())   # ❌ 带括号
created_at = mapped_column(DateTime, default=datetime.now)     # ✅ 不带括号
```

带括号 = **在定义类的那个时刻**求值一次，之后所有插入都用这同一个固定时间；不带括号 = 传入函数本身，每次插入时才调用。这个 bug 曾导致本项目所有用户的创建时间是同一个值。

**复现要点**：写 `models/base.py` → `users.py`（User + UserToken）→ `news.py`（Category + News，继承 TimestampMixin）→ `favorite.py`、`history.py`。验证：`python -c "from models import users, news, favorite, history; print('ok')"`。本项目表结构由 `database/database.sql` 管理，模型只做映射不做建表，所以不需要跑 `create_all`。

---

## 9. 校验层：schemas/

**概念**：Pydantic 模型 = "带声明的数据形状"。请求进来，FastAPI 自动按它解析+校验 JSON；不符合就返回 422，**你的业务代码一行校验都不用写**。

以 `schemas/users.py` 为例，看四件事：

```python
class UserRequest(BaseModel):          # 注册/登录的入参
    username: str
    password: str

class UserAuthResponse(BaseModel):     # 登录成功的响应体
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., min_length=6, alias="newPassword")   # 内置校验：少于6位直接422
```

- **为什么 models 和 schemas 要分开**：`User` ORM 对象里有密码哈希、created_at 等不该出现在接口响应里的字段；而接口入参（注册）只需要 username/password 两个字段。两边形状不同、变化原因不同——强行共用一个类，早晚泄露字段。
- **`alias`**：内部用 Python 风格 `user_info`，对外 JSON 用前端习惯的 `userInfo`。`populate_by_name=True` 表示两个名字都认。
- **`from_attributes=True`**：允许"从 ORM 对象直接构造"：`UserInfoResponse.model_validate(user_orm对象)`，字段名对得上就自动搬。
- **序列化时的别名**：FastAPI 返回 Pydantic 模型时按 alias 输出，所以前端拿到的键是 `userInfo`、`hasMore`、`favoriteTime` 这类驼峰。

**⚠️ 本项目踩过的命名坑**：`schemas/base.py:15` 里 `publish_time` 的别名是 `publishedTime`（多了个 d）。别名一旦定下，前端就按它取值，后改别名=前端联调全挂。新字段起别名时想清楚。

**复现要点**：每个模块按"入参 Request + 出参 Response"各写一个。写完可以用 `UserRequest(username=1, password="x")` 试一下——`username` 传 int 会被 Pydantic 强转/报错，这就是"白拿的校验"。

---

## 10. 数据访问层：crud/（从 users 开始）

**概念**：crud 层的函数 = "对某张表的一种操作"，只收 `db` 会话和业务参数，返回 ORM 对象或标量；**不懂 HTTP**（不碰 request/response）。

`backend/crud/users.py` 覆盖了全部四种基本操作，是最佳入门样本：

```python
# 查（Read）
async def get_user_by_username(db, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()      # 恰好一行→对象；0行或多行可能→None（多于1行会抛错）

# 增（Create）
async def create_user(db, user_data: UserRequest):
    hashed_password = security.get_hash_password(user_data.password)   # 先哈希再入库！
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)                 # 进入会话（还没写库）
    await db.commit()            # 真正写库
    await db.refresh(user)       # 从库读回自增 id 等数据库生成的值
    return user

# 改（Update）
query = update(User).where(User.username == username).values(**user_data.model_dump(exclude_unset=True, exclude_none=True))
result = await db.execute(query)
await db.commit()
if result.rowcount == 0: ...     # rowcount：影响了几行，0=用户不存在

# 删（Delete）
stmt = delete(UserToken).where(...)
```

要点：

- `select(User).where(...)` 是 SQLAlchemy 的查询构造器，**不是字符串拼 SQL**。参数由框架自动绑定为占位符，SQL 注入无入口。
- `.model_dump(exclude_unset=True)`：Pydantic v2 把"用户实际传了的字段"挑出来——实现"传什么改什么"的 PATCH 语义。
- `scalar_one_or_none()`（一行或 None）与 `scalars().all()`（多行列表）是最常用的两个收尾方法；`func.count()` 配 `scalar_one()` 做计数。
- **commit 的位置**：本项目 crud 函数各自 commit（写完立刻提交）。`get_db` 结尾还有一次统一 commit，形成"双轨"。能用，但口径要心里有数（见第 21 章）。

**复现要点**：只写 `crud/users.py` 五个函数（查用户、建用户、生成 token、验密码、改密码）。验证：临时脚本 `python -m asyncio` 里 `await create_user(...)`，再用 SQL 客户端看 `user` 表多了一行、密码是 bcrypt 串而不是明文。

---

## 11. 密码安全：utils/security.py

**概念**：密码绝不能明文入库。**哈希**是单向函数：同一密码得到同一"指纹"，但无法从指纹还原密码。登录时把用户输入再哈希一次，比对两个指纹。

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash_password(password: str):
    return pwd_context.hash(password)               # 注册时：明文 → 指纹

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)   # 登录时：输入+库里指纹 → 是否匹配
```

bcrypt 自带**盐**（同样密码每次哈希结果都不同，防彩虹表），所以验证必须交给 `verify` 而不是自己再 hash 一次比对字符串。MD5/SHA1 一律不要用于密码。

**复现要点**：两行函数 + 一个自测：`get_hash_password("demo-pass-001")` 跑两次结果不同，但 `verify_password("demo-pass-001", 两次结果)` 都为 True。

---

## 12. 用户路由：routers/users.py 与统一响应

**概念**：路由层是"接待员"——声明 URL 和方法、声明参数形状（用 schemas）、调用 crud、包响应。**业务规则可以在这层，但数据库细节不在这层。**

```python
router = APIRouter(prefix="/api/user", tags=["users"])   # 本文件所有接口共享前缀

@router.post("/register", response_model=APIResponse[UserAuthResponse])   # 声明响应结构
async def register(user_data: UserRequest,                       # 请求体自动按 Pydantic 校验
                   db: AsyncSession = Depends(get_db)):          # 依赖注入拿 db 会话
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")   # 主动抛=返回错误响应
    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    return {
        "code": 200,
        "message": "注册成功",
        "data": UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user)),
    }
```

**统一响应结构**（`schemas/response.py`）：所有接口都返回 `{"code": 200, "message": "...", "data": ...}` 三键结构，前端只写一次解析逻辑：

```python
class APIResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
```

它是**泛型模型**：每个路由通过 `response_model=APIResponse[该接口的数据模型]` 声明"data 里装什么"，FastAPI 据此自动完成序列化（datetime→字符串、ORM→dict）和 OpenAPI 文档生成，且**序列化默认按 alias 输出**——这就是第 9 章别名能生效的原因。

知识点：

- `Depends(get_db)`：每个请求独立拿一个 session，见第 7 章。
- `HTTPException(status_code=..., detail=...)`：抛出后由框架接住转成错误响应；本项目用第 16 章的全局处理器把它包成统一三键格式。
- 参数来源：`POST` 请求体=Pydantic 模型参数；URL 查询参数=`Query(...)`（如 `news_id: int = Query(..., alias="newsId")`，把前端的 `newsId` 映射到内部 `news_id`）；路径参数=路径里 `{history_id}`。
- 参数校验直接写在 `Query` 里：`page: int = Query(1, ge=1)`、`page_size: int = Query(10, ge=1, le=100, alias="pageSize")`。**不写校验的代价是真实的**：本项目曾因 `page_size=0` 未拦截，`skip // limit` 直接 ZeroDivisionError 返回 500。

**复现要点**：写 `routers/users.py` 5 个接口，`main.py` 里 `app.include_router(users.router)`，去 `/docs` 把注册→登录→改密码整条链路点一遍。

---

## 13. 认证体系：token 表方案

**概念**：HTTP 无状态——服务器不记得"上一个请求是谁"。所以每次请求都要**自带身份凭证**。主流方案两种：

| 方案 | 做法 | 特点 |
|------|------|------|
| JWT | 服务器签发自包含的加密串，凭签名验真伪，**不用查库** | 无状态、可扩展，但签发后难吊销 |
| 服务端 Token（本项目） | 随机串存数据库表，每个请求查库比对 | 简单直白、可随时删行吊销；代价是每请求多一次查询 |

**本项目流程**（对零基础更友好的方案）：

```
登录成功 → crud/users.py:create_token：
    token = str(uuid.uuid4())                       # 生成随机令牌
    expires_at = datetime.now() + timedelta(days=7) # 有效期7天
    查 user_token 表：该用户已有 token → 更新值和过期时间；没有 → 插入新行
    返回 token 给前端

之后每个受保护请求 → utils/auth.py:get_current_user（它也是一个依赖）：
    authorization: str = Header(..., alias="Authorization")   # 从请求头取
    token = authorization[7:].strip() if authorization.startswith("Bearer ") else authorization.strip()
    → crud.get_user_by_token(db, token)：
        查 user_token 表 → 没查到或 expires_at < now → None
        → 再查 user 表拿用户对象
    → 拿不到用户 → 抛 401 "无效的令牌或已经过期的令牌"
```

使用方式极其优雅——**受保护的接口只要多加一个参数**：

```python
async def get_user_info(user: User = Depends(get_current_user)):
```

依赖还能嵌套：`get_current_user` 自己又 `Depends(get_db)`。FastAPI 会先解 db，再解 auth，整条链自动组装。**这就是"依赖注入"的最大价值**：认证逻辑写一次，17 个接口按需挂载。

两个实战细节：

1. `Bearer ` 前缀解析用 `startswith` 严格判断，不要用 `replace("Bearer ", "")`——后者会把 token 中间出现的 "Bearer " 也删掉（本项目真实修过的 bug）。
2. 令牌方案的取舍：每请求 2 次查库（token→user）在本项目规模可接受；换 JWT 的思路和前置条件见第 21 章。

**复现要点**：`create_token` + `get_user_by_token` + `get_current_user`，然后给 `/api/user/info` 加依赖，用 `/docs` 的 Authorize 按钮先试错误 token（401）、再试登录返回的真 token（200）。

---

## 14. 新闻模块：关联表、分页与缓存版查询

**模型**（`models/news.py`）：分类表和新闻表是典型的一对多：

```python
class Category(Base, TimestampMixin):
    __tablename__ = "news_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

class News(Base, TimestampMixin):
    __tablename__ = "news"
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),   # 按分类查是高频操作 → 建索引
        Index('idx_publish_time', 'publish_time'),      # 按时间排序 → 建索引
    )
    ...
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
```

注意 `News` 没有 `category` 关系属性，只有裸的 `category_id` 外键列——本项目刻意不用 relationship，联表全手写 join（第 17 章），好处是查询行为完全可控，代价是多写几行。

**分页查询**（`crud/news_cache.py:get_news_list`）：

```python
stmt = select(News).filter_by(category_id=category_id).offset(skip).limit(limit)
```

`offset/limit` 就是翻页的本质："跳过前 N 条，取 M 条"。路由层负责换算：`offset = (page - 1) * page_size`。**hasMore（还有没有下一页）**有两种等价写法，本项目两种都用了（新闻接口用前者，收藏/历史用后者）：

```python
has_more = (offset + len(news_list)) < total      # 已取到的 + 本页条数 < 总数
has_more = total > page * page_size               # 总数超过"前 page 页容量"
```

**浏览量自增**（`crud/news_cache.py:increase_news_views`）：

```python
stmt = update(News).filter_by(id=news_id).values(views=News.views + 1)   # 数据库端自增，非先读后写
result = await db.execute(stmt)
await db.commit()
if result.rowcount > 0:
    await invalidate_news_caches(news_id)      # 写库成功 → 失效相关缓存（第15章）
return result.rowcount > 0
```

`News.views + 1` 生成的是 SQL 表达式 `views = views + 1`，**并发下也不会丢计数**（对比"读出来+1再写回"的丢更新问题）。

**复现要点**：models/news.py → crud 的五个查询函数（先不管缓存，直接查库）→ routers/news.py 三个接口（列表、详情、分类）。`/docs` 里验证分页参数 `page=0` 返回 422 而不是 500。

---

## 15. 缓存体系：穿透、雪崩与一致性

**为什么缓存**：新闻列表/详情/分类是"读极多、改极少"的数据。每次都查 MySQL 太浪费。Redis 是内存数据库，读它比读 MySQL 快一个量级。策略：**先问 Redis，没有再查 MySQL，查到顺手写回 Redis 并设过期时间**。

`cache/news_cache.py` 集中管理所有键规则（crud 层只调函数、不拼键）：

| 键 | 内容 | 默认 TTL |
|----|------|----------|
| `news:categories` | 分类列表 | 7200s（2小时） |
| `news_list:{分类}:{页}:{大小}` | 列表页 | 1800s（30分钟） |
| `news:detail:{id}` | 新闻详情 | 300s（5分钟） |
| `news:count:{分类}` | 分类新闻总数 | 1800s |
| `news:related:{id}:{分类}` | 相关新闻 | 1800s |

数据越稳定 TTL 越长。**缓存三大经典问题及本项目解法**（面试高频，也是实际必踩）：

**① 缓存穿透**：查询"不存在的东西"（如 `id=99999999`），Redis 永远没有 → 每次都打到 MySQL。攻击者可用不存在的 id 扫你。
解法：**空结果也缓存**，但只给 60 秒（`EMPTY_TTL`），存占位标记 `{"__empty__": true}`。crud 层看到哨兵值 `EMPTY` 直接返回空，不碰数据库。新数据最多延迟 1 分钟可见，可接受。

**② 缓存雪崩**：大量键**同一时刻**集体过期，请求洪峰全部涌向 MySQL。
解法：TTL 加 ±10% 随机抖动——`_with_jitter()` 让同类键的过期时间错开。

**③ 缓存一致性**：数据库改了，缓存还是旧值。本项目策略是"写后失效"：浏览量写库成功 → `invalidate_news_caches(news_id)` 删掉该新闻的详情缓存和相关新闻缓存（列表缓存允许 TTL 内短暂滞后——每次浏览都清空全部列表缓存会让缓存形同虚设，这是明确的取舍）。

**降级**：所有 Redis 读写都包在 `try/except` 里，失败只 `logger.warning` 并返回 None——**Redis 全挂，系统退化为直连数据库，功能不中断**。缓存是加速器，不是命脉。

**复现要点**：先写 `config/cache_conf.py` 的 `get_json_cache/set_cache/delete_cache/delete_cache_pattern`（`scan_iter` 渐进扫描按前缀删，避免 `keys *` 阻塞 Redis），再写 `cache/news_cache.py` 键规则层，最后回填到第 14 章的 crud 里。验证：请求一次详情（`SQL_ECHO=true` 能看到查库日志）→ 再请求一次（无查库日志=命中缓存）→ `redis-cli` 里 `keys news:*` 看键；停掉 Redis 服务再请求（应正常返回但日志里有 warning）。

---

## 16. 全局异常处理：utils/exception.py

**概念**：业务代码里到处 `try/except` 会淹没主逻辑。FastAPI 支持**全局异常处理器**：某类异常抛出到顶层，统一由一个函数转成响应。

`utils/exception_handlers.py` 注册了 4 个，**从具体到抽象**：

```python
app.add_exception_handler(HTTPException, http_exception_handler)      # 业务主动抛的
app.add_exception_handler(IntegrityError, integrity_error_handler)    # 数据库唯一约束/外键
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # 其他数据库错误
app.add_exception_handler(Exception, general_exception_handler)       # 兜底：谁都没接住的
```

最有教学价值的是 `integrity_error_handler`：数据库的 IntegrityError 报错文本里带着**违反了哪个约束**的名字，据此映射成人话：

```python
CONSTRAINT_MESSAGES = {
    "username_UNIQUE": "用户名已存在",
    "phone_UNIQUE": "手机号已被注册",
    "user_news_unique": "已收藏过该新闻",
    ...                                                    # 与 database.sql 里的约束名一一对应
}
detail = next((msg for name, msg in CONSTRAINT_MESSAGES.items() if name in error_msg), None)
```

本项目曾把所有 Duplicate entry 一律报"用户名已存在"——收藏重复时用户看到的就是驴唇不对马嘴的提示。**错误消息是产品的一部分**。

另一个要点是 `DEBUG_MODE`：

```python
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
```

调试模式下错误响应的 `data` 里附带异常类型、详情、**完整堆栈**和请求路径（排障神器）；生产必须 false，否则数据库结构、文件路径全泄露给攻击者。

**复现要点**：写两个 handler（HTTPException + 兜底 Exception 最小可用），故意注册重复用户名触发 IntegrityError，观察 400 响应的 message 随约束名变化。

---

## 17. 收藏与历史模块：join 查询与唯一约束

这两个模块教你 ORM 的进阶三板斧：**联表、聚合、条件删除**。

**联表查询**（`crud/favorite.py:get_favorite_list`）——收藏列表要展示"新闻内容 + 收藏时间"，数据分散在两张表：

```python
# 总数：聚合函数
count_query = select(func.count()).where(Favorite.user_id == user_id)

# 列表：join + 起别名 + 排序 + 分页
query = (select(News,                                        # 主查询体：整行新闻
                Favorite.created_at.label("favorite_time"),  # 顺带取收藏时间，起别名
                Favorite.id.label("favorite_id"))            # 和收藏 id
         .join(Favorite, Favorite.news_id == News.id)        # 两表按外键连接
         .where(Favorite.user_id == user_id)
         .order_by(Favorite.created_at.desc())
         .offset(offset).limit(page_size))
result = await db.execute(query)
rows = result.all()          # [(News对象, 收藏时间, 收藏id), ...] 一次查询，无 N+1
```

"N+1 问题"顺带讲清：先查 10 条收藏、再循环 10 次查每条新闻 = 1+10 次查询；一次 join = 1 次。数据量大时是天壤之别。

**唯一约束兜住并发**（`models/favorite.py`）：`UniqueConstraint('user_id','news_id', name='user_news_unique')` 保证同一用户对同一新闻最多一条收藏。即使两个请求同时通过"查重"，数据库也会拒绝第二个——应用层查重（先查再插）永远有竞态窗口，**约束是最后防线**。违反约束时抛 IntegrityError，由第 16 章的处理器翻译成"已收藏过该新闻"。

**历史模块的两个教训**（都修过真实 bug）：

1. **删除语义要对齐文档**：`DELETE /api/history/delete/{history_id}` 曾把路径参数 `history_id` 当成 `news_id` 去匹配，删的是"该新闻的记录"。修正后按主键删并**限定归属**——`where(History.user_id == user_id, History.id == history_id)`，顺手杜绝了"删别人的历史"的水平越权。
2. **时间字段**：`view_time` 默认 `datetime.now`（不带括号，第 8 章的坑），并有 `idx_view_time` 索引支撑"按浏览时间倒序"的高频排序。

**复现要点**：models → crud（5+4 个函数）→ 路由。验证：收藏→重复收藏（400 且文案正确）→ 列表联表数据完整 → 删除别人（换个账号）的记录 id 返回 404。

---

## 18. 组装：main.py（路由、CORS、日志）

所有零件齐了，`main.py` 负责总装——它只有 50 行，但三件事都有讲究：

**① 日志**：`logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), ...)`。各模块用 `logging.getLogger("app.cache")` 拿自己的 logger。对比 `print`：日志有级别、时间戳、来源，可统一开关（这就是为什么第 15 章的降级警告不是 print）。

**② CORS 中间件**——前后端分离必然遇到的问题：

```python
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    cors_origins = ["*"]; cors_credentials = False   # 开发：全放开
else:
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    cors_credentials = True                           # 生产：白名单
```

浏览器同源策略默认禁止 A 网站的页面 JS 请求 B 网站的接口；CORS 是服务器"声明允许谁来调"的机制。**易错点**：`allow_origins=["*"]` 与 `allow_credentials=True` 不能同时用（HTTP 规范禁止通配源携带凭证），所以开发模式必须把 credentials 关掉。

**③ 注册路由与异常处理器**：

```python
register_exception_handlers(app)      # 第16章
app.include_router(news.router)       # 第12-17章的所有 router
app.include_router(users.router)
...
```

**复现要点**：把 4 个 router 挂上、CORS 按 DEBUG 切换、logging 配置好。至此你的后端与 `backend/main.py` 等价。

---

## 19. 前端对接点速览

后端项目的你只需要知道"我的接口被谁、以什么姿势调用"，30 秒版：

- **统一请求器**：`frontend/src/api/request.js` 创建了 axios 实例（baseURL 读 `VITE_API_BASE_URL`，默认 `http://127.0.0.1:8000`），请求拦截器自动加 `Authorization: Bearer <token>`，响应拦截器遇到 401 清除本地登录态。**所以前端永远不需要手动拼鉴权头**。
- **接口消费点**：每个业务页面的数据都走 Pinia store——`store/user.js` 调用户 5 接口，`store/modules/news.js` 调新闻 3 接口，`favorite.js`/`history.js` 调收藏与历史。
- **AI 问答**：`views/AIChat.vue` 用 fetch 调后端代理 `/api/ai/chat`（SSE 流式），前端零密钥；提供方（智谱/Ollama）与 Key 都在后端 `.env`。
- **Token 存哪**：登录成功后 token 存进 Pinia 并经 `pinia-plugin-persistedstate` 持久化到 localStorage（键 `user-store`），页面刷新不丢。
- **联调时的跨域**：开发模式后端 CORS 全放开直接调；若想摆脱 CORS，前端 vite 代理已备好（`vite.config.js` 的 `/api-proxy`）。
- **联调排错**：前端报"网络请求失败"先看后端终端日志和 `/docs` 能否手工调通——99% 是后端问题或参数名大小写不符（对照 `docs/api-spec.md` 的 alias）。

---

## 20. 调试与排错手册

| 症状 | 大概率原因 | 手段 |
|------|-----------|------|
| 启动即报 `Can't connect to MySQL` | MySQL 没启动 / `.env` 密码错 / 库没建 | 先 `mysql -uroot -p` 能进；重导 `database/database.sql` |
| 启动报 `ModuleNotFoundError` | 没进 conda 环境 / 目录不对 | `conda activate ./.conda-env`；必须在 `backend/` 下执行 `uvicorn main:app` |
| 接口返回 422 | 参数缺失/类型错/`page<1`/密码<6位 | `/docs` 里看该接口的 Schema；422 的 body 会指出哪个参数错 |
| 401 无效令牌 | 没带 Authorization / token 过期 / Bearer 格式错 | 先登录拿新 token；`/docs` Authorize 重新填 |
| 404 | id 不存在 / 删除了不属于自己的资源 | 对照 `docs/api-spec.md` |
| 500 数据库操作失败 | 看**后端终端日志**（`LOG_LEVEL=INFO` 以上必打） | 开 `SQL_ECHO=true` 看具体 SQL |
| 响应字段名和预期对不上 | alias 机制（`publishedTime` vs `publish_time`） | 以 `docs/api-spec.md` 为准 |
| 改了代码不生效 | uvicorn 忘了 `--reload` / 改错环境 | 确认激活的是 `.conda-env` |
| 请求卡住好几秒 | Redis 挂了但没超时（本项目已配 2s 超时，快速失败降级） | `redis-cli ping` 检查 |

调试心法：**从后端终端的日志往回追**，而不是盯着前端界面猜。`SQL_ECHO=true` + `LOG_LEVEL=DEBUG` 能让你看到每一层发生了什么。

---

## 21. 已知设计取舍与进阶方向

复现完成 ≠ 项目完美。以下是本项目**有意保留或尚未做**的，理解它们比背概念更有价值：

| 现状 | 为什么 | 进阶方向 |
|------|--------|----------|
| token 表方案（每请求查 2 次库） | 教学上最直白 | 迁移 JWT（`pyjwt`）：签发自包含令牌免查库；前置是前端所有请求已统一走 request.js |
| 事务"双轨"：crud 内自行 commit + `get_db` 收尾 commit | 简单场景两套都能跑 | 统一为 crud 自管写事务、`get_db` 只管连接生命周期 |
| 响应模型 | 已统一：全部路由挂 `response_model=APIResponse[...]`，`schemas/response.py` 的泛型包络 | —— |
| 详情/列表时间字段曾两套命名（publishTime 与 publish_time） | 已修复：统一为 `publishTime`（`schemas/base.py` 别名） | —— |
| 无数据库迁移（表靠 `database.sql`） | 表结构稳定、项目规模小 | 引入 Alembic：模型变更自动生成迁移脚本（前置：统一 metadata，已完成） |
| 无自动化测试 | —— | pytest + httpx 异步客户端，先覆盖注册/登录/列表/收藏主链路 |
| 事务"双轨"：crud 内自行 commit + `get_db` 收尾 commit | 简单场景两套都能跑 | 统一为 crud 自管写事务、`get_db` 只管连接生命周期 |

---

## 附录 A：复现检查清单

- [ ] conda 环境建立，9 个依赖能 import
- [ ] `uvicorn main:app` 启动，`/` 与 `/docs` 可访问
- [ ] `config/`：连接串从 `.env` 拼出；Redis 客户端带超时
- [ ] `models/`：5 个模型 + 统一 Base + TimestampMixin；`datetime.now` 不带括号
- [ ] `schemas/`：各模块 Request/Response，alias 与 `docs/api-spec.md` 一致
- [ ] `utils/`：bcrypt 哈希自测通过；`schemas/response.py` 的 `APIResponse` 泛型包络
- [ ] `crud/users.py`：注册后 user 表有 bcrypt 密码行
- [ ] `routers/users.py`：/docs 全链路（注册→登录→信息→改密）
- [ ] `utils/auth.py`：错误 token 401，正确 token 200
- [ ] `news_cache.py` + `routers/news.py`：分页 hasMore 正确，`page=0` 是 422
- [ ] 缓存：二次请求不产生 SQL 日志；Redis 停掉后功能仍可用（降级）
- [ ] 浏览量自增后，详情缓存被失效（再次请求看到新浏览量）
- [ ] 重复注册/重复收藏返回 400 且文案与约束对应
- [ ] 收藏/历史 join 列表含时间与 id；历史删除仅限本人记录
- [ ] `main.py`：CORS 随 DEBUG_MODE 切换；日志替代 print

## 附录 B：术语表

| 术语 | 一句话解释 |
|------|-----------|
| HTTP 方法 | GET 读 / POST 建 / PUT 改 / DELETE 删，接口的"动词" |
| 状态码 | 200 成功、400 参数/业务错、401 未认证、404 不存在、422 校验失败、500 服务器内部错 |
| 端点（endpoint） | 一个"方法 + 路径"组合，如 `GET /api/news/list` |
| 依赖注入 | 框架自动准备参数（db 会话、当前用户），函数只声明"我需要什么" |
| ORM | 用类/对象操作数据库，SQL 由框架生成并参数化 |
| 连接池 | 预先建好的数据库连接复用，避免每次请求都握手 |
| 缓存穿透 | 查询不存在的数据，缓存永远失效、全打到数据库 |
| 缓存雪崩 | 大量缓存键同时过期，请求洪峰压垮数据库 |
| 写后失效 | 数据库写成功后删除对应缓存，下次读重新加载 |
| 哈希/盐 | 不可逆"指纹"；盐让相同密码指纹也不同 |
| N+1 查询 | 先查列表再逐条查关联数据；用 join 一次取齐 |
| 水平越权 | 访问不属于自己的资源；删除/查询必须带归属条件 |
| 迁移 | 表结构变更的版本化管理工具（Alembic） |
