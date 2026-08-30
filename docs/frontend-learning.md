# 前端学习文档：从零理解「AI 头条新闻系统」前端

> **这份文档是写给谁的**：新加入项目的前端开发者。假设你了解 Vue 基础语法（组件、props、v-for），但对本项目的目录组织、状态管理和业务流转还不熟悉。
>
> **这份文档能做什么**：带你按"请求从哪里发出、数据存在哪里、页面怎么渲染"的脉络，把 `frontend/` 目录完整过一遍。每一章都是：**为什么这样设计（概念）→ 本项目怎么做的（对照真实代码）→ 你上手要做什么（要点）**。
>
> **怎么用**：左手开这份文档，右手开编辑器里的 `frontend/` 目录，边读边对照。后端不是重点，只在第 9 章讲"前端发出的请求到了后端会发生什么"，接口的完整定义见 [api-spec.md](api-spec.md)。

---

## 目录

- [1. 项目是什么：前端在系统中的角色](#1-项目是什么前端在系统中的角色)
- [2. 技术栈地图：每个东西是干嘛的](#2-技术栈地图每个东西是干嘛的)
- [3. 环境搭建与第一次启动](#3-环境搭建与第一次启动)
- [4. 目录结构与分层职责](#4-目录结构与分层职责)
- [5. 应用装配：main.js 逐行做了什么](#5-应用装配mainjs-逐行做了什么)
- [6. 路由组织：路由表与 keepAlive](#6-路由组织路由表与-keepalive)
- [7. 网络层：axios 封装与 Token 流转](#7-网络层axios-封装与-token-流转)
- [8. 状态管理：六个 store 的分工与持久化](#8-状态管理六个-store-的分工与持久化)
- [9. 数据流转全景：一次打开详情的完整旅程](#9-数据流转全景一次打开详情的完整旅程)
- [10. 核心公共组件](#10-核心公共组件)
- [11. 业务模块：新闻流 Home](#11-业务模块新闻流-home)
- [12. 业务模块：详情页与收藏历史的联动](#12-业务模块详情页与收藏历史的联动)
- [13. 业务模块：AI 问答 SSE 流式](#13-业务模块ai-问答-sse-流式)
- [14. 国际化与分类名映射](#14-国际化与分类名映射)
- [15. 主题系统：CSS 变量方案](#15-主题系统css-变量方案)
- [16. 测试：vitest 的结构与写法](#16-测试vitest-的结构与写法)
- [17. 开发约定与代码规范](#17-开发约定与代码规范)
- [18. 调试与排错手册](#18-调试与排错手册)
- [19. 已知取舍与注意点](#19-已知取舍与注意点)
- [附录 A：上手自查清单](#附录-a上手自查清单)
- [附录 B：localStorage 键速查](#附录-blocalstorage-键速查)

---

## 1. 项目是什么：前端在系统中的角色

这是"仿今日头条"新闻系统的**移动端 H5 前端**（Vue 3 单页应用），与 FastAPI 后端纯 HTTP + JSON 通信，不生成任何服务端页面。它提供 11 个页面：首页新闻流、分类、新闻详情、收藏、浏览历史、AI 问答、我的、登录、注册、个人信息、设置。

**一句话概括架构**：页面组件（views）只管"渲染 + 收集用户操作" → 数据全部存放在 Pinia store → store 的 action 调用统一的 axios 实例发请求 → 后端返回 `{code, message, data}` → action 把结果写回 state → 页面自动响应式更新。AI 问答是唯一的例外：它用原生 `fetch` 直连后端 SSE 流（第 13 章）。

**一个重要前提**：前端零密钥。AI 提供方（智谱/本地 Ollama）与 API Key 全部在后端 `.env` 配置，前端只调用后端代理接口 `/api/ai/chat`。

---

## 2. 技术栈地图：每个东西是干嘛的

| 名词 | 它是什么 | 本项目怎么用 |
|------|----------|--------------|
| **Vue 3.5** | 渐进式前端框架，本项目全部使用组合式 API | 所有组件统一 `<script setup>` 写法 |
| **Vite 7** | 开发服务器 + 构建工具 | `npm run dev` 起本地服务；同时承载 vitest 配置 |
| **Vue Router 4** | SPA 路由 | 12 条路由，`createWebHistory`，全量懒加载 |
| **Pinia 3** | 状态管理 | 6 个 store：user / news / favorite / history / theme / language |
| **pinia-plugin-persistedstate 4** | store 持久化到 localStorage | 仅 user store 启用（键 `user-store`），刷新不丢登录态 |
| **Vant 4** | 移动端组件库 | 在 `main.js` **手动按需注册**，不用自动导入插件 |
| **vue-i18n 9** | 国际化 | `legacy: false` 组合式 API，zh-CN / en-US 双语言包 |
| **axios** | HTTP 客户端 | `src/api/request.js` 统一封装 baseURL / Bearer / 401 处理 |
| **marked + DOMPurify** | Markdown 渲染 + HTML 消毒 | AI 回复渲染专用，防 XSS |
| **vitest 4 + @vue/test-utils + jsdom** | 单元测试 | 4 个测试文件 16 例，配置内嵌在 `vite.config.js` |
| **ESLint 10 + Prettier** | 代码检查 / 格式化 | ESLint 扁平配置管正确性，Prettier 管格式 |

**两个必须先建立的观念**：

1. **视图薄、store 厚**：views 里不直接写 `request.get(...)`（唯一例外是 AIChat 的 fetch），所有接口调用都封装在 store action 里。找一个接口的实现，先去 `store/` 找。
2. **双轨数据**：收藏和历史有"本地态"与"服务端态"两份（未登录也能用，登录后以服务端为准），代码里处处能看到 `xxxApi()` 与本地 `xxx()` 两个方法，不要混淆（第 12 章）。

---

## 3. 环境搭建与第一次启动

> 目标：把前端跑起来并连上后端。

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 配置环境变量：复制模板（不填则默认连 http://127.0.0.1:8000）
cp .env.example .env.local

# 3. 启动开发服务器
npm run dev
```

浏览器打开 http://localhost:5173 （手机模拟器视图效果最佳，F12 切换设备模拟）。

**前置条件**：后端必须已启动（`backend/` 下 `uvicorn main:app`，见 [backend-learning.md](backend-learning.md) 第 3 章），否则页面能开但所有列表为空、控制台报网络错误。

**摆脱 CORS 依赖（可选）**：开发模式后端 CORS 全放开，直接连即可。若想走代理，把 `.env.local` 的 `VITE_API_BASE_URL` 改为 `/api-proxy`——`vite.config.js` 已配置该前缀转发到 `http://127.0.0.1:8000` 并重写去掉前缀。

常用脚本（`package.json`）：

| 命令 | 作用 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` / `npm run preview` | 生产构建 / 本地预览构建产物 |
| `npm run test` | 跑 vitest 全部 16 例（`test:watch` 进入监听模式） |
| `npm run lint` / `lint:fix` | ESLint 检查 / 自动修复 |
| `npm run format` | Prettier 格式化 `src/` |

---

## 4. 目录结构与分层职责

```
frontend/
├── index.html                # SPA 唯一 HTML 入口（<div id="app"> + /src/main.js）
├── vite.config.js            # Vite + vitest 配置：@ 别名、jsdom 环境、/api-proxy 代理
├── eslint.config.js          # ESLint 10 扁平配置（含浏览器全局变量白名单）
├── .prettierrc.json          # Prettier：无分号 / 单引号 / 行宽 100 / es5 逗号
├── .env.example              # 环境变量模板（复制为 .env.local）
└── src/
    ├── main.js               # 应用装配：i18n → Vant 按需注册 → router → pinia → 主题初始化
    ├── App.vue               # 根组件：router-view + 按 meta.keepAlive 决定是否 keep-alive
    ├── style.css             # 全局样式
    ├── api/
    │   └── request.js        # axios 实例：baseURL、10s 超时、Bearer 注入、401 清理
    ├── config/
    │   └── api.js            # apiConfig.baseURL（读 VITE_API_BASE_URL）+ AI 端点常量
    ├── constants/
    │   └── categories.js     # 后端中文分类名 → i18n key 的映射表
    ├── router/
    │   └── index.js          # 12 条路由 + beforeEach 设置页面标题
    ├── store/
    │   ├── index.js          # createPinia + persistedstate 插件
    │   ├── user.js           # 用户会话（唯一启用持久化的 store）
    │   ├── theme.js          # 主题（CSS 变量 + localStorage）
    │   ├── language.js       # 界面语言（localStorage）
    │   └── modules/          # 业务数据 store：news / favorite / history
    ├── i18n/
    │   ├── index.js          # createI18n（legacy: false）+ 语言切换辅助
    │   └── locales/          # zh-CN.js / en-US.js 语言包
    ├── components/           # 公共组件：TabBar / NewsItem / NewsRecordList
    └── views/                # 11 个页面组件（与路由一一对应）
```

**分层依赖方向**：`views → store → api/request → 后端`。公共组件（components）被 views 使用，不反向依赖任何 store。`constants/` 与 `config/` 是被任意层引用的纯常量。

**一个现状说明**：`vite.config.js` 配了 `@` → `src/` 的路径别名，但**现有代码一律使用相对路径**（如 `../../api/request`）。写新代码时保持相对路径习惯，与现有风格一致。

---

## 5. 应用装配：main.js 逐行做了什么

`src/main.js` 是唯一知道"全局有哪些东西"的文件，顺序有讲究：

1. **创建 app 并挂 i18n**：`setupI18n()`（`src/i18n/index.js`）在创建实例前读 `localStorage.getItem('language')`，保证首屏就是用户上次选的语言；`legacy: false` 启用组合式 API 模式。
2. **Vant 按需注册**：`main.js` 顶部 `import { Button, NavBar, ... } from 'vant'` 并逐个 `app.use(...)`，样式只引一次 `vant/lib/index.css`。**新页面想用一个没用过的 Vant 组件，必须先来这里注册**，否则渲染为空且不报错（常见新手坑）。
3. **挂 router、pinia**，`app.mount('#app')`。
4. **初始化主题**：mount 之后 `useThemeStore().initTheme()` 把主题写入 CSS 变量（第 15 章）——必须在 pinia 安装之后，因为 useThemeStore 依赖 pinia 实例。

`src/App.vue` 只有一件事：渲染路由出口，并按路由元信息决定是否缓存：

```html
<router-view v-slot="{ Component }">
  <template v-if="$route.meta.keepAlive">
    <keep-alive>
      <component :is="Component" />
    </keep-alive>
  </template>
  <template v-else>
    <component :is="Component" />
  </template>
</router-view>
```

---

## 6. 路由组织：路由表与 keepAlive

路由表在 `src/router/index.js`，全部懒加载（`() => import('../views/Xxx.vue')`），首屏只加载当前页：

| 路径 | 组件 | keepAlive | 说明 |
|------|------|-----------|------|
| `/` | — | — | redirect 到 `/home` |
| `/home` | Home.vue | ✅ | 首页新闻流（Tabs + 无限滚动） |
| `/category` | Category.vue | ✅ | 全部分类宫格 |
| `/news/detail/:id` | NewsDetail.vue | ❌ | 详情，路径参数 `:id` |
| `/aichat` | AIChat.vue | ✅ | AI 问答（保留对话记录） |
| `/my` | My.vue | ✅ | 个人中心 |
| `/favorite` / `/history` | Favorite / History | ❌ | 收藏 / 历史列表 |
| `/login` / `/register` | Login / Register | ❌ | 认证页 |
| `/profile` / `/settings` | Profile / Settings | ❌ | 资料编辑 / 设置 |

两个全局机制：

- **标题**：`router.beforeEach` 里 `document.title = to.meta.title || '新闻资讯'`，标题全部来自 `meta.title`。
- **keepAlive**：`meta.keepAlive: true` 的页面（Home/Category/AIChat/My）切走再切回不重新挂载——这就是首页 Tabs 滚动位置和 AI 对话记录能保留的原因。新增列表页时想清楚要不要缓存：缓存了就要自己处理数据刷新时机。

**本项目没有路由级登录守卫**。需要登录的操作在页面内检查（如 NewsDetail 点收藏、AIChat 发消息前查 `userStore.getLoginStatus`），未登录时 toast 提示并跳 `/login`。这是有意为之：游客可以浏览新闻，只在写操作时才要求登录。

---

## 7. 网络层：axios 封装与 Token 流转

`src/api/request.js` 是所有 HTTP 请求（除 AIChat 的 fetch）的唯一出口：

```js
const request = axios.create({
  baseURL: apiConfig.baseURL,   // 来自 src/config/api.js，读 VITE_API_BASE_URL
  timeout: 10000,
})
```

三个关键机制：

1. **Token 注入**：请求拦截器给每个请求加 `Authorization: Bearer <token>`。token 有两个来源：`setAuthToken()` 注入的模块内变量（登录后设置），以及兜底函数 `readPersistedToken()`——页面刷新后模块变量丢失，从 localStorage 的 `user-store` 键（user store 的持久化）里解析出来。
2. **401 处理**：响应拦截器发现 401 就 `setAuthToken(null)` + `localStorage.removeItem('user-store')` 清掉本地登录态，然后**继续抛错**给调用方（由 store 捕获后返回失败信息）。
3. **baseURL 集中一处**：`src/config/api.js` 的 `apiConfig.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'`。改后端地址只动 `.env.local`。

**Token 的完整生命周期**：

```
登录成功 → user store: this.token = token; setAuthToken(token)
        → persist 插件把整个 state 写入 localStorage('user-store')
页面刷新 → 模块内 token 为 null → 拦截器回退 readPersistedToken()
401 响应 → 双清（模块变量 + localStorage）→ 用户需重新登录
退出登录 → logout() action 里同样双清
```

**接口路径写在 store action 里**（如 `request.get('/api/news/list', { params })`），本项目没有集中式的 `api/xxx.js` 接口定义层——对照 [api-spec.md](api-spec.md) 的路径即可找到实现位置。

---

## 8. 状态管理：六个 store 的分工与持久化

Pinia 在 `src/store/index.js` 装配：`createPinia()` + `pinia.use(createPersistedstate({ storage: localStorage }))`。**插件全局装了，但按 store 粒度 opt-in**——只有声明了 `persist` 配置的 store 才会持久化。

| store | 文件 | 职责 | 持久化方式 |
|-------|------|------|-----------|
| `useUserStore` | `store/user.js` | 登录态、token、用户信息 | ✅ 插件，键 `user-store` |
| `useNewsStore` | `store/modules/news.js` | 分类、新闻列表、详情、分页状态 | ❌ 每次进页面重新拉取 |
| `useFavoriteStore` | `store/modules/favorite.js` | 收藏列表 + 收藏状态 | 手动 `news_favorites` |
| `useHistoryStore` | `store/modules/history.js` | 浏览历史 | 手动 `news_history` |
| `useThemeStore` | `store/theme.js` | 主题配置与应用 | 手动 `theme` |
| `useLanguageStore` | `store/language.js` | 界面语言 | 手动 `language` |

**约定：store 放根层还是 modules/？** 会话与偏好（user/theme/language）放 `store/` 根层，业务数据（news/favorite/history）放 `store/modules/`。命名统一 `useXxxStore`。

**user store 的关键部分**（`store/user.js`）：

```js
state: () => ({ userInfo: null, token: '', isLogin: false, userBio: '这是我的个人简介' }),

// 持久化配置（pinia-plugin-persistedstate v4 写法）
persist: {
  key: 'user-store',
  storage: localStorage
}
```

actions：`login` / `register`（成功后自动存 token + userInfo + setAuthToken）、`logout`（清 state + 双清 token）、`getUserInfoDetail`（拉 `/api/user/info` 刷新 userInfo）、`updateUserBio`、`updatePassword`。

**action 返回值约定（全项目统一）**：不抛异常，返回 `{ success: boolean, message?: string, data?: any }`，调用方据此 toast。网络异常兜底为「网络请求失败，请稍后再试」类文案。

**news store 的分页机制**（`store/modules/news.js`）：

```js
const params = {
  categoryId: this.currentCategory,
  page: isRefresh ? 1 : Math.ceil(this.newsList.length / 10) + 1,  // 由已加载条数推算页码
  pageSize: 10
}
// 响应后：追加而不是覆盖；返回条数 < pageSize 则 finished = true（配合 van-list 停止加载）
```

`getCategories()` 成功后会在分类数组末尾追加 `{ id: 10, name: '更多' }` 入口项；接口失败时降级为一套内置的 7 个默认分类，保证页面不空白。

**favorite / history 的双轨模式**：每个操作都有两个方法——`addFavoriteApi(newsId)`（调后端，要求登录）与本地 `addFavorite(news)`（只动本地数组 + localStorage），由 `toggleFavorite()` 编排：先调 API，成功后再同步本地。未登录时 API 类 action 返回 `{ success: false, message: '请先登录' }`，查询类 action 回退本地状态并带 `isLocal: true` 标记。

---

## 9. 数据流转全景：一次打开详情的完整旅程

以「用户在首页点开一条新闻」为例，把所有层串起来：

```
NewsItem 点击
  → router.push('/news/detail/42')
  → 路由匹配 NewsDetail.vue（不 keepAlive，重新挂载）
  → onMounted：
      ① newsStore.getNewsDetail(42)
           → request.get('/api/news/detail?id=42')   [拦截器注入 Bearer]
           → 后端返回 {code:200, data:{id,title,content,relatedNews,...}}
           → this.newsDetail = response.data.data
      ② 已登录 → historyStore.addHistoryApi(42)        （服务端记录历史）
      ③ favoriteStore.loadFavorites()                   （本地收藏态兜底）
      ④ 已登录 → checkFavoriteStatusApi(42)             （服务端收藏态与本地对齐）
  → 模板里 newsStore.newsDetail.id 有值后渲染详情；isFavorite 计算属性驱动星标按钮
```

后端视角：详情接口的浏览量 +1 在**响应之后**由后端后台任务完成，所以前端拿到的 `views` 是本次浏览前的值——不要在页面上自己 +1。

---

## 10. 核心公共组件

`src/components/` 下只有三个，职责刻意保持单一：

| 组件 | 职责 | 关键 props / 逻辑 |
|------|------|-------------------|
| **TabBar.vue** | 底部导航（首页 / AI问答 / 我的） | `<van-tabbar route>` 路由模式；挂在每个主页面底部 |
| **NewsItem.vue** | 首页新闻条目（左文右图） | `props.news`；点击 `router.push('/news/detail/${id}')`；标题/摘要两行截断 |
| **NewsRecordList.vue** | 收藏列表与历史列表**共用**的记录列表 | `props.items / type('favorite'\|'history') / emptyText`；`emit('delete')` 交回父页面处理；按 type 决定时间标签文案与取 `favoriteTime` 还是 `viewTime` |

NewsRecordList 是"一个组件服务两个页面"的范本：差异点（时间字段、文案）全部通过 props 声明，删除动作只 emit 不实现——Favorite.vue 和 History.vue 各自决定删除前是否弹确认框、调用哪个 API。

---

## 11. 业务模块：新闻流 Home

`src/views/Home.vue` 是最复杂的页面，三层结构：顶部 `van-tabs` 分类栏 → 中间 `van-pull-refresh` + `van-list` 无限滚动 → 底部 TabBar。

```
van-tabs (v-model:active="activeTab", swipeable)
  └─ van-tab × displayCategories        ← 过滤掉"更多"项后的分类
       └─ van-pull-refresh (@refresh → newsStore.getNewsList(true))
            └─ van-list (@load → newsStore.getNewsList(), :finished)
                 └─ news-item × newsStore.newsList
```

三个联动逻辑：

1. **分类切换**：`watch(activeTab)` → `newsStore.changeCategory(categoryId)` → store 清空列表、重置 finished、以 `isRefresh=true` 拉第一页。
2. **分类页回跳**：Category.vue 点宫格后 `router.push({ path: '/home', query: { categoryId } })`；Home 里 `watch(() => route.query.categoryId, ..., { immediate: true })` 接住参数，定位到对应 Tab 并切换分类。
3. **分类名国际化**：Tab 标题不走 `category.name` 原文，而是经 `constants/categories.js` 的 `CATEGORY_NAME_KEY_MAP` 查 i18n key（第 14 章）。

`van-list` 的 `@load` 在滚动到底部自动触发，配合 store 的 `loading/finished` 状态实现无限加载；`onRefresh` 下拉时以 `isRefresh=true` 重置到第一页。

---

## 12. 业务模块：详情页与收藏历史的联动

**NewsDetail.vue**（第 9 章已讲数据流）的交互逻辑：

- **收藏按钮**：未登录 → toast + 跳 `/login`；已登录 → `favoriteStore.toggleFavorite(newsDetail)`，返回值三态：`true` 已收藏 / `false` 已取消 / `null` 操作失败，分别 toast 不同文案。
- **正文渲染**：后端存的是纯文本段落，`contentParagraphs` 计算属性按 `\n\n` 拆段渲染成 `<p>`，不引入富文本渲染器。
- **相关新闻**：直接用详情响应里的 `relatedNews` 数组渲染，点击跳同路由（`/news/detail/:id`）。

**收藏 / 历史页**（Favorite.vue / History.vue）结构对称：`onMounted` 里登录则调 `getFavoriteListApi()` / `getHistoryListApi()` 以服务端为准，未登录则 `loadFavorites()` / `loadHistory()` 读本地；删除走 `NewsRecordList` 的 `delete` 事件，先弹 `showDialog` 确认再调 API。

**本地历史的上限与去重**（`store/modules/history.js`）：`addHistory` 本地版会先移除同 id 旧记录再 `unshift`（最新在前），超过 50 条截断——这两个本地规则不依赖后端。

---

## 13. 业务模块：AI 问答 SSE 流式

`src/views/AIChat.vue` 是全项目唯一不走 axios 的请求，因为需要逐字渲染的 SSE 流，而 axios 不便处理流式响应：

```js
const response = await fetch(`${apiConfig.baseURL}${aiConfig.chatEndpoint}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json',
             'Authorization': `Bearer ${userStore.token}` },   // 手动带 token
  body: JSON.stringify({ message: userMessage, history })
});
```

**流解析的核心循环**：`response.body.getReader()` + `TextDecoder` 增量解码 → 按 `\n` 切行、剩余进 buffer → 只处理 `data: ` 开头的行 → `[DONE]` 表示结束 → 每个合法 JSON 取 `choices[0].delta.content` 追加到 `aiResponse` 并实时写入最后一条消息（打字机效果）。

几个值得注意的细节：

- **history 的裁剪**：发送前 `messages.value.slice(0, -2)` 排除当前用户消息和 AI 占位消息，只传历史轮次；后端再截取最近 10 条。
- **业务错误帧**：后端代理出错时返回 `data: {"error": "..."}`，前端解析到 `json.error` 就 `throw`，由外层 catch 把最后一条占位消息替换为错误文案。
- **XSS 防护**：AI 回复是 Markdown，经 `marked.parse()` 转 HTML 后**必须**过 `DOMPurify.sanitize()` 再 `v-html`——模型输出不可信，这个顺序不能反。
- **登录前置**：`sendMessage` 开头检查 `userStore.getLoginStatus`，未登录 toast 提示。
- 路由 `meta.keepAlive: true`，切到其他 Tab 再回来，对话记录还在。

---

## 14. 国际化与分类名映射

i18n 在 `src/i18n/index.js` 装配：`legacy: false`（组合式 API）、初始 locale 读 `localStorage('language')`、`fallbackLocale: 'zh-CN'`。语言包在 `locales/zh-CN.js` 与 `en-US.js`，顶层按键分组（共 12 组）：`common / nav / home / aiChat / newsDetail / login / register / favorite / history / my / settings / profile`。

组件里两种用法：

```html
<van-nav-bar :title="$t('home.title')" />          <!-- 模板里 -->
const { t } = useI18n();  t('history.confirmDelete')  <!-- 逻辑里（如 toast 文案） -->
```

**切语言**（Settings.vue）：`languageStore.setLanguage(value)` 写 localStorage（下次启动生效）+ `locale.value = value` 立即生效，两步缺一不可。

**分类名特殊处理**：后端分类表存的是中文（"头条"/"科技"...），直接展示无法翻译，所以有 `src/constants/categories.js`：

```js
export const CATEGORY_NAME_KEY_MAP = {
  '头条': 'headline', '社会': 'society', ..., '更多': 'more'
}
```

Home/Category 统一经 `getCategoryTranslation()` 查 `t('home.categories.' + key)`；**未收录的分类名原样展示**（英文环境下显示中文，可接受降级）。`categories.test.js` 的 3 个用例保证映射表与两份语言包始终一致——新增分类时三处要同步：语言包 ×2 + 映射表。

---

## 15. 主题系统：CSS 变量方案

`src/store/theme.js` 内置 4 套主题（light / dark / blue / green），每套 4 个颜色值。切换与初始化都走 `applyTheme()`：

```js
document.documentElement.style.setProperty('--background-color', theme.backgroundColor);
document.documentElement.style.setProperty('--text-color', theme.textColor);
document.documentElement.style.setProperty('--primary-color', theme.primaryColor);
document.documentElement.style.setProperty('--secondary-color', theme.secondaryColor);
```

任何组件想适配主题，样式里直接引用变量，如 Settings 页：`background-color: var(--background-color)`。注意现状：**只有 Settings 等少数页面接了变量**，多数页面仍写死浅色色值——新增页面建议直接用变量。主题名持久化在 localStorage(`theme`)，`main.js` 末尾 `initTheme()` 保证刷新后主题恢复。

---

## 16. 测试：vitest 的结构与写法

配置在 `vite.config.js` 的 `test` 字段：`environment: 'jsdom'`（提供 DOM/localStorage）、`globals: true`（describe/it 免导入也可，现有文件选择显式导入）。现有 4 个文件 16 例：

| 文件 | 覆盖 |
|------|------|
| `src/api/request.test.js`（5 例） | Bearer 注入、localStorage 回退、无 token 不带头、401 清理登录态 |
| `src/store/user.test.js`（6 例） | 登录成功 / 失败文案 / 网络异常兜底 |
| `src/components/NewsItem.test.js`（2 例） | 渲染与点击跳转 |
| `src/constants/categories.test.js`（3 例） | 分类映射与语言包的一致性 |

`request.test.js` 展示了本项目测 axios 的关键技巧——**自定义 adapter 捕获拦截器处理后的配置**：

```js
const makeAdapter = (status = 200, data = { code: 200 }) => {
  const captured = []
  const adapter = async (config) => {
    captured.push(config)          // 记录经过拦截器后的最终请求配置
    ...                            // 非 2xx 手动抛带 response 的错误，触发响应拦截器
  }
  return { adapter, captured }
}
// 断言：captured[0].headers.Authorization === 'Bearer token-abc'
```

写法约定：测 store 用 `createPinia()` + `setActivePinia()`；测组件用 `@vue/test-utils` 的 `mount`；涉及 localStorage 的用例记得 `beforeEach(() => localStorage.clear())`。跑法：`npm run test`（单次）/ `npm run test:watch`。

---

## 17. 开发约定与代码规范

**组件写法**

- 一律 `<script setup>` 组合式 API，不使用 Options API。
- 页面组件名 = 路由名单词（Home/Login/My...），ESLint 已关 `vue/multi-word-component-names`；公共组件用多词 PascalCase（NewsItem、TabBar）。
- Vant 函数式 API（`showToast`/`showDialog`）从 `'vant'` 直接导入，不走全局注册。

**数据与请求**

- 接口调用只写在 store action 里；view 不直接发请求（AIChat 的 fetch 除外）。
- action 返回 `{ success, message?, data? }`，不 throw；catch 里 `console.error` 是既定实践（ESLint `no-console` 已关）。
- 新增接口时对照 `docs/api-spec.md` 的参数 alias（camelCase）——前端传参/取字段以 spec 为准。

**文案与国际化**

- 用户可见文案一律走 `$t()` / `t()`，键进两份语言包**同步维护**；禁止模板里写死中文。
- 与后端数据值相关的翻译（如分类名）走 `constants/` 映射表模式。

**样式**

- 组件样式全部 `<style scoped>`；覆盖 Vant 内部类用 `:deep()` 选择器（见 Home.vue）。
- 新页面主题色优先用 `var(--primary-color)` 等变量。

**Lint / 格式 / 提交**

- `npm run lint` 必须零告警再提交；ESLint 管正确性，格式交给 Prettier（`npm run format`）。
- Prettier 约定：无分号、单引号、行宽 100、es5 逗号。历史文件风格不完全统一（部分带分号），改动时对所在文件现状从众即可，不必全量重排。
- ESLint 浏览器全局变量（window/localStorage/fetch 等）在 `eslint.config.js` 的 `globals` 白名单维护，用到新全局（如 `AbortController`）先去确认。

---

## 18. 调试与排错手册

| 症状 | 大概率原因 | 手段 |
|------|-----------|------|
| 页面能开但所有列表为空 | 后端没启动 / `VITE_API_BASE_URL` 指错 | 先确认 `http://127.0.0.1:8000/docs` 可访问；Network 面板看请求打到哪 |
| 控制台报 CORS 错误 | 后端非 DEBUG_MODE 且白名单没配 | 用后端开发模式，或改走 `/api-proxy` 代理 |
| 刷新后掉登录态 | `user-store` 键被清 / persist 失效 | Application 面板看 localStorage；确认登录成功响应里有 token |
| 某个 Vant 组件渲染成空白 | `main.js` 没注册该组件 | 去 main.js 补 `app.use(...)` |
| AI 问答一直转圈无回复 | 后端 AI 提供方不可用（Key 无效 / Ollama 未起） | 看后端终端日志 `app.ai` 的 warning；前端 Network 里看 SSE 帧内容 |
| 接口返回 401 | token 过期（7 天）或没带 | 重新登录；Network 确认请求头有 `Authorization: Bearer ...` |
| 接口返回 400 | 参数不符合后端校验（如密码 <6 位） | 响应 `data` 是字段级错误明细，直接看 message |
| 分类 Tab 标题显示中文原文 | 新分类没进 `CATEGORY_NAME_KEY_MAP` | 补映射 + 两份语言包（categories.test.js 会帮你查漏） |
| 改了代码页面没变 | Vite 热更新偶发失灵 | 硬刷新；重启 `npm run dev` |

调试心法：**打开 Vue Devtools 看 store 状态，打开 Network 面板看请求**——先分清"数据没拿到"还是"拿到了没渲染"，再决定往 store 还是组件里找。

---

## 19. 已知取舍与注意点

理解这些"有意为之或暂未做"的点，避免误改：

| 现状 | 为什么 | 改进方向 |
|------|--------|----------|
| 收藏/历史"本地 + API"双轨 | 游客也能收藏/留痕，登录后以服务端为准 | 保持现状；改收藏逻辑时两条路径都要动 |
| 没有路由级登录守卫 | 游客可浏览，写操作页面内拦截 | 若加全局守卫，注意游客浏览体验 |
| news store 不持久化 | 新闻是易变数据，每次进页面重拉 | —— |
| 列表分页页码由 `newsList.length / 10` 推算 | 简单可靠（pageSize 固定 10）；改 pageSize 需同步改这里 | 改为后端返回的 `hasMore` 驱动即可解耦 |
| `getNewsDetail` 用 `?id=${id}` 拼 URL，其余接口用 `params` | 历史写法，行为等价 | 顺手统一成 `{ params: { id } }` |
| Home 的 `watch(activeTab)` 读的是 `newsStore.categories[newVal].id` | "更多"项固定追加在末尾，前段索引恰好对齐 displayCategories | 若调整分类顺序逻辑，注意两数组索引语义 |
| AIChat 组件卸载不中断流 | 实现简单；离开页面后流在后台跑完 | 可加 AbortController（ESLint 白名单已备） |
| AI 的错误文案会留在 messages 里 | 简单直接 | 发送 history 前过滤掉错误占位消息 |
| 部分页面颜色写死浅色值 | 主题变量方案是后期引入的 | 新页面用 CSS 变量，旧页面渐进迁移 |

---

## 附录 A：上手自查清单

- [ ] `npm install` 后 `npm run dev` 能打开首页，后端连通（列表有数据）
- [ ] 注册 → 登录 → 刷新页面不掉登录态（localStorage 出现 `user-store`）
- [ ] 能说清一次请求经过哪几层：view → store action → request.js → 后端
- [ ] 能找到任意接口的前端实现位置（store action 里的字符串路径）
- [ ] 首页切换分类 / 下拉刷新 / 上拉加载的行为链路（第 11 章）
- [ ] 收藏按钮三态 toast 与双轨数据的关系（第 12 章）
- [ ] AIChat 的 SSE 解析循环与 DOMPurify 的位置（第 13 章）
- [ ] `npm run test` 16 例全绿；`npm run lint` 零告警
- [ ] 新增一个 Vant 组件时知道去 main.js 注册
- [ ] 新增文案时两份语言包同步添加

## 附录 B：localStorage 键速查

| 键 | 写入者 | 内容 |
|----|--------|------|
| `user-store` | pinia-plugin-persistedstate（仅 user store） | `{ userInfo, token, isLogin, userBio }` |
| `news_favorites` | favorite store 手动读写 | 本地收藏数组 |
| `news_history` | history store 手动读写 | 本地历史数组（最多 50 条） |
| `theme` | theme store | `'light' \| 'dark' \| 'blue' \| 'green'` |
| `language` | language store | `'zh-CN' \| 'en-US'` |

> 401 时 `request.js` 只清 `user-store`（登录态），其余键不受影响；"退出登录"在 `My.vue` 触发 user store 的 `logout()`。
