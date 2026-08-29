# AI头条新闻系统 (Toutiao News)

一个基于 FastAPI 和 SQLAlchemy 构建的现代化新闻系统，支持用户注册登录、新闻浏览、收藏和历史记录等功能。

## 1-1 项目概述

这是一个仿今日头条的新闻系统，采用前后端分离结构：后端使用异步 Python 框架 FastAPI 开发，使用 MySQL 作为数据库存储，通过 SQLAlchemy ORM 进行数据访问，Redis 作为缓存层；前端为 Vue 3 移动端 H5 应用。系统提供完整的用户管理、新闻浏览、收藏和历史记录功能。

## 1-2 技术栈

**后端**
- **后端框架**: FastAPI
- **数据库**: MySQL
- **ORM**: SQLAlchemy (异步)
- **数据库驱动**: aiomysql
- **密码加密**: passlib + bcrypt
- **缓存系统**: Redis
- **环境管理**: conda（项目内独立环境，见 `backend/environment.yml`）

**前端**
- **框架**: Vue 3（组合式 API）
- **构建工具**: Vite
- **状态管理**: Pinia
- **UI 组件库**: Vant 4
- **国际化**: vue-i18n

## 1-3 项目结构

```
FoundGoldenNews/                        # 仓库根目录
├── backend/                            # 后端（FastAPI）
│   ├── crud/                           # 数据访问层（CRUD操作）
│   │   ├── favorite.py                 # 收藏相关数据库操作
│   │   ├── history.py                  # 历史记录相关数据库操作
│   │   ├── news.py                     # 新闻相关数据库操作
│   │   ├── news_cache.py               # 新闻相关数据库操作（带缓存）
│   │   └── users.py                    # 用户相关数据库操作
│   ├── models/                         # 数据模型定义（SQLAlchemy）
│   ├── routers/                        # API路由定义
│   ├── schemas/                        # 数据验证模型（Pydantic）
│   ├── cache/                          # 缓存键与序列化封装
│   ├── utils/                          # 工具函数（认证/异常/响应）
│   ├── config/                         # 配置相关
│   │   ├── db_conf.py                  # 数据库配置（读环境变量）
│   │   └── cache_conf.py               # Redis缓存配置（读环境变量）
│   ├── main.py                         # 应用入口文件
│   ├── requirements.txt                # Python 依赖清单（锁定版本）
│   ├── environment.yml                 # conda 环境定义
│   ├── .env.example                    # 环境变量模板（复制为 .env 使用）
│   └── .env                            # 本机环境变量（不入库）
│
├── frontend/                           # 前端（Vue 3 + Vite）
│   └── src/
│       ├── views/                      # 页面组件
│       ├── components/                 # 公共组件
│       ├── store/                      # Pinia 状态管理
│       ├── router/                     # 路由
│       ├── i18n/                       # 国际化（zh-CN / en-US）
│       └── config/api.js               # API 地址配置
│
├── docs/
│   └── api-spec.md                     # API 接口规范文档（17 个接口）
│
├── database/
│   └── database.sql                    # 建库建表 SQL（含 8 张表）
│
├── .gitignore
└── README.md
```

## 1-4 快速开始

### 环境准备

1. MySQL 8.x 与 Redis 已在本地安装并启动
2. conda（Anaconda/Miniconda）已安装

### 后端启动

```bash
# 1. 创建项目内独立 conda 环境（不依赖本机 Anaconda base 的包）
cd backend
conda env create -f environment.yml -p .conda-env

# 2. 配置环境变量：复制模板并按需修改
cp .env.example .env

# 3. 初始化数据库（创建 news_app 库与 8 张表）
mysql -uroot -p < ../database/database.sql

# 4. 启动服务
conda activate ./.conda-env
uvicorn main:app --reload
```

启动后访问 http://127.0.0.1:8000/docs 查看接口文档。

> 说明：也可以用 `conda run -p .conda-env uvicorn main:app --reload` 免激活直接运行；`--reload` 仅用于开发。

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

启动后按提示打开本地地址（默认 http://localhost:5173）。

### 环境变量说明（backend/.env）

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` / `DB_NAME` | MySQL 连接信息 | root / 空 / localhost / 3306 / news_app |
| `SQL_ECHO` | 是否在控制台输出 SQL 日志 | false |
| `DEBUG_MODE` | true 时异常详情（含堆栈）返回给客户端，仅限本地开发 | false |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` / `REDIS_PASSWORD` | Redis 连接信息 | localhost / 6379 / 0 / 空 |
| `CORS_ORIGINS` | 生产环境前端来源白名单（逗号分隔） | 空 |

## 1-5 功能模块

### 1. 用户管理模块

- 用户注册
- 用户登录
- 用户信息获取
- 用户信息更新
- 用户密码修改

### 2. 新闻模块

- 新闻分类获取
- 新闻列表获取（支持分页和分类筛选）
- 新闻详情获取
- 浏览量统计

### 3. 收藏模块

- 添加收藏
- 取消收藏
- 收藏列表获取
- 清空所有收藏
- 检查收藏状态

### 4. 浏览历史模块

- 添加浏览记录
- 浏览历史列表获取
- 删除单条浏览记录
- 清空浏览历史

### 5. 缓存模块

- 新闻详情缓存
- 新闻列表缓存
- 分类数据缓存
- 用户历史记录缓存

## 1-6 数据库设计

建库建表 SQL 见 `database/database.sql`，库名 `news_app`（utf8mb4）。

### 主要数据表

1. **用户表 (user)** —— 用户基本信息，包含用户名、密码(加密)、昵称、头像等字段
2. **用户令牌表 (user_token)** —— 用户认证令牌管理，支持令牌过期机制
3. **新闻分类表 (news_category)** —— 新闻分类信息
4. **新闻表 (news)** —— 新闻内容存储，包含标题、内容、作者、浏览量等字段
5. **关联新闻表 (related_news)** —— 新闻间关联关系
6. **收藏表 (favorite)** —— 用户收藏记录，关联用户和新闻
7. **浏览历史表 (history)** —— 用户浏览历史记录，关联用户和新闻
8. **AI对话表 (ai_chat)** —— 用户 AI 问答记录

## 1-7 缓存设计

系统采用 Redis 作为缓存层，对高频访问的数据进行缓存，以提升系统性能和响应速度。

### 缓存数据类型

1. **新闻详情缓存**
    - 缓存键: `news:detail:{news_id}`
    - 过期时间: 5分钟（`backend/cache/news_cache.py`）

2. **新闻列表缓存**
    - 缓存键: `news:list:{category_id}:{page}:{size}`
    - 过期时间: 30分钟

3. **分类数据缓存**
    - 缓存键: `news:categories`
    - 过期时间: 2小时

### 缓存更新机制

- 数据更新时自动清除相关缓存
- 采用缓存失效而非主动更新策略
- Redis 不可用时自动降级为直连数据库

### 缓存配置

Redis 连接信息通过 `backend/.env` 环境变量配置（模板见 `.env.example`），由 `backend/config/cache_conf.py` 读取。

## 1-8 API 接口说明

完整的接口规范（含请求/响应示例）见 `docs/api-spec.md`，以下为接口清单。

### 用户相关接口

| 接口                 | 方法 | 说明         |
| -------------------- | ---- | ------------ |
| `/api/user/register` | POST | 用户注册     |
| `/api/user/login`    | POST | 用户登录     |
| `/api/user/info`     | GET  | 获取用户信息 |
| `/api/user/update`   | PUT  | 更新用户信息 |
| `/api/user/password` | PUT  | 修改用户密码 |

### 新闻相关接口

| 接口                   | 方法 | 说明             |
| ---------------------- | ---- | ---------------- |
| `/api/news/categories` | GET  | 获取新闻分类列表 |
| `/api/news/list`       | GET  | 获取新闻列表     |
| `/api/news/detail`     | GET  | 获取新闻详情     |

### 收藏相关接口

| 接口                   | 方法   | 说明             |
| ---------------------- | ------ | ---------------- |
| `/api/favorite/check`  | GET    | 检查新闻收藏状态 |
| `/api/favorite/add`    | POST   | 添加收藏         |
| `/api/favorite/remove` | DELETE | 取消收藏         |
| `/api/favorite/list`   | GET    | 获取收藏列表     |
| `/api/favorite/clear`  | DELETE | 清空所有收藏     |

### 浏览历史相关接口

| 接口                               | 方法   | 说明             |
| ---------------------------------- | ------ | ---------------- |
| `/api/history/add`                 | POST   | 添加浏览记录     |
| `/api/history/list`                | GET    | 获取浏览历史列表 |
| `/api/history/delete/{history_id}` | DELETE | 删除单条浏览记录 |
| `/api/history/clear`               | DELETE | 清空浏览历史     |

## 1-9 认证机制

系统使用基于令牌(Token)的认证机制：

1. 用户登录成功后返回访问令牌
2. 需要认证的接口在请求头中添加 `Authorization: Bearer <token值>`
3. 令牌有效期为7天

## 1-10 错误处理

系统提供统一的错误处理机制（`backend/utils/exception.py`）：

- 用户认证失败返回 401 状态码
- 资源不存在返回 404 状态码
- 数据库约束冲突返回 400 状态码（按具体约束返回对应提示）
- 服务器内部错误返回 500 状态码
- 堆栈等调试信息仅在 `DEBUG_MODE=true` 时返回

## 1-11 开发规范

- 使用异步数据库操作
- 所有密码均加密存储（bcrypt）
- 接口返回统一的 JSON 格式
- 数据库与 Redis 连接信息一律走 `.env` 环境变量，禁止硬编码入库
- 缓存操作封装成独立函数便于调用

## 1-12 性能优化

- 使用 Redis 缓存热点数据
- 异步数据库操作提升并发性能
- 合理的数据库索引设计
- 连接池管理减少连接开销
