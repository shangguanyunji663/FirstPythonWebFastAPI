# 后端学习文档：从零复现「AI 头条新闻系统」

> **这份文档是写给谁的**：只会 Python 基础语法（变量、函数、类、装饰器听过但未必熟练），没接触过 Web 开发、数据库、缓存的初学者。
>
> **这份文档能做什么**：带你按"如果是你自己从零写这个项目，应该按什么顺序想、按什么顺序写"的逻辑，把 `backend/` 目录下的后端完整复现一遍。每一章都是：**为什么需要它（概念）→ 本项目怎么做的（对照真实代码）→ 你动手写什么（复现要点）**。代码示例全部来自当前仓库，注释级别的讲解尽量做到"每一行都知道在干嘛"。
>
> **怎么用**：左手开这份文档，右手开编辑器里的 `backend/` 目录，边读边对照。**第 0 章是前置概念课**——如果 HTTP/JSON/命令行这几个词你还发怵，一定先读它；已经熟悉的老手可以直接从第 1 章开始。读完一章就自己在空目录里敲出对应的那一层，跑通再进下一章。前端不是重点，只在第 19 章讲"你的后端会被谁调用、怎么调"，接口的完整定义见 [api-spec.md](api-spec.md)，前端实现见 [frontend-learning.md](frontend-learning.md)。

---

## 目录

- [0. 开始之前：先把 5 个前置概念弄明白](#0-开始之前先把-5-个前置概念弄明白)
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
- [11. 密码安全：utils/security.py](#11-密码安全utilssecuritypy)
- [12. 用户路由：routers/users.py 与统一响应](#12-用户路由routersuserspy-与统一响应)
- [13. 认证体系：token 表方案](#13-认证体系token-表方案)
- [14. 新闻模块：关联表、分页与缓存版查询](#14-新闻模块关联表分页与缓存版查询)
- [15. 缓存体系：穿透、雪崩与一致性](#15-缓存体系穿透雪崩与一致性)
- [16. 全局异常处理：utils/exception.py](#16-全局异常处理utilsexceptionpy)
- [17. 收藏与历史模块：join 查询与唯一约束](#17-收藏与历史模块join-查询与唯一约束)
- [18. 组装：main.py（路由、CORS、日志、定时任务）](#18-组装mainpy路由cors日志定时任务)
- [19. 前端对接点速览](#19-前端对接点速览)
- [20. 调试与排错手册](#20-调试与排错手册)
- [21. 已知设计取舍与进阶方向](#21-已知设计取舍与进阶方向)
- [附录 A：复现检查清单](#附录-a复现检查清单)
- [附录 B：术语表](#附录-b术语表)
- [附录 C：完整请求/响应示例集（curl）](#附录-c完整请求响应示例集curl)

---

## 0. 开始之前：先把 5 个前置概念弄明白

这一章不讲项目，只讲"读后面章节必须会的 5 个概念"。每个概念配一个生活类比和一个自查问题，能答上来就可以跳到第 1 章。

### 0.1 HTTP：前后端之间怎么"说话"

**类比**：HTTP 请求就像寄快递。请求 = 包裹（写着收件地址和里面装的东西），响应 = 回执（对方收到后寄回来的东西）。

前端每次调后端接口，就是发一个**请求**，它由三部分组成：

```
POST /api/user/register HTTP/1.1     ← 请求行：方法 + 路径 + 协议版本
Content-Type: application/json       ← 请求头：元信息（我发的是 JSON）
                                     ← （空行，头和体的分隔线）
{"username": "tom", "password": "123456"}   ← 请求体：真正的数据
```

后端处理后回一个**响应**：

```
HTTP/1.1 200 OK                      ← 状态行：状态码 + 短语
Content-Type: application/json

{"code": 200, "message": "注册成功", "data": {...}}   ← 响应体
```

**方法（动词）**只有几个常用的：`GET` 读数据、`POST` 创建、`PUT` 更新、`DELETE` 删除。**路径**决定找谁：`/api/user/register` 一眼能看出是"user 服务的 register 功能"。

**请求头**里最重要的一个后面会反复出现：`Authorization: Bearer <token>`——把你的"通行证"带在身上，证明"这个请求是我发的"。

> **自查**：`GET /api/news/detail?id=1` 和 `POST /api/favorite/add`（体里带 `{"newsId": 1}`）分别是什么意思？答：前者"读取 id=1 的新闻详情"（参数在路径上），后者"创建一条收藏记录"（数据在体里）。

### 0.2 JSON：数据传输的通用格式

**类比**：JSON 就是前后端约定的"填表格式"——不管你内部用什么语言、什么数据结构，寄出去的包裹一律按这个格式装箱。

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "tags": ["科技", "AI"],
    "related": null
  }
}
```

规则只有几条：花括号是**对象**（Python 的 dict）、方括号是**数组**（list）、双引号字符串、数字/布尔/null（对应 Python 的 `None`）。**注意两个新手坑**：

1. JSON 的 key 必须双引号，Python dict 的 key 单双引号都行。
2. Python 的 `True/False/None` 序列化成 JSON 后是 `true/false/null`——你在代码里写 Python，在 curl/日志里看到的是 JSON。

Python 里 `json.dumps(dict)` 把字典转 JSON 字符串（打包），`json.loads(字符串)` 反过来（拆包）。本项目 Redis 里存的就是 JSON 字符串（第 15 章）。

### 0.3 命令行：本章的"操作界面"

后端开发离不开命令行（Windows 下推荐 Git Bash，本项目命令都在它下面验证过）。只用得上一小撮命令：

| 命令 | 作用 | 类比 |
|------|------|------|
| `cd backend` | 进入 backend 目录 | 走进某个房间 |
| `ls`（或 Windows `dir`） | 列出当前目录内容 | 看房间里有什么 |
| `cp A B` | 复制文件 | 复印一份 |
| `mkdir xx` | 新建目录 | 隔一个新房间 |
| `command --help` | 看命令的帮助 | 说明书 |

**怎么读报错**：命令行报错**最后一行最重要**。比如：

```
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    from routers import users
ModuleNotFoundError: No module named 'routers'    ← 看这行！
```

`ModuleNotFoundError: No module named 'routers'` = "没找到 routers 模块"——十有八九是你不在 `backend/` 目录下运行。记住这个读法：**先看最后一行，再看它上面最近的两三行**。

### 0.4 状态码：一眼判断请求的结局

状态码三位数，只需要记住**三个家族**：

| 家族 | 含义 | 本项目常用值 |
|------|------|--------------|
| 2xx | 成功 | 200（一切正常） |
| 4xx | **客户端**的错（你请求得不对） | 400 参数不合法、401 没登录/令牌无效、404 资源不存在、429 请求太频繁 |
| 5xx | **服务器**的错（后端代码炸了） | 500 内部错误 |

调试时的第一反应应该是：**4xx 查自己的请求参数，5xx 查后端终端日志**。本项目所有错误响应都长一个样（统一三键包络，第 16 章细讲），`message` 字段直接告诉你人话原因。

### 0.5 同步与异步：为什么要到处写 async/await

**类比**：奶茶店一个店员。**同步**模式下，店员接一个单就站那儿等奶茶机出杯，后面排队的人全部干等；**异步**模式下，店员按下奶茶机按钮后马上去接待下一位，机器好了再回头端给客人——**等待的时间拿来干别的**。

Web 服务天生充满"等待"：等数据库查完、等 Redis 读完、等第三方接口响应。这些等待如果傻站着（同步），一个慢查询就能堵死整个服务。Python 的 `async def` + `await` 就是"异步写法"：

```python
async def get_news(db):            # async def：声明这是个"会等待"的函数
    result = await db.execute(q)   # await：这里要等 IO，等待期间去服务别的请求
    return result
```

两条铁律：① `await` 只能写在 `async def` 函数里；② 一个环节不异步（比如数据库驱动是同步的），整条链就退化成阻塞——所以本项目 FastAPI（异步框架）+ aiomysql（异步驱动）+ `AsyncSession`（异步会话）三者必须配套，缺一个都不行（第 2 章细讲）。

> **自查**：`await db.execute(q)` 执行时，其他用户的请求在干嘛？答：在被处理——事件循环把这个等待时间让给了别人。

---

## 1. 项目是什么：一个新闻系统的后端

这是仿"今日头条"的新闻系统，**本仓库的主角是它的后端 API 服务**。先从用户视角走一遍，看看每个动作背后是哪个接口在工作：

| 用户动作 | 背后的接口 | 干了什么 |
|----------|-----------|----------|
| 打开 App 首页 | `GET /api/news/categories` + `GET /api/news/list` | 拉分类栏 + 拉第一页新闻（分页/缓存） |
| 点开一条新闻 | `GET /api/news/detail?id=1` | 拉详情 + 相关新闻；浏览量在响应后异步 +1 |
| 注册/登录 | `POST /api/user/register` / `POST /api/user/login` | bcrypt 存密码 / 签发 7 天令牌 |
| 点收藏 ⭐ | `POST /api/favorite/add` | 唯一约束防重复收藏 |
| 回头看"浏览历史" | `GET /api/history/list` | join 查询新闻+浏览时间 |
| 问 AI"总结今天科技新闻" | `POST /api/ai/chat` | 后端代理转发智谱/本地 Ollama，SSE 流式回 |
| 新闻从哪来？ | 内置 RSS 爬虫 | 启动即抓一次，之后每 6 小时（可配）自动抓公开源入库 |

全部接口共 **20 个，分 6 组**：

| 模块 | 功能 | 接口数 |
|------|------|--------|
| 用户 | 注册、登录、查信息、改资料、改密码 | 5 |
| 新闻 | 分类列表、新闻列表（分页）、新闻详情（浏览量后台+1） | 3 |
| 收藏 | 检查/添加/取消/列表/清空 | 5 |
| 历史 | 添加/列表/删除单条/清空 | 4 |
| AI 问答 | SSE 流式对话（后端代理智谱/本地 Ollama）、聊天历史 | 2 |
| 数据采集 | RSS 爬虫手动触发（定时抓取随应用启动自动注册） | 1 |

本教程的复现路线覆盖前 4 组共 17 个核心接口；AI 问答与爬虫不单独成章，读完本教程后可直接读 `routers/ai.py`（约 100 行）和 `crawler/`（约 200 行），用到的全是前面章节的概念。

**看一个真实的接口交互**——注册。前端发来请求体：

```json
{"username": "tom", "password": "pass123456"}
```

后端校验通过后（用户名 4~20 位字母/数字/下划线、密码 6~32 位），密码**加密**存库、签发令牌，返回：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "8f14e45f-ea2b-4c3a-9b1d-...",   ← 通行证，前端存起来
    "userInfo": {                              ← 注意：驼峰命名，后端 Pydantic alias 转的（第 9 章）
      "id": 1,
      "username": "tom",
      "bio": "这个人很懒，什么都没留下",
      "avatar": "https://..."
    }
  }
}
```

前端把 `token` 存进 localStorage，之后每个需要登录的请求都带上 `Authorization: Bearer <token>`（第 13 章）。这就是整个系统最核心的一条主线。

**一句话概括架构**：浏览器里的 Vue 前端发 HTTP 请求 → FastAPI 接住请求 → 经过校验和认证 → 通过 SQLAlchemy 查 MySQL（能命中 Redis 缓存就不查库）→ 把结果包成统一格式的 JSON 返回。

---

## 2. 技术栈地图：每个东西是干嘛的

零基础最大的困惑是"一坨名词各管什么"。逐个说清，重点看第三列——**不用它你就要手工做什么**，这一列才是"它为什么存在"：

| 名词 | 它是什么 | 不用它你就要手工做什么 |
|------|----------|------------------------|
| **FastAPI** | Python 的 Web 框架，负责"接收 HTTP 请求、返回响应" | 自己解析 HTTP 报文、自己写路由分发 |
| **uvicorn** | Web 服务器，真正监听 8000 端口的程序，FastAPI 挂在它上面运行 | 自己实现 TCP/HTTP 协议 |
| **Pydantic (v2)** | 数据校验库：声明"这个接口需要什么字段、什么类型"，不符合自动报错 | 请求进来后手动 `if not isinstance(...)` 一层层检查 |
| **MySQL** | 关系型数据库，数据真正存放的地方 | 用文件存数据然后自己维护一致性 |
| **SQLAlchemy (2.0)** | ORM：用 Python 类和对象操作数据库，不用手写 SQL 字符串 | 手写 SQL 拼接并小心 SQL 注入 |
| **aiomysql** | MySQL 的**异步**驱动，SQLAlchemy 通过它发请求 | —— |
| **redis** | 内存键值数据库，本项目用作**缓存**（高频数据先问 Redis，没有再查 MySQL） | 每个请求都打数据库，量大就拖垮 |
| **bcrypt** | 密码哈希（直接用官方库，不经过已停更的 passlib）：存"不可逆的指纹"而不是明文密码 | 数据库泄露=全部明文密码泄露 |
| **httpx** | 异步 HTTP 客户端：AI 代理转发模型服务、爬虫抓取 RSS 源都用它 | 自己造轮子发 HTTP 请求 |
| **APScheduler** | 定时任务调度：应用启动后按固定间隔触发 RSS 抓取 | 自己写 `while True: sleep()` 循环 |
| **feedparser + selectolax** | RSS/XML 解析与 HTML 转纯文本：把抓来的源变成新闻行 | 手写 XML/HTML 字符串解析 |
| **python-dotenv** | 从 `.env` 文件读配置（数据库密码等），避免写死在代码里 | 密码提交进代码仓库 |

**看一次请求怎么穿过这些技术栈**（以 `GET /api/news/list?categoryId=1&page=1` 为例，从上往下）：

```
uvicorn（监听 8000 端口，收到 HTTP 报文）
  → FastAPI（按路径找到处理函数；CORS 中间件先过一遍）
    → Pydantic（校验 categoryId 必填、page ≥ 1）
      → utils/auth（此接口无需登录，跳过）
      → crud/news.py：先问 Redis（缓存命中就到此为止）
        → 未命中 → SQLAlchemy（把 Python 查询翻译成 SQL）
          → aiomysql（异步把 SQL 发给 MySQL）→ MySQL 返回行
        → 结果写回 Redis
      → schemas（把 ORM 对象转成响应模型，alias 转驼峰）
    → FastAPI 打包成 JSONResponse
  → uvicorn 发回浏览器
```

**两个零基础必须先建立的观念**：

1. **同步 vs 异步**：第 0.5 节的奶茶店。数据库查询、Redis 读写都是 IO，所以本项目全线 `async def` + `await`。FastAPI 的异步能力 + aiomysql 的异步驱动 + `AsyncSession` 三者配套，缺一个就退化成同步阻塞。
2. **前后端分离**：后端只负责"响应 JSON 数据"，不生成 HTML 页面；页面渲染由独立的前端（Vue）负责。两者之间只靠 HTTP + JSON 交流，所以开发时各自独立启动、靠接口文档对齐。

---

## 3. 环境搭建与第一次启动

> 目标：把别人的项目跑起来，你才有"对照物"。**每一步都给了"怎么确认成功"**，卡住了对照第 20 章排错。

```bash
# 1. 创建项目内独立的 conda 环境（不污染本机 Anaconda base）
cd backend
conda env create -f environment.yml -p .conda-env

# 2. 配置环境变量：复制模板
cp .env.example .env        # Windows Git Bash 用 cp；PowerShell 用 copy

# 3. 初始化数据库（建 news_app 库 + 7 张表 + 示例数据）
mysql -uroot -p --default-character-set=utf8mb4 < ../database/database.sql

# 4. 启动
conda activate ./.conda-env
uvicorn main:app --reload
```

**逐条拆解每条命令在干嘛**：

- `conda env create -f environment.yml -p .conda-env`：conda 是 Python 的"环境管家"。`-f` 指定环境清单（里面写着要 Python 3.12 + requirements.txt 里的所有依赖）；`-p .conda-env` 把环境**装进项目目录里**而不是全局——好处是整个环境跟着项目走，不想要了删文件夹即可，也不会和本机其他 Python 项目互相污染。
- `cp .env.example .env`：`.env` 是配置文件（数据库密码等）。为什么不直接提交 `.env`？因为里面有密码——所以仓库只放**模板** `.env.example`（占位值），真实配置每人本地自己拷贝一份并填真密码，`.gitignore` 已把 `.env` 排除在 git 之外。
- `mysql -uroot -p --default-character-set=utf8mb4 < ../database/database.sql`：`-uroot` 用 root 用户，`-p` 交互式输密码（输入时不回显，正常）；`--default-character-set=utf8mb4` 指定按 utf8mb4 编码导入（MySQL 的 utf8 是残血版，存不了 emoji 和部分生僻字，utf8mb4 才是完整 UTF-8）；`< 文件` 把 SQL 文件"喂"给 mysql 客户端执行——文件里是一串 CREATE TABLE 和 INSERT 语句。
- `conda activate ./.conda-env`：激活刚才创建的项目内环境（之后 `python`、`uvicorn` 都用这个环境里的）。
- `uvicorn main:app --reload`：启动服务器。`main:app` 的语法是 **`文件名:变量名`**——"main.py 里的 app 变量"；`--reload` 让代码改动后自动重启（**只用于开发**，生产不带）。

**每一步怎么确认成功**：

| 步骤 | 成功的样子 | 失败时先看 |
|------|-----------|-----------|
| conda 创建 | 结尾输出 `# To activate this environment...`；`conda env list` 能看到 `.conda-env` | 最后一行报错；conda 命令不存在 → conda 没装/不在 PATH |
| 拷贝 .env | `backend/.env` 存在 | —— |
| 导入 SQL | mysql 客户端无报错退出；`mysql -uroot -p -e "USE news_app; SHOW TABLES;"` 能看到 7 张表 | `Access denied` → 密码错；`Unknown database` → 先看 SQL 文件开头是否建库 |
| 启动 | 终端打出 `INFO: Uvicorn running on http://127.0.0.1:8000`，浏览器打开 `/docs` 能看到接口列表 | `[Errno 10048]` → 8000 端口被占（可能已开了一个 uvicorn） |

打开 `http://127.0.0.1:8000/docs`——这是 FastAPI **自动生成**的交互式接口文档，所有接口可以直接在网页上填参数调试。**它是你复现过程中最重要的自测工具**。

> 应用启动时会自动注册 RSS 定时抓取：启动即抓一次，之后默认每 6 小时一轮（间隔由 `.env` 的 `CRAWL_INTERVAL_HOURS` 调整）。开发环境反复热重载觉得吵的话，在 `.env` 里设 `CRAWLER_ENABLED=false` 再启动。

`.env` 里每个变量改了会发生什么，见第 7 章。

---

## 4. 复现路线总览

不要按文件名字母序写，要按**依赖关系**写：被依赖的先写，每写完一层都能独立验证。这就像盖楼——地基（配置/模型）没打好，上面的路由层写完也没法验证。

| 步骤 | 写什么 | 验证方式 | 产出 |
|------|--------|----------|------|
| 1 | `main.py` 最小骨架 | 浏览器访问 `/` 返回 JSON | 一个能跑的服务 |
| 2 | `config/db_conf.py` | Python 里能建 engine 不报错 | 能连数据库的引擎 |
| 3 | `models/` 全部模型 | import 无报错 | 7 张表的 Python 映射 |
| 4 | `schemas/` 全部校验模型 | import 无报错 | 接口出入参的形状定义 |
| 5 | `utils/`（security/response） | 单独调用函数测哈希 | 密码哈希 + 统一响应 |
| 6 | `crud/users.py` | 用临时脚本调函数，库里能查到新用户 | 第一个能写库的函数 |
| 7 | `routers/users.py` + 挂路由 | `/docs` 里注册登录走通 | 第一批真接口 |
| 8 | `utils/auth.py` | 带/不带 token 调 `/api/user/info` | 登录保护 |
| 9 | `models/news.py`、`crud/news.py`、`routers/news.py` | 新闻三接口走通 | 新闻域 |
| 10 | `cache/news_cache.py` + Redis 配置 | 断开 Redis 再请求，应降级不报错 | 缓存层 |
| 11 | `utils/exception*.py` | 故意插重复用户名，看 400 文案 | 统一错误响应 |
| 12 | `crud/favorite.py`、`history.py` 及路由 | 收藏/历史全流程走通 | 收藏/历史域 |
| 13 | `main.py` 收尾（CORS、日志） | 前端能跨域调用 | 完整后端 |

**为什么是这个顺序**：2 依赖 1（骨架里挂配置）；3 依赖 2（模型要被会话操作）；4 依赖 3（schema 描述模型的形状）；6 依赖 3/4/5；7 依赖 6……每一格都能**独立跑通验证**，这是"小步快跑"——写 500 行才发现跑不起来是初学者最大的时间黑洞。

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

**逐行拆**：

1. `from fastapi import FastAPI` + `app = FastAPI()`：创建应用对象——它是整个服务的"总调度台"，路由、中间件、异常处理器都挂在它身上。uvicorn 启动命令里的 `main:app` 找的就是这个变量。
2. `@app.get("/")`：**装饰器**。装饰器本质是"语法糖"——这一行等价于：

```python
def root():
    return {"message": "Hello World"}
root = app.get("/")(root)   # 先调用 app.get("/") 拿到"注册函数"，再把 root 传进去注册
```

   读作："把 root 函数登记到路由表：以后收到 `GET /` 就执行它"。`get` 换成 `post`/`put`/`delete` 就是登记到其他 HTTP 方法上。
3. `async def`：第 0.5 节的异步函数。函数体里没有 IO 时写不写 `await` 都行，但**习惯上全部用 async def 统一风格**。
4. `return {"message": "Hello World"}`：返回 dict。FastAPI 自动 `json.dumps` 并带上 `Content-Type: application/json` 响应头——这就是"框架替你干了脏活"。

**跑起来看结果**：

```bash
uvicorn main:app --reload
```

浏览器访问 `http://127.0.0.1:8000/` 会看到 `{"message":"Hello World"}`；访问 `/docs` 是自动生成的接口文档页。终端里每次请求会打出访问日志：

```
INFO:     127.0.0.1:52341 - "GET / HTTP/1.1" 200 OK
```

**复现要点**：新建空目录，写出上面几行，`uvicorn main:app` 跑起来，浏览器访问 `http://127.0.0.1:8000/` 和 `/docs`。对照项目 `backend/main.py` 里的 `root()`——一模一样。

---

## 6. 分层架构：目录设计与一次请求的旅程

**为什么要分层**：如果所有代码堆在 main.py，500 行后就没法维护。**类比一家餐厅**：

| 餐厅角色 | 本项目对应 | 职责 | 明确不管什么 |
|----------|-----------|------|--------------|
| 迎宾/大堂经理 | `main.py` | 开门营业、安排座位（挂路由/中间件） | 不做菜 |
| 服务员 | `routers/` | 接单（收请求）、报菜名（参数校验）、上菜（返回响应） | 不进仓库搬货 |
| 菜单/点单纸 | `schemas/` | 规定"点什么菜、什么格式"（出入参形状） | 不关心菜怎么做 |
| 后厨 | `crud/` | 真正做菜（读写数据） | 不直接面对客人 |
| 仓库管理员 | `models/` | 知道仓库里每样东西放哪（表结构映射） | 不做菜 |
| 库房 | MySQL | 真正存货的地方 | —— |
| 备菜冰箱 | Redis | 常用的先从冰箱拿，没有再去库房 | —— |
| 保安 | `utils/` | 查证件（认证）、拦捣乱的（限流）、处理纠纷（异常） | —— |

分层的核心好处：**每一层可以被单独替换和测试**。哪天把 MySQL 换 PostgreSQL，只动 models/config；哪天换 Web 框架，只动 routers——后厨（crud）完全不知道发生 anything。

**目录结构**（项目现状）：

```
backend/
├── main.py          # 入口：创建 app、装中间件、注册路由
├── routers/         # 路由层：定义 URL、校验入参、调 crud、组织响应（只管"接客"）
├── schemas/         # 校验层：每个接口的入参/出参数据形状（只管"格式"）
├── crud/            # 数据访问层：所有数据库读写（只管"数据怎么来"）
├── models/          # 模型层：数据库表在 Python 里的映射（只管"表长什么样"）
├── cache/           # 缓存键与读写封装（只管"Redis 怎么用"）
├── crawler/         # RSS 爬虫：抓取公开源 → 解析 → 去重入库 → 失效分类缓存
├── config/          # 配置：数据库/Redis 连接（只管"连到哪"）
└── utils/           # 横切工具：认证、密码哈希、限流、异常处理
```

**依赖方向必须是单向的**：`routers → crud → models`（服务员可以叫后厨做菜，后厨不能跑去前台拉客）。反向依赖（crud 里 import routers）是架构坏味道——本项目曾有一处反例（crud 层抛 Web 层的 `HTTPException`），已重构为 crud 返回 `None`、路由层翻译成 404。写新代码时保持 crud 只返回数据或领域结果，不做 HTTP 翻译。

**一次"GET /api/news/list?categoryId=1&page=1"的完整旅程**（记住这条线，后面每章都是线上的一站）：

```
浏览器请求
  → main.py 路由表找到 routers/news.py 的 get_news_list        【服务员接单】
  → FastAPI 校验查询参数（categoryId 必填、page≥1……）          【对照点单纸】
  → 依赖注入系统先准备 db 会话（config/db_conf.py 的 get_db）   【给后厨开仓库门】
  → crud/news.py.get_news_list：先问 Redis（cache/news_cache.py）【先看冰箱】
       命中 → 直接返回
       未命中 → 查 MySQL（models/news.py 定义的表）→ 结果写回 Redis 【冰箱没有→去库房→补货】
  → crud.get_news_count_cached 拿总数                          【顺带问总数】
  → 路由层拼 {list, total, hasMore} 返回                        【摆盘上菜】
  → get_db 收尾：commit / rollback / close                     【打烊清点】
```

**复现要点**：先只建目录和空 `__init__.py`（`touch routers/__init__.py crud/__init__.py ...`）。Python 把含 `__init__.py` 的目录当"包"，这样 `from routers import news` 才是明确的包导入。

---

## 7. 配置层：config/

**概念**：数据库地址、密码这类"因环境而异、且敏感"的信息不该写在代码里——换台机器要改代码、提交仓库会泄露。方案：写在 `.env` 文件里（不进 git），代码启动时读环境变量。这套思路来自十二要素应用（12-Factor App）的"配置与代码分离"原则。

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

# ---- AI 问答（提供方与密钥统一在后端，前端零密钥） ----
AI_PROVIDER=zhipu              # zhipu（智谱云端）| ollama（本地）
AI_API_KEY=                    # 智谱 API Key；provider=ollama 时无需
AI_BASE_URL=                   # 智谱端点覆盖（自建中转/代理时才需要），留空用官方默认
AI_MODEL=glm-4.7-flash
OLLAMA_BASE_URL=http://localhost:11434

# ---- RSS 爬虫 ----
CRAWLER_ENABLED=true           # false 关闭定时抓取（开发热重载时用）
CRAWL_INTERVAL_HOURS=6         # 定时抓取间隔（小时）
```

`python-dotenv` 的作用就一步：`load_dotenv()` 把 `.env` 文件里的 `key=value` 全部灌进进程的环境变量（`os.environ`），之后代码用 `os.getenv("KEY", "默认值")` 读。

`config/db_conf.py` 读取并创建**异步引擎**，逐行看：

```python
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

load_dotenv()  # 把 .env 内容加载进环境变量

DB_USER = os.getenv("DB_USER", "root")        # 第二个参数是缺省值：没配就用 root
...
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
```

连接串的格式值得背下来：**`方言+驱动://用户:密码@主机:端口/库名?参数`**。`mysql+aiomysql` = "MySQL 方言，用 aiomysql 驱动"——SQLAlchemy 本身不连库，全靠驱动。

```python
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # true 时打印每条 SQL
    pool_size=10,        # 常驻连接数
    max_overflow=20,     # 高峰可临时多开的连接数
    pool_pre_ping=True,  # 取连接前探活：闲置连接被 MySQL 服务端掐掉后自动重建
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
```

- **连接池**：类比公司前台的总机——养 10 条常驻外线（`pool_size=10`），话务高峰最多再临时拉 20 条（`max_overflow=20`），用完归还。没有池的话每个请求都要重新"拨号"（TCP 三次握手 + MySQL 认证），慢且费。
- **`pool_pre_ping=True`**：MySQL 服务端有个 `wait_timeout`（默认 8 小时），闲置太久的连接会被**服务端单方面掐断**，而池子还以为它是好的——下次取出来用就直接报「MySQL server has gone away」。`pre_ping` = 每次取线前先"喂一声"确认活着，死了就换一条。部署后隔夜必现的那种 500，多半是这个。
- **`expire_on_commit=False`**：commit 之后 ORM 对象属性不立刻"过期"。不关的话，commit 后再访问对象属性会触发一次新的隐式查询，异步下很容易踩坑。

**`get_db`——FastAPI 的"依赖注入"**，逐行看：

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

`yield` 把函数劈成两半，执行时序是关键：

```
请求进来 ──→ 执行 yield 之前的代码（建会话）
         ──→ 在 yield 处"暂停"，把 session 递给路由函数
路由函数执行（查库/写库）……
         ──→ 路由函数 return 后，回到 yield 之后：
             正常 → commit；抛异常 → rollback 并把异常继续往外抛
         ──→ finally：close 归还连接（一定执行）
```

路由里写 `db: AsyncSession = Depends(get_db)`，FastAPI 就会在**每个请求**进来时执行 `get_db` 到 `yield` 为止、把 session 递给你，请求结束后自动执行 yield 之后的收尾。"开头准备、结尾清理"的逻辑全部由框架托管，你不用在每个接口里手动开关连接。

- `config/cache_conf.py` 同理：读 Redis 配置建 `redis_client`，另外加了 `socket_timeout=2`（Redis 挂了 2 秒就失败，别让请求挂着——**快速失败**好过无限等待）。

**复现要点**：写出 `.env.example` 模板 → `db_conf.py` → 单独跑 `python -c "from config.db_conf import async_engine; print(async_engine.url)"` 验证连接串拼接正确（此时尚未真正连库，engine 是惰性的）。

---

## 8. 模型层：models/

**概念**：ORM = "表 ↔ Python 类"的映射。**类比 Excel**：一个类 = 一张工作表，一个对象 = 一行记录，类的属性 = 列。好处：不用手写 SQL、自带防注入（参数自动绑定）、类型有提示。

**语法（SQLAlchemy 2.0 推荐写法）**，以 `models/users.py` 的 User 为例，逐行看：

```python
class User(Base):
    __tablename__ = 'user'                      # 对应数据库里的表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #    ↑类型注解      ↑列定义：主键，自增
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    #   唯一约束（重复用户名直接被数据库拒绝），不许为 NULL
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    #   存的是 bcrypt 哈希串，约 60 字符，255 够宽
    gender: Mapped[str | None] = mapped_column(Enum('male', 'female', 'unknown'), default='unknown')
    #   `str | None` 是 Python 3.10+ 语法：可能是 str 也可能是 None
    #   Enum：数据库层面只允许这三个值，脏数据进不来
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)   # 注意：没有括号！
```

逐个拆解名词：

- `Mapped[int]`：类型注解，说明这一列在 Python 里是什么类型。它只是"标注"，真正的列定义在 `mapped_column(...)` 里。
- `mapped_column(...)` 的常用参数：`primary_key` 主键；`unique=True` 唯一（重复插入报错）；`nullable=False` 不许空；`comment` 写进建表语句的注释；`default` 插入时没给值就用的默认值（由 SQLAlchemy 在 INSERT 时填，属于 ORM 层行为）。
- `Enum('male','female','unknown')`：数据库层面就拦住脏数据，比"代码里 if 校验"多一道保险。

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

每个模型文件 `from models.base import Base`。**为什么强调"一个"**：`DeclarativeBase` 子类自带一张"注册表"（metadata），记录它知道的所有表。跨文件的外键（如 favorite 表指向 user、news 表）必须落在同一张 metadata 上才能成立。本项目早期每个文件各建一个 Base，是重构掉的真实坏味道。

`TimestampMixin` 则演示了**混入（Mixin）**：把公共列抽出来，`class News(Base, TimestampMixin)` 一继承就带上两个时间列——Python 的多继承在这里当"功能包"用。

**7 个模型 ↔ 7 张表对照**（建表 SQL 在 `database/database.sql`，模型只做映射不做建表）：

| 模型文件 | 类 | 表 |
|----------|-----|-----|
| `users.py` | `User` / `UserToken` | `user` / `user_token` |
| `news.py` | `Category` / `News` | `news_category` / `news` |
| `favorite.py` | `Favorite` | `favorite` |
| `history.py` | `History` | `history` |
| `ai.py` | `AIChat` | `ai_chat` |

**跨表引用**：`models/favorite.py` 里 `ForeignKey(User.id)`、`ForeignKey(News.id)` 直接引用其他文件的模型——这就是统一 metadata 之后才可能的事。`unique=True`、`UniqueConstraint('user_id','news_id', name='user_news_unique')`（多列联合唯一）在数据库层面防止"重复收藏"。

**⚠️ 本项目真实踩过的坑（务必记住）**：

```python
created_at = mapped_column(DateTime, default=datetime.now())   # ❌ 带括号
created_at = mapped_column(DateTime, default=datetime.now)     # ✅ 不带括号
```

带括号 = **在定义类的那个时刻**求值一次，之后所有插入都用这同一个固定时间；不带括号 = 传入函数本身，每次插入时才调用。这个 bug 曾导致本项目所有用户的创建时间是同一个值——现象非常隐蔽：单条数据看不出问题，`SELECT * FROM user` 一看全员同一秒注册。

**复现要点**：写 `models/base.py` → `users.py`（User + UserToken）→ `news.py`（Category + News，继承 TimestampMixin）→ `favorite.py`、`history.py`、`ai.py`。验证：`python -c "from models import users, news, favorite, history, ai; print('ok')"`。本项目表结构由 `database/database.sql` 管理，模型只做映射不做建表，所以不需要跑 `create_all`。

---

## 9. 校验层：schemas/

**先看没有校验层的世界**：注册接口你得手写——

```python
username = data.get("username")
if not isinstance(username, str) or not (4 <= len(username) <= 20) or not username.isalnum():
    return {"code": 400, "message": "用户名不合法"}
password = data.get("password")
if not isinstance(password, str) or len(password) < 6:
    return {"code": 400, "message": "密码不合法"}
...
```

每个接口来一遍，漏一个字段就是漏洞。**Pydantic 把这套检查变成"声明"**——你只描述"合法数据长什么样"，校验、转换、报错全自动化。

以 `schemas/users.py` 为例，看五件事：

```python
class UserRequest(BaseModel):          # 注册入参：强校验（与 user 表列定义对齐）
    username: str = Field(..., min_length=4, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    #                        ↑必填   ↑长度 4~20        ↑正则：只允许字母/数字/下划线
    password: str = Field(..., min_length=6, max_length=32)

class UserLoginRequest(BaseModel):     # 登录入参：仅要求非空，宽松规则避免历史账号被新规则锁在门外
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=64)

class UserAuthResponse(BaseModel):     # 登录成功的响应体
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., min_length=6, alias="newPassword")   # 内置校验：少于6位直接400
```

拆解：

- **`Field(...)`** 的常用参数：`...` 表示必填（三个点的省略号是 Pydantic 的约定）；`min_length/max_length` 长度；`pattern` 正则；`alias` 对外名称；`description` 会出现在 `/docs` 里。
- **为什么注册强校验、登录宽松**：强规则是后来加的（和 user 表列定义对齐）。如果登录也强校验，那些注册于规则上线前的"不合规老用户名"会被锁在门外。**同一资源的新建和更新可以有不同严格度**——这是真实的业务考量，不是随手写的。
- **`alias` 双向生效**：`populate_by_name=True` 让入参两个名字都认（`userInfo`/`user_info`）；序列化时 FastAPI 默认按 alias 输出，所以前端拿到的键是驼峰 `userInfo`、`hasMore`。
- **`from_attributes=True`**：允许"从 ORM 对象直接构造"：`UserInfoResponse.model_validate(user_orm对象)`，字段名对得上就自动搬。

**校验失败长什么样**：注册时密码只传 `"123"`，不用写任何处理代码，自动返回 400（本项目全局处理器把 FastAPI 默认的 422 统一转成 400，第 16 章）：

```json
{
  "code": 400,
  "message": "长度不足",
  "data": [{ "field": "password", "message": "长度不足" }]
}
```

**⚠️ 本项目踩过的命名坑**：`schemas/base.py` 里 `publish_time` 的别名是 `publishedTime`（多了个 d）。别名一旦定下，前端就按它取值，后改别名=前端联调全挂。新字段起别名时想清楚。

**为什么 models 和 schemas 要分开**：`User` ORM 对象里有密码哈希、created_at 等不该出现在接口响应里的字段；而接口入参（注册）只需要 username/password 两个字段。两边形状不同、变化原因不同——强行共用一个类，早晚泄露字段。

**复现要点**：每个模块按"入参 Request + 出参 Response"各写一个。写完可以用 `UserRequest(username=1, password="x")` 试一下——`username` 传 int 会被 Pydantic 强转/报错，这就是"白拿的校验"。

---

## 10. 数据访问层：crud/（从 users 开始）

**概念**：crud 层的函数 = "对某张表的一种操作"，只收 `db` 会话和业务参数，返回 ORM 对象或标量；**不懂 HTTP**（不碰 request/response）。类比后厨：接单（参数）→ 做菜（读写数据）→ 出菜（返回结果），不直接面对客人。

**先建 SQL 直觉**——你写的每个 SQLAlchemy 调用都对应一条 SQL：

| 你写的 | 等价 SQL |
|--------|----------|
| `select(User).where(User.username == "tom")` | `SELECT * FROM user WHERE username = 'tom'` |
| `db.add(user)` + `commit` | `INSERT INTO user (...) VALUES (...)` |
| `update(User).where(...).values(bio="hi")` | `UPDATE user SET bio='hi' WHERE ...` |
| `delete(User).where(...)` | `DELETE FROM user WHERE ...` |

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

**收尾方法速查表**（`db.execute(query)` 之后怎么把数据拿出来）：

| 方法 | 返回 | 适用 |
|------|------|------|
| `scalar_one_or_none()` | 单个对象或 None | 按唯一键查一条（查不到不算错） |
| `scalar_one()` | 单个对象（没有/多了都抛错） | `func.count()` 等必然一行的聚合 |
| `scalars().all()` | 对象列表 | 多行结果 |
| `result.rowcount` | int | UPDATE/DELETE 影响了几行 |

要点：

- `select(User).where(...)` 是 SQLAlchemy 的查询构造器，**不是字符串拼 SQL**。参数由框架自动绑定为占位符，SQL 注入无入口。
- `.model_dump(exclude_unset=True)`：Pydantic v2 把"用户实际传了的字段"挑出来——实现"传什么改什么"的 PATCH 语义（`exclude_none=True` 再把 None 剔掉，代价是无法把字段清回 null，见第 21 章）。
- **commit 的位置**：本项目 crud 函数各自 commit（写完立刻提交），`get_db` 结尾还有一次统一 commit，形成"双轨"。能用，但口径要心里有数——`create_token` 的两个分支就都显式 commit 了，因为它可能在请求上下文之外被复用（见第 21 章）。

**复现要点**：只写 `crud/users.py` 五个函数（查用户、建用户、生成 token、验密码、改密码）。验证：临时脚本 `python -m asyncio` 里 `await create_user(...)`，再用 SQL 客户端看 `user` 表多了一行、密码是 bcrypt 串而不是明文。

---

## 11. 密码安全：utils/security.py

**概念**：密码绝不能明文入库。注意是**哈希**不是**加密**——加密是可逆的（有钥匙就能还原），哈希是**单向**的（只能从密码算出指纹，永远无法从指纹还原密码）。**类比**：把苹果打成苹果汁容易，把果汁还原成苹果不可能。登录时把用户输入再哈希一次，比对两个指纹是否一致。

```python
import bcrypt

# 密码加密：bcrypt 自带随机盐，同一密码每次哈希结果都不同（$2b$ 开头的串）
def get_hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")  # 注册时：明文 → 指纹

# 密码验证: verify 返回值是布尔型
def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False   # 登录时：输入+库里指纹 → 是否匹配；库中脏数据不抛异常
```

**解剖一个 bcrypt 哈希串**，看懂它就不怕"每次结果都不同"了：

```
$2b$12$KIXQxJ9v8mNk3Oe5pQ1rYuY7zGhXwKvVnR3mTqLdSfA0bCxWjK9Ha
 │   │  └────────盐 + 摘要（合成一段，22 字符盐 + 31 字符摘要）────────┘
 │   └ 成本因子 2^12 = 4096 轮（算得越慢越难暴力破解）
 └ 算法版本
```

**同一个密码每次 hash 出的串都不一样**（因为盐是随机的），那 `checkpw` 怎么验证？——它从**库里那个串**中把盐抠出来，用同样的盐和成本因子把你输入的密码重算一遍，比对摘要。所以"不同"不妨碍"可验证"。

两个必答的面试题顺带解决：

- **为什么不用 MD5/SHA256 直接哈希密码**？它们太快了——GPU 一秒算几十亿次，泄露后可彩虹表/暴力破解。bcrypt 故意慢（成本因子可调），破解成本天壤之别。
- **为什么 `verify_password` 要 try/except**？库里若混入非 bcrypt 格式的脏数据（手改过、别的系统导入的），`checkpw` 会抛 `ValueError`。返回 False 让用户走"密码错误"流程，比抛 500 友好。

本项目曾用 passlib 库封装 bcrypt，因 passlib 多年停更已改为直接使用官方 bcrypt 库——存量哈希串格式不变，无需迁移数据。

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

逐行走查注册函数，每一步对应一个前面章节的知识：

1. `user_data: UserRequest`——第 9 章：请求体自动校验，不合法根本进不了函数体。
2. `db: AsyncSession = Depends(get_db)`——第 7 章：依赖注入，框架自动把会话递进来。
3. 先查重再插入——注意这有**竞态窗口**（两个人同时注册同一用户名可能都通过查重），真正的最后防线是数据库唯一索引 + IntegrityError 处理（第 16 章）。
4. `create_user`（第 10 章）→ `create_token`（第 13 章）→ 包响应返回。

**统一响应结构**（`schemas/response.py`）：所有接口都返回 `{"code": 200, "message": "...", "data": ...}` 三键结构，前端只写一次解析逻辑：

```python
class APIResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None
```

`Generic[T]` 是**泛型模型**：`T` 是"占位类型"，每个路由通过 `response_model=APIResponse[该接口的数据模型]` 声明"data 里装什么"——`APIResponse[UserInfoResponse]` 就表示"这个接口的 data 是 UserInfoResponse 形状"。FastAPI 据此自动完成序列化（datetime→字符串、ORM→dict）和 OpenAPI 文档生成，且**序列化默认按 alias 输出**——这就是第 9 章别名能生效的原因。

知识点：

- `HTTPException(status_code=..., detail=...)`：抛出后由框架接住转成错误响应；本项目用第 16 章的全局处理器把它包成统一三键格式。
- 参数来源三分法：`POST` 请求体=Pydantic 模型参数；URL 查询参数=`Query(...)`（如 `news_id: int = Query(..., alias="newsId")`，把前端的 `newsId` 映射到内部 `news_id`）；路径参数=路径里 `{history_id}`。
- 参数校验直接写在 `Query` 里：`page: int = Query(1, ge=1)`、`page_size: int = Query(10, ge=1, le=100, alias="pageSize")`。**不写校验的代价是真实的**：本项目曾因 `page_size=0` 未拦截，`skip // limit` 直接 ZeroDivisionError 返回 500。

**异常下沉（本项目重构过的点）**：修改用户信息时，crud 层不再抛 Web 异常，而是返回 `None`：

```python
# crud/users.py：只返回数据或 None，不做 HTTP 翻译
if result.rowcount == 0:
    return None

# routers/users.py：HTTP 语义由路由层决定
user = await users.update_user(db, user.username, user_data)
if user is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
```

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
    库里只存 SHA-256 摘要（security.hash_token(token)），原始 token 仅在本次响应中返回一次
    返回 token 给前端

之后每个受保护请求 → utils/auth.py:get_current_user（它也是一个依赖）：
    authorization: str = Header(..., alias="Authorization")   # 从请求头取
    token = authorization[7:].strip() if authorization.startswith("Bearer ") else authorization.strip()
    → crud.get_user_by_token(db, token)：
        对原始 token 做同样的 SHA-256 摘要后查 user_token 表 → 没查到或 expires_at < now → None
        → 再查 user 表拿用户对象
    → 拿不到用户 → 抛 401 "无效的令牌或已经过期的令牌"
```

几个设计点展开：

- **为什么库里只存 SHA-256 摘要不存原文**：数据库泄露（比如备份文件外流）时，攻击者拿到的是摘要——无法反推出可用 token，拿不到能直接登录的会话凭证。比对时对请求头里的原始 token 做同样的摘要再查库即可（SHA-256 是确定性函数，同一输入永远同一输出）。代价是无法从库里反查某个原始 token 属于谁——对教学项目是划算的取舍。
- **每用户仅一条有效令牌**：`user_token` 表有 `user_id` 唯一约束，重新登录直接**更新**旧记录的值和过期时间——旧 token 的摘要被覆盖，自然失效。不用另写"吊销"逻辑。
- **顺手清理**：`create_token` 每次先 `delete` 掉全表已过期的行，防止表无限膨胀。

使用方式极其优雅——**受保护的接口只要多加一个参数**：

```python
async def get_user_info(user: User = Depends(get_current_user)):
```

依赖还能嵌套：`get_current_user` 自己又 `Depends(get_db)`。FastAPI 会先解 db，再解 auth，整条链自动组装。**这就是"依赖注入"的最大价值**：认证逻辑写一次，20 个接口按需挂载。

三个实战细节：

1. `Bearer ` 前缀解析用 `startswith` 严格判断，不要用 `replace("Bearer ", "")`——后者会把 token 中间出现的 "Bearer " 也删掉（本项目真实修过的 bug）。
2. `create_token` 的两个分支（更新/新插）**都要显式 commit**——它可能在请求上下文之外被复用（脚本、后台任务），不能依赖 `get_db` 的收尾提交。
3. 令牌方案的取舍：每请求 2 次查库（token→user）在本项目规模可接受；换 JWT 的思路和前置条件见第 21 章。

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
        Index('title_category_UNIQUE', 'title', 'category_id', unique=True),  # 爬虫去重兜底
    )
    ...
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
```

**索引类比**：书的目录。没有目录（索引），查"分类 1 的新闻"只能从第一页翻到最后一页（全表扫描）；有目录直接翻到那几页。索引不是越多越好——每加一个，写入时都要多维护一份目录，所以只给**高频查询条件**建。

注意 `News` 没有 `category` 关系属性，只有裸的 `category_id` 外键列——本项目刻意不用 relationship，联表全手写 join（第 17 章），好处是查询行为完全可控，代价是多写几行。

**分页的真实演示**：拿种子数据（某分类 15 条）来算。路由层换算 `offset = (page - 1) * page_size`：

| 请求 | SQL 的 offset/limit | 返回 | hasMore 计算 |
|------|--------------------|------|--------------|
| `page=1&pageSize=10` | offset=0, limit=10 | 第 1~10 条 | (0 + 10) < 15 → true |
| `page=2&pageSize=10` | offset=10, limit=10 | 第 11~15 条（只 5 条） | (10 + 5) < 15 → false |

`offset/limit` 就是翻页的本质："跳过前 N 条，取 M 条"。**hasMore（还有没有下一页）**有两种等价写法，本项目两种都用了（新闻接口用前者，收藏/历史用后者）：

```python
has_more = (offset + len(news_list)) < total      # 已取到的 + 本页条数 < 总数
has_more = total > page * page_size               # 总数超过"前 page 页容量"
```

**浏览量自增**（`crud/news.py:increase_news_views`）：

```python
stmt = update(News).filter_by(id=news_id).values(views=News.views + 1)   # 数据库端自增，非先读后写
result = await db.execute(stmt)
await db.commit()
if result.rowcount > 0:
    await invalidate_news_caches(news_id)      # 写库成功 → 失效相关缓存（第15章）
return result.rowcount > 0
```

`News.views + 1` 生成的是 SQL 表达式 `views = views + 1`，**并发下也不会丢计数**（对比"读出来+1再写回"的丢更新问题）。

路由层（`routers/news.py`）不直接调用它，而是挂到 `BackgroundTasks` 上——浏览量在**响应发出之后**才后台 +1，接口秒回，且响应里的 `views` 是本次浏览前的值：

```
请求到达 → 查详情（返回旧 views）→ 组响应 → 发给用户 ──→ 用户已拿到响应
                                                    └→ 后台才执行 update views+1
```

注意后台任务执行时请求级会话已关闭，函数内部要自建 `AsyncSessionLocal` 会话。

**复现要点**：models/news.py → crud 的五个查询函数（先不管缓存，直接查库）→ routers/news.py 三个接口（列表、详情、分类）。`/docs` 里验证分页参数 `page=0` 返回 400（`data` 为字段级错误明细）而不是 500。

---

## 15. 缓存体系：穿透、雪崩与一致性

**先看没有缓存的世界**：首页每次刷新 = 分类查询 + 列表查询 + count 总数 ≈ 3 次数据库查询。10 个人同时在线就是每秒 30 次查询，MySQL 每秒能扛的查询是有限的（简单查询几千，复杂查询几百）——**缓存就是把"读极多、改极少"的数据（新闻列表/详情/分类）放进内存级的 Redis，把数据库从重复劳动里解放出来**。策略：先问 Redis，没有再查 MySQL，查到顺手写回 Redis 并设过期时间。

`cache/news_cache.py` 集中管理所有键规则（crud 层只调函数、不拼键）：

| 键 | 内容 | 默认 TTL |
|----|------|----------|
| `news:categories:{skip}:{limit}` | 分类列表（分页编入键） | 7200s（2小时） |
| `news:list:{分类}:{页}:{大小}` | 列表页 | 1800s（30分钟） |
| `news:detail:{id}` | 新闻详情 | 300s（5分钟） |
| `news:count:{分类}` | 分类新闻总数 | 1800s |
| `news:related:{id}:{分类}` | 相关新闻（空结果短 TTL 占位） | 1800s |

数据越稳定 TTL 越长（分类几天不变 → 2 小时；详情会因浏览量变化 → 5 分钟）。**缓存三大经典问题及本项目解法**（面试高频，也是实际必踩）：

**① 缓存穿透**：查询"不存在的东西"（如 `id=99999999`），Redis 永远没有 → 每次都打到 MySQL。攻击者可用不存在的 id 扫你。
解法：**空结果也缓存**，但只给 60 秒（`EMPTY_TTL`），存占位标记 `{"__empty__": true}`。读取侧 `_detect_empty()` 统一识别（兼容裸 marker 和 `[marker]` 两种形态），命中就还原成内存哨兵 `EMPTY`，crud 层看到它直接返回空，不碰数据库。新数据最多延迟 1 分钟可见，可接受。

**② 缓存雪崩**：大量键**同一时刻**集体过期，请求洪峰全部涌向 MySQL。
解法：TTL 加 ±10% 随机抖动——`_with_jitter()` 让同类键的过期时间错开（1800 秒的键实际在 1620~1980 秒之间随机过期，不会挤在同一秒）。

**③ 缓存一致性**：数据库改了，缓存还是旧值。本项目策略是"写后失效"：浏览量写库成功 → `invalidate_news_caches(news_id)` 删掉该新闻的详情缓存和相关新闻缓存（列表缓存允许 TTL 内短暂滞后——每次浏览都清空全部列表缓存会让缓存形同虚设，这是明确的取舍）。

**降级**：所有 Redis 读写都包在 `try/except` 里，失败只 `logger.warning` 并返回 None——**Redis 全挂，系统退化为直连数据库，功能不中断**。缓存是加速器，不是命脉。

**复现要点**：先写 `config/cache_conf.py` 的 `get_json_cache/set_cache/delete_cache/delete_cache_pattern`（`scan_iter` 渐进扫描按前缀删，避免 `keys *` 阻塞 Redis），再写 `cache/news_cache.py` 键规则层，最后回填到第 14 章的 crud 里。验证：请求一次详情（`SQL_ECHO=true` 能看到查库日志）→ 再请求一次（无查库日志=命中缓存）→ `redis-cli` 里 `keys news:*` 看键、`TTL news:detail:1` 看剩余秒数；停掉 Redis 服务再请求（应正常返回但日志里有 warning）。

---

## 16. 全局异常处理：utils/exception.py

**先看没有全局处理器的世界**：业务代码里 `raise HTTPException(400, "...")` 之外，任何漏网的异常（数据库挂了、代码写错了）都会让 FastAPI 返回默认的 500 页面——响应体里可能带着 Python 文件路径、代码行号，**等于把内部地图交给攻击者**；而且格式和业务错误不统一，前端没法统一处理。

FastAPI 的**全局异常处理器**：某类异常抛出到顶层，统一由一个函数转成响应。`utils/exception_handlers.py` 注册了 5 个，**从具体到抽象**（先注册的先匹配，所以具体的放前面）：

```python
app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # 参数校验：统一转 400 + 字段明细
app.add_exception_handler(HTTPException, http_exception_handler)      # 业务主动抛的
app.add_exception_handler(IntegrityError, integrity_error_handler)    # 数据库唯一约束/外键
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # 其他数据库错误
app.add_exception_handler(Exception, general_exception_handler)       # 兜底：谁都没接住的
```

最有教学价值的是 `integrity_error_handler`：数据库的 IntegrityError 报错文本里带着**违反了哪个约束**的名字，据此映射成人话。两种数据库的报错长得很不一样：

```
MySQL  ：Duplicate entry 'tom' for key 'user.username_UNIQUE'
SQLite ：UNIQUE constraint failed: user.username
```

所以查找顺序是**先按约束名精确匹配（MySQL 走这条）、再按列名兜底（SQLite 走这条）**：

```python
CONSTRAINT_MESSAGES = {
    "username_UNIQUE": "用户名已存在",
    "phone_UNIQUE": "手机号已被注册",
    "user_news_unique": "已收藏过该新闻",
    ...                                                    # 与 database.sql 里的约束名一一对应
}
COLUMN_MESSAGES = {
    "user.username": "用户名已存在",
    "favorite.user_id, favorite.news_id": "已收藏过该新闻",
    ...
}
detail = next((msg for name, msg in CONSTRAINT_MESSAGES.items() if name in error_msg), None)
if detail is None:
    detail = next((msg for col, msg in COLUMN_MESSAGES.items() if col in error_msg), None)
```

参数校验同理：`RequestValidationError` 不走 FastAPI 默认的 422，而是统一转成 400，`data` 里带 `[{field, message}]` 字段级明细，`message` 由 `VALIDATION_MESSAGE_MAP` 把 Pydantic 错误类型翻译成人话（如 `string_too_short` → `长度不足`）。

本项目曾把所有 Duplicate entry 一律报"用户名已存在"——收藏重复时用户看到的就是驴唇不对马嘴的提示。**错误消息是产品的一部分**。

另一个要点是 `DEBUG_MODE`（每次处理异常时实时读取环境变量，不依赖模块导入顺序）：

```python
def _debug_mode() -> bool:
    return os.getenv("DEBUG_MODE", "false").lower() == "true"
```

调试模式下错误响应的 `data` 里附带异常类型、详情、**完整堆栈**和请求路径（排障神器）；生产必须 false，否则数据库结构、文件路径全泄露给攻击者。对照：

```json
// DEBUG_MODE=false（生产）
{ "code": 500, "message": "服务器内部错误", "data": null }
// DEBUG_MODE=true（本地）
{ "code": 500, "message": "服务器内部错误", "data": { "error_type": "ZeroDivisionError",
  "error_detail": "division by zero", "traceback": "Traceback ...", "path": "http://..." } }
```

**复现要点**：写两个 handler（HTTPException + 兜底 Exception 最小可用），故意注册重复用户名触发 IntegrityError，观察 400 响应的 message 随约束名变化。

---

## 17. 收藏与历史模块：join 查询与唯一约束

这两个模块教你 ORM 的进阶三板斧：**联表、聚合、条件删除**。

**联表查询**（`crud/favorite.py:get_favorite_list`）——收藏列表要展示"新闻内容 + 收藏时间"，数据分散在两张表（favorite 只存 user_id/news_id 两个数字，标题内容在 news 表里）：

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

`join` 读法："把 favorite 表按 `favorite.news_id == news.id` 贴到 news 表旁边"——匹配上的行拼成一行返回。**结果集的形状**是元组列表，每个元组是 `(News对象, 收藏时间, 收藏id)`，所以路由层解包时是 `for n, ft, fid in rows`。

**"N+1 问题"顺带讲清**：先查 10 条收藏、再循环 10 次查每条新闻 = 1+10 次查询（N 条收藏就是 N+1 次）；一次 join = 1 次。数据量大时是天壤之别。

**唯一约束兜住并发**（`models/favorite.py`）：`UniqueConstraint('user_id','news_id', name='user_news_unique')` 保证同一用户对同一新闻最多一条收藏。为什么"代码里先查再插"不够？——两个请求同时到达：都查了"没收藏过"→ 都执行插入 → 重复了。**应用层查重永远有竞态窗口，数据库约束是最后防线**。违反约束时抛 IntegrityError，由第 16 章的处理器翻译成"已收藏过该新闻"。

**历史模块的两个要点**：

1. **删除语义要对齐文档**：`DELETE /api/history/delete/{history_id}` 按**历史记录主键**删并**限定归属**——`where(History.user_id == user_id, History.id == history_id)`。两个条件缺一不可：只按 id 删，别人就能删你的记录（**水平越权**——访问不属于自己的资源）。本项目修过把路径参数当 news_id 匹配的真实 bug，也顺手杜绝了越权。
2. **add_history 是 upsert 语义**：先查"该用户该新闻"有没有记录，有就**更新浏览时间**（重复浏览不产生重复行），没有才插入。
3. **时间字段**：`view_time` 默认 `datetime.now`（不带括号，第 8 章的坑），并有 `idx_view_time` 索引支撑"按浏览时间倒序"的高频排序。

**复现要点**：models → crud（5+4 个函数）→ 路由。验证：收藏→重复收藏（400 且文案正确）→ 列表联表数据完整 → 删除别人（换个账号）的记录 id 返回 404。

---

## 18. 组装：main.py（路由、CORS、日志、定时任务）

所有零件齐了，`main.py` 负责总装——它不足百行，但这几件事都有讲究：

**① 日志**：`logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), ...)`。各模块用 `logging.getLogger("app.cache")` 拿自己的 logger（日志会带模块名前缀，一眼看出是谁打的）。对比 `print`：日志有级别、时间戳、来源，可统一开关（这就是为什么第 15 章的降级警告不是 print）。

**② CORS 中间件**——前后端分离必然遇到的问题。**通俗解释**：浏览器默认禁止"A 网站的页面 JS 请求 B 网站的接口"（同源策略），跨域请求会被浏览器拦下（注意：是浏览器拦，curl/Postman 不受影响）。CORS 是服务器"声明允许谁来调"的机制——浏览器发起真正的跨域请求前，可能先发一个 OPTIONS 预检请求问服务器"我能不能来"，服务器在响应头里表态。

```python
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    cors_origins = ["*"]; cors_credentials = False   # 开发：全放开
else:
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    cors_credentials = True                           # 生产：白名单
```

**易错点**：`allow_origins=["*"]` 与 `allow_credentials=True` 不能同时用（HTTP 规范禁止通配源携带凭证），所以开发模式必须把 credentials 关掉。

**③ 注册路由与异常处理器**：

```python
register_exception_handlers(app)      # 第16章
app.include_router(news.router)       # 第12-17章的所有 router
app.include_router(users.router)
...                                    # 共 6 个 router（含 ai、crawler）
```

**④ 定时任务（lifespan）**：RSS 爬虫的调度注册在 `lifespan` 生命周期钩子里——应用启动时先抓一次，之后 `AsyncIOScheduler` 默认每 6 小时一轮（`CRAWL_INTERVAL_HOURS` 可调）；`CRAWLER_ENABLED=false` 可整体关闭（如开发环境反复热重载时），关闭状态下 shutdown 前要判断 `scheduler.running` 再停，否则抛 `SchedulerNotRunningError`（本项目真实修过的坑）。用 lifespan 而不是模块顶层代码的好处：任务随应用启停，不泄漏后台线程。

**复现要点**：把 6 个 router 挂上（含 ai、crawler）、CORS 按 DEBUG 切换、logging 配置好、lifespan 注册定时抓取。至此你的后端与 `backend/main.py` 等价。

---

## 19. 前端对接点速览

后端项目的你只需要知道"我的接口被谁、以什么姿势调用"，30 秒版：

- **统一请求器**：`frontend/src/api/request.js` 创建了 axios 实例（baseURL 读 `VITE_API_BASE_URL`，默认 `http://127.0.0.1:8000`），请求拦截器自动加 `Authorization: Bearer <token>`，响应拦截器遇到 401 清除本地登录态并跳登录页（带 redirect 回跳）。**所以前端永远不需要手动拼鉴权头**。
- **接口消费点**：每个业务页面的数据都走 Pinia store——`store/user.js` 调用户 5 接口，`store/modules/news.js` 调新闻 3 接口，`favorite.js`/`history.js` 调收藏与历史。
- **AI 问答**：`views/AIChat.vue` 用 fetch 调后端代理 `/api/ai/chat`（SSE 流式），前端零密钥；提供方（智谱/Ollama）与 Key 都在后端 `.env`。
- **Token 存哪**：登录成功后 token 存进 Pinia 并经 `pinia-plugin-persistedstate` 持久化到 localStorage（键 `user-store`），页面刷新不丢。
- **联调时的跨域**：开发模式后端 CORS 全放开直接调；若想摆脱 CORS，前端 vite 代理已备好（`vite.config.js` 的 `/api-proxy`）。
- **联调排错**：前端报"网络请求失败"先看后端终端日志和 `/docs` 能否手工调通——99% 是后端问题或参数名大小写不符（对照 `api-spec.md` 的 alias）。

---

## 20. 调试与排错手册

| 症状 | 大概率原因 | 手段 |
|------|-----------|------|
| 启动即报 `Can't connect to MySQL` | MySQL 没启动 / `.env` 密码错 / 库没建 | 先 `mysql -uroot -p` 能进；重导 `database/database.sql` |
| 启动报 `ModuleNotFoundError` | 没进 conda 环境 / 目录不对 | `conda activate ./.conda-env`；必须在 `backend/` 下执行 `uvicorn main:app` |
| `Address already in use` / `[Errno 10048]` | 8000 端口被占（通常已开着一个 uvicorn） | 关掉旧进程再启动 |
| 接口返回 400 | 参数缺失/类型错/`page<1`/密码<6位 | 响应 `data` 是字段级错误明细数组；`/docs` 里看该接口的 Schema |
| 接口返回 400 但不是参数问题 | 业务规则拒绝（重复用户名/重复收藏/旧密码错） | 看 `message`：约束冲突按约束名给文案，旧密码错误固定「旧密码不正确」 |
| 401 无效令牌 | 没带 Authorization / token 过期 / Bearer 格式错 | 先登录拿新 token；`/docs` Authorize 重新填 |
| 404 | id 不存在 / 删除了不属于自己的资源 | 对照 `api-spec.md` |
| 429 | 登录尝试太频繁（60 秒内超 5 次） | 等 1 分钟，或重启后端（限流状态在内存里） |
| 500 数据库操作失败 | 看**后端终端日志**（`LOG_LEVEL=INFO` 以上必打） | 开 `SQL_ECHO=true` 看具体 SQL |
| `AttributeError: 'NoneType' object has no attribute ...` | `scalar_one_or_none()` 返回 None 后没判空就用 | 查不到是正常分支，先 `if not obj: raise HTTPException(404, ...)` |
| 中文/emoji 入库报错或乱码 | 连接串没用 utf8mb4 / 建库时字符集不对 | 连接串带 `?charset=utf8mb4`；重建库时指定 utf8mb4 |
| 隔夜后接口报 `server has gone away` | 闲置连接被 MySQL 掐断，池里没有探活 | `pool_pre_ping=True`（本项目已配） |
| 响应字段名和预期对不上 | alias 机制（`publishedTime` vs `publish_time`） | 以 `api-spec.md` 为准 |
| 改了代码不生效 | uvicorn 忘了 `--reload` / 改错环境 | 确认激活的是 `.conda-env` |
| 请求卡住好几秒 | Redis 挂了但没超时（本项目已配 2s 超时，快速失败降级） | `redis-cli ping` 检查；日志里找 `app.cache` 的 warning |

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
| `update_user` 的 `exclude_none=True` 导致无法把可选字段清回 null | PATCH 语义的简单实现 | 需要时改用 `exclude_unset` + 显式 None 处理 |
| 无数据库迁移（表靠 `database.sql`） | 表结构稳定、项目规模小 | 引入 Alembic：模型变更自动生成迁移脚本（前置：统一 metadata，已完成） |
| 自动化测试 | 已有：后端 pytest 48 例（接口/缓存层/爬虫/限流，aiosqlite+fakeredis 免真实服务）+ 前端 vitest 18 例 | 接入 CI（如 GitHub Actions），每次提交自动跑 |

---

## 附录 A：复现检查清单

- [ ] conda 环境建立，12 个依赖能 import
- [ ] `uvicorn main:app` 启动，`/` 与 `/docs` 可访问
- [ ] `config/`：连接串从 `.env` 拼出；Redis 客户端带超时；engine 带 `pool_pre_ping`
- [ ] `models/`：7 个模型 + 统一 Base + TimestampMixin；`datetime.now` 不带括号
- [ ] `schemas/`：各模块 Request/Response，alias 与 `api-spec.md` 一致
- [ ] `utils/`：bcrypt 哈希自测通过；`schemas/response.py` 的 `APIResponse` 泛型包络
- [ ] `crud/users.py`：注册后 user 表有 bcrypt 密码行；`update_user` 返回 None 而非抛 HTTP 异常
- [ ] `routers/users.py`：/docs 全链路（注册→登录→信息→改密）
- [ ] `utils/auth.py`：错误 token 401，正确 token 200；库里 token 列是 64 位 SHA-256 摘要
- [ ] `crud/news.py` + `routers/news.py`：分页 hasMore 正确，`page=0` 是 400
- [ ] 缓存：二次请求不产生 SQL 日志；Redis 停掉后功能仍可用（降级）
- [ ] 浏览量自增后，详情缓存被失效（再次请求看到新浏览量）
- [ ] 重复注册/重复收藏返回 400 且文案与约束对应
- [ ] 收藏/历史 join 列表含时间与 id；历史删除仅限本人记录
- [ ] `main.py`：CORS 随 DEBUG_MODE 切换；日志替代 print；lifespan 注册定时抓取
- [ ] `POST /api/crawler/run`（登录后）返回 `fetched/inserted/skipped` 统计
- [ ] `python -m pytest` 48 例全部通过（aiosqlite + fakeredis，无需真实 MySQL/Redis）

## 附录 B：术语表

| 术语 | 一句话解释 |
|------|-----------|
| HTTP 方法 | GET 读 / POST 建 / PUT 改 / DELETE 删，接口的"动词" |
| 状态码 | 200 成功、400 参数/业务/校验错（本项目校验失败也归 400）、401 未认证、404 不存在、429 请求过于频繁、500 服务器内部错 |
| 端点（endpoint） | 一个"方法 + 路径"组合，如 `GET /api/news/list` |
| 请求头/请求体 | 头=元信息（鉴权、内容类型），体=真正的数据（POST/PUT 才有） |
| JSON | 前后端通用的数据格式；Python dict ↔ JSON 字符串靠 `json.dumps/loads` 互转 |
| 环境变量 / .env | 进程级的配置来源；`.env` 文件由 python-dotenv 灌进 `os.environ`，不入 git |
| 虚拟环境 | 独立的 Python 包安装空间，项目之间互不污染（本项目用 conda 管理） |
| 装饰器 | `@xxx` 语法糖，等价于"函数 = 外层函数(函数)"，FastAPI 用它注册路由 |
| 依赖注入 | 框架自动准备参数（db 会话、当前用户），函数只声明"我需要什么" |
| 生成器 / yield | `yield` 把函数劈成两半，两次执行之间框架可以插手（get_db 的收尾逻辑） |
| ORM | 用类/对象操作数据库，SQL 由框架生成并参数化 |
| 连接池 | 预先建好的数据库连接复用，避免每次请求都握手；`pool_pre_ping` 取用前探活 |
| 主键 / 外键 | 主键=行的唯一编号；外键=指向别的表主键的"引用"，数据库帮你检查合法性 |
| 索引 | 表的目录，加速查询、拖慢写入；只给高频查询条件建 |
| 事务 | 一组写操作的原子包裹：commit 全生效 / rollback 全撤销 |
| 占位符 / 参数化 | SQL 里用 `?`/`%s` 占位、参数单独传，杜绝 SQL 注入 |
| 唯一约束 | 数据库层面拒绝重复值（单列或多列联合），并发下的最后防线 |
| 缓存穿透 | 查询不存在的数据，缓存永远失效、全打到数据库 |
| 缓存雪崩 | 大量缓存键同时过期，请求洪峰压垮数据库 |
| 写后失效 | 数据库写成功后删除对应缓存，下次读重新加载 |
| 哈希/盐 | 不可逆"指纹"；盐让相同密码指纹也不同 |
| N+1 查询 | 先查列表再逐条查关联数据；用 join 一次取齐 |
| 水平越权 | 访问不属于自己的资源；删除/查询必须带归属条件 |
| upsert | 存在则更新、不存在则插入（本项目的 add_history） |
| 迁移 | 表结构变更的版本化管理工具（Alembic） |

## 附录 C：完整请求/响应示例集（curl）

以下示例可直接复制运行（先 `cd backend` 起服务，另开一个终端执行；`TOKEN` 变量在登录后设置）。GET 请求用浏览器打开等价。

**1. 注册**（成功返回 token + userInfo；重复用户名返回 400「用户已存在」）：

```bash
curl -X POST http://127.0.0.1:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "tom_cat", "password": "pass123456"}'
```

**2. 登录**（失败返回 401「用户名或密码错误」；60 秒内错 5 次返回 429）：

```bash
curl -X POST http://127.0.0.1:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tom_cat", "password": "pass123456"}'
# 从响应里取出 token 存进变量（Git Bash）：
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tom_cat", "password": "pass123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
```

**3. 带 token 访问需要登录的接口**（对照：去掉 `-H "Authorization: ..."` 会得到 401）：

```bash
curl http://127.0.0.1:8000/api/user/info -H "Authorization: Bearer $TOKEN"
```

**4. 新闻分类与列表**（无需登录；列表分页参数对照第 14 章）：

```bash
curl "http://127.0.0.1:8000/api/news/categories"
curl "http://127.0.0.1:8000/api/news/list?categoryId=1&page=1&pageSize=10"
```

**5. 参数校验失败的 400**（`page=0` 违反 `ge=1`）：

```bash
curl "http://127.0.0.1:8000/api/news/list?categoryId=1&page=0"
# {"code":400,"message":"不能小于最小值","data":[{"field":"page","message":"不能小于最小值"}]}
```

**6. 收藏一条新闻**（先收藏返回 200，重复收藏返回 400「已收藏过该新闻」）：

```bash
curl -X POST http://127.0.0.1:8000/api/favorite/add \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"newsId": 1}'
```

> 提示：把 curl 换成 `/docs` 页面上的"Try it out"效果相同且更直观——每个接口都能填参数、带 Authorize、看完整响应。

