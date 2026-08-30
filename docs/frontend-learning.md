# 前端学习文档：从零理解「AI 头条新闻系统」前端

> **这份文档是写给谁的**：新加入项目的前端开发者。假设你了解 Vue 基础语法（组件、props、v-for、ref），但对本项目的目录组织、状态管理和业务流转还不熟悉。
>
> **这份文档能做什么**：带你按"请求从哪里发出、数据存在哪里、页面怎么渲染"的脉络，把 `frontend/` 目录完整过一遍。每一章都是：**为什么这样设计（概念）→ 本项目怎么做的（对照真实代码）→ 你上手要注意什么（要点）**。第 20–22 章是三篇动手演练：新增页面、对接接口、写组件测试，按步骤照做即可。
>
> **怎么用**：左手开这份文档，右手开编辑器里的 `frontend/` 目录，边读边对照。后端不是重点，接口的完整定义见 [api-spec.md](api-spec.md)，后端内部实现见 [backend-learning.md](backend-learning.md)。

---

## 目录

- [1. 项目是什么：前端在系统中的角色](#1-项目是什么前端在系统中的角色)
- [2. 技术栈地图：每个东西是干嘛的](#2-技术栈地图每个东西是干嘛的)
- [3. 环境搭建与第一次启动](#3-环境搭建与第一次启动)
- [4. 目录结构与分层职责](#4-目录结构与分层职责)
- [5. 应用装配：main.js 装配顺序](#5-应用装配mainjs-装配顺序)
- [6. 路由组织：路由表、keepAlive 与导航守卫](#6-路由组织路由表keepalive-与导航守卫)
- [7. 网络层：axios 封装与 Token 流转](#7-网络层axios-封装与-token-流转)
- [8. 后端响应契约：统一包络、字段别名与错误明细](#8-后端响应契约统一包络字段别名与错误明细)
- [9. 状态管理：六个 store 的分工与持久化](#9-状态管理六个-store-的分工与持久化)
- [10. store 逐个拆解：user / news / favorite / history / theme / language](#10-store-逐个拆解user--news--favorite--history--theme--language)
- [11. 数据流转全景：一次打开详情的完整旅程](#11-数据流转全景一次打开详情的完整旅程)
- [12. 核心公共组件](#12-核心公共组件)
- [13. 页面逐个讲：Home（新闻流）](#13-页面逐个讲home新闻流)
- [14. 页面逐个讲：NewsDetail（详情与收藏/历史联动）](#14-页面逐个讲newsdetail详情与收藏历史联动)
- [15. 页面逐个讲：AIChat（SSE 流式）](#15-页面逐个讲aichatsse-流式)
- [16. 页面逐个讲：Login / Register / My / Profile / Settings / Favorite / History](#16-页面逐个讲login--register--my--profile--settings--favorite--history)
- [17. 国际化与分类名映射](#17-国际化与分类名映射)
- [18. 主题系统：CSS 变量方案](#18-主题系统css-变量方案)
- [19. 测试：vitest 的结构与写法](#19-测试vitest-的结构与写法)
- [20. 动手演练 A：新增一个页面（端到端）](#20-动手演练-a新增一个页面端到端)
- [21. 动手演练 B：对接一个新接口](#21-动手演练-b对接一个新接口)
- [22. 动手演练 C：新增公共组件与单元测试](#22-动手演练-c新增公共组件与单元测试)
- [23. 开发约定与代码规范](#23-开发约定与代码规范)
- [24. 调试与排错手册](#24-调试与排错手册)
- [25. 已知取舍与注意点](#25-已知取舍与注意点)
- [附录 A：上手自查清单](#附录-a上手自查清单)
- [附录 B：localStorage 键速查](#附录-blocalstorage-键速查)
- [附录 C：Vant 组件注册清单](#附录-cvant-组件注册清单)

---

## 1. 项目是什么：前端在系统中的角色

这是"仿今日头条"新闻系统的**移动端 H5 前端**（Vue 3 单页应用），与 FastAPI 后端纯 HTTP + JSON 通信，不生成任何服务端页面。它提供 11 个页面：首页新闻流、分类、新闻详情、收藏、浏览历史、AI 问答、我的、登录、注册、个人信息、设置。

**一句话概括架构**：页面组件（views）只管"渲染 + 收集用户操作" → 数据全部存放在 Pinia store → store 的 action 调用统一的 axios 实例发请求 → 后端返回 `{code, message, data}` → action 把结果写回 state → 页面自动响应式更新。AI 问答是唯一的例外：它用原生 `fetch` 直连后端 SSE 流（第 15 章）。

**一个重要前提**：前端零密钥。AI 提供方（智谱/本地 Ollama）与 API Key 全部在后端 `.env` 配置，前端只调用后端代理接口 `/api/ai/chat`。

**代码体量参考**（改错地方之前先估量）：全部 `src/` 约 3100 行，其中 `views/` 约 2100 行、`store/` 约 500 行、公共组件约 280 行。最大单文件是 `AIChat.vue`（约 350 行，一半是样式）和 `NewsDetail.vue`（约 280 行）。任何"新功能"通常只涉及 3~4 个文件：一个 view、一个 store、一份语言包 ×2。

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
| **vitest 4 + @vue/test-utils + jsdom** | 单元测试 | 4 个测试文件 18 例，配置内嵌在 `vite.config.js` |
| **ESLint 10 + Prettier** | 代码检查 / 格式化 | ESLint 扁平配置管正确性，Prettier 管格式 |

**两个必须先建立的观念**：

1. **视图薄、store 厚**：views 里不直接写 `request.get(...)`（唯一例外是 AIChat 的 fetch），所有接口调用都封装在 store action 里。找一个接口的实现，先去 `store/` 找。
2. **双轨数据**：收藏和历史有"本地态"与"服务端态"两份（未登录也能用，登录后以服务端为准），代码里处处能看到 `xxxApi()` 与本地 `xxx()` 两个方法，不要混淆（第 10、14 章）。

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

**摆脱 CORS 依赖（可选）**：开发模式后端 CORS 全放开，直接连即可。若想走代理，把 `.env.local` 的 `VITE_API_BASE_URL` 改为 `/api-proxy`——`vite.config.js` 已配置该前缀转发到 `http://127.0.0.1:8000` 并重写去掉前缀：

```js
// vite.config.js
server: {
  proxy: {
    '/api-proxy': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api-proxy/, ''),
    },
  },
},
```

常用脚本（`package.json`）：

| 命令 | 作用 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` / `npm run preview` | 生产构建 / 本地预览构建产物 |
| `npm run test` | 跑 vitest 全部 18 例（`test:watch` 进入监听模式） |
| `npm run lint` / `lint:fix` | ESLint 检查 / 自动修复 |
| `npm run format` | Prettier 格式化 `src/` |

> 提交前至少跑 `npm run test` 和 `npm run lint`；改动涉及模板时建议加跑 `npm run build`（它能兜住 vitest 覆盖不到的模板编译错误）。

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
    │   ├── request.js        # axios 实例：baseURL、10s 超时、Bearer 注入、401 跳登录
    │   └── request.test.js   # 网络层单元测试（7 例）
    ├── config/
    │   └── api.js            # apiConfig.baseURL（读 VITE_API_BASE_URL）+ AI 端点常量
    ├── constants/
    │   ├── categories.js     # 后端中文分类名 → i18n key 的映射表
    │   └── categories.test.js
    ├── router/
    │   └── index.js          # 12 条路由 + beforeEach 设置页面标题
    ├── store/
    │   ├── index.js          # createPinia + persistedstate 插件
    │   ├── user.js           # 用户会话（唯一启用持久化的 store）
    │   ├── theme.js          # 主题（CSS 变量 + localStorage）
    │   ├── language.js       # 界面语言（localStorage）
    │   └── modules/          # 业务数据 store：news / favorite / history
    ├── i18n/
    │   ├── index.js          # i18n 单例（default 导出）+ 语言切换辅助
    │   └── locales/          # zh-CN.js / en-US.js 语言包（各 12 个分组）
    ├── components/           # 公共组件：TabBar / NewsItem / NewsRecordList
    └── views/                # 11 个页面组件（与路由一一对应）
```

**分层依赖方向**：`views → store → api/request → 后端`。公共组件（components）被 views 使用，不反向依赖任何 store。`constants/` 与 `config/` 是被任意层引用的纯常量。

**一个现状说明**：`vite.config.js` 配了 `@` → `src/` 的路径别名，但**现有代码一律使用相对路径**（如 `../../api/request`）。写新代码时保持相对路径习惯，与现有风格一致。

---

## 5. 应用装配：main.js 装配顺序

`src/main.js` 是唯一知道"全局有哪些东西"的文件，顺序有讲究：

```js
const app = createApp(App)

// 1. i18n：setupI18n() 返回 i18n/index.js 的模块级单例
const i18n = setupI18n()
app.use(i18n)

// 2. Vant 按需注册：用哪个注册哪个（完整清单见附录 C）
app.use(Button)
app.use(NavBar)
app.use(Tabbar)
// ...共 19 个组件

// 3. 路由与状态
app.use(router)
app.use(pinia)

app.mount('#app')

// 4. 主题初始化：必须在 pinia 安装之后（useThemeStore 依赖 pinia 实例）
const themeStore = useThemeStore()
themeStore.initTheme()
```

四个关键点：

1. **i18n 是模块级单例**：`src/i18n/index.js` 在模块加载时就 `createI18n` 并 default 导出（初始 locale 读 `localStorage('language')`），`setupI18n()` 只是返回同一实例。这样 `request.js` 这类非组件模块才能 `import i18n from '../i18n'` 后用 `i18n.global.t()` 取当前语言文案（第 7 章的 401 提示就是这么做的）。
2. **Vant 忘注册的后果**：模板里的 `<van-xxx>` 渲染为空且**不报错**——新页面想用一个没注册过的 Vant 组件，必须先去 `main.js` 补 `app.use(...)`。这是本项目最常见的新手坑（清单见附录 C）。
3. **Vant 样式只引一次**：`import 'vant/lib/index.css'`（全量样式，本项目不做按需样式）。
4. **主题初始化在 mount 之后**：把主题色写入 CSS 变量（第 18 章）。放在 mount 后是因为 `useThemeStore()` 需要 pinia 已安装。

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

## 6. 路由组织：路由表、keepAlive 与导航守卫

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

**keepAlive 的取舍**：`meta.keepAlive: true` 的页面切走再切回**不重新挂载**——`onMounted` 不会重跑，这就是首页 Tabs 滚动位置和 AI 对话记录能保留的原因；代价是数据刷新要自己做（Home 靠 `watch(route.query.categoryId)` 接住分类页回跳）。新增列表页时想清楚：要缓存就得自己处理刷新时机。

唯一的全局守卫只管标题：

```js
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '新闻资讯'
  next()
})
```

**本项目没有路由级登录守卫**。需要登录的操作在页面内检查（如 NewsDetail 点收藏、AIChat 发消息前查 `userStore.getLoginStatus`），未登录时 toast 提示并跳 `/login`；登录态过期由 axios 拦截器全局兜底跳转（第 7 章）。这是有意为之：游客可以浏览新闻，只在写操作时才要求登录。

**一个 Vue Router 通用陷阱（本项目已踩）**：同一路由记录只变参数（如 `/news/detail/42` → `/news/detail/45`）时**组件实例被复用**，`onMounted` 不会重跑。NewsDetail 目前没有监听参数变化，点击相关新闻时存在内容不刷新的问题（见第 25 章取舍表，修复方向是 `onBeforeRouteUpdate` 或 `watch(() => route.params.id)`）。

---

## 7. 网络层：axios 封装与 Token 流转

`src/api/request.js` 是所有 HTTP 请求（除 AIChat 的 fetch）的唯一出口，全文不到 70 行，值得完整读一遍：

```js
const request = axios.create({
  baseURL: apiConfig.baseURL,   // 来自 src/config/api.js，读 VITE_API_BASE_URL
  timeout: 10000,
})

// 模块内保存 token：登录后由 user store 调用 setAuthToken 注入
let authToken = null

export function setAuthToken(token) {
  authToken = token || null;
}

// 请求拦截器：统一携带 Bearer Token
request.interceptors.request.use((config) => {
  const token = authToken || readPersistedToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

三个关键机制：

1. **Token 注入（双来源）**：优先用模块内 `authToken`（登录后 `setAuthToken` 注入）；页面刷新后模块变量丢失，回退 `readPersistedToken()` 从 localStorage 的 `user-store` 键（user store 持久化）里解析。
2. **401 全局兜底**：响应拦截器发现 401 先**双清**登录态（模块变量 + localStorage），再按来源分流：

```js
const url = error.config?.url || '';
// 登录/注册接口自身的 401（如密码错误）由表单提示，不劫持跳转
const isAuthEndpoint = url.includes('/api/user/login') || url.includes('/api/user/register');
if (!isAuthEndpoint && router.currentRoute.value.path !== '/login') {
  showToast({ message: i18n.global.t('common.loginExpired'), position: 'bottom' });
  router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } });
}
```

   即：业务接口 401（token 过期）→ toast + 跳登录页并带上回跳参数；登录/注册接口自己的 401（密码错误）不劫持，仍由表单显示错误。`Login.vue` 登录成功后读取 `redirect` 回跳（只接受 `/` 开头的站内路径，防开放重定向）。
3. **baseURL 集中一处**：`src/config/api.js` 的 `apiConfig.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'`。改后端地址只动 `.env.local`。

**Token 的完整生命周期**：

```
登录成功 → user store: this.token = token; setAuthToken(token)
        → persist 插件把整个 state 写入 localStorage('user-store')
页面刷新 → 模块内 token 为 null → 拦截器回退 readPersistedToken()
401 响应 → 双清（模块变量 + localStorage）→ toast + 跳 /login?redirect=原页面 → 登录后回跳
退出登录 → logout() action 里同样双清
```

**接口路径写在 store action 里**（如 `request.get('/api/news/list', { params })`），本项目没有集中式的 `api/xxx.js` 接口定义层——对照 [api-spec.md](api-spec.md) 的路径即可找到实现位置。注意 AIChat 的 fetch 不经过这套拦截器，401 时它只会把后端错误文案显示在聊天气泡里（不走全局跳转）。

---

## 8. 后端响应契约：统一包络、字段别名与错误明细

**所有接口返回三键包络**，前端每个 action 都在解这层：

```json
{ "code": 200, "message": "success", "data": { } }
```

- **成功判定**：HTTP 状态码 200 **且** `response.data.code === 200`，两者都满足才算成功。action 里的标准写法：

```js
if (response.data && response.data.code === 200) {
  this.userInfo = response.data.data;   // 业务数据在 data 字段里
  return { success: true };
}
return { success: false, message: response.data.message || '兜底文案' };
```

- **字段别名（camelCase）**：后端 Pydantic schema 用 alias 输出驼峰，前端**只接触驼峰字段**：

| 数据库/内部字段 | 前端拿到的字段 |
|----------------|----------------|
| `publish_time` | `publishTime` |
| `category_id` | `categoryId` |
| `view_time` / `favorite_time` | `viewTime` / `favoriteTime` |
| `has_more` | `hasMore` |
| `user_info` / `created_at` | `userInfo` / `createdAt` |
| 路径/查询参数 `news_id` | 请求时传 `newsId` |

  对照 [api-spec.md](api-spec.md) 的参数表写代码，不要猜。

- **错误明细（400）**：参数校验失败时 `data` 不是 null，而是字段级数组，`message` 是第一条错误的人话翻译：

```json
{
  "code": 400,
  "message": "长度不足",
  "data": [{ "field": "password", "message": "长度不足" }]
}
```

  目前表单校验（Vant 的 `rules`）在提交前就拦住了大部分错误，所以前端暂时没有渲染这个明细数组；要做成字段级报错提示时从这里取。

- **401**：被 request.js 全局处理（第 7 章），store 只需处理自己 `catch` 里的部分。

---

## 9. 状态管理：六个 store 的分工与持久化

Pinia 在 `src/store/index.js` 装配：`createPinia()` + `pinia.use(createPersistedstate({ storage: localStorage }))`。**插件全局装了，但按 store 粒度 opt-in**——只有声明了 `persist` 配置的 store 才会持久化。

| store | 文件 | 职责 | 持久化方式 |
|-------|------|------|-----------|
| `useUserStore` | `store/user.js` | 登录态、token、用户信息 | ✅ 插件，键 `user-store` |
| `useNewsStore` | `store/modules/news.js` | 分类、新闻列表、详情、分页状态 | ❌ 每次进页面重新拉取 |
| `useFavoriteStore` | `store/modules/favorite.js` | 收藏列表 + 收藏状态 | 手动 `news_favorites` |
| `useHistoryStore` | `store/modules/history.js` | 浏览历史 | 手动 `news_history` |
| `useThemeStore` | `store/theme.js` | 主题配置与应用 | 手动 `theme` |
| `useLanguageStore` | `store/language.js` | 界面语言 | 手动 `language` |

**为什么 favorite/history 不用 persist 插件**：它们的本地数据有写入规则（去重、条数上限、时间戳格式化），需要走自己的 `save/load` 方法控制格式，所以手动读写 localStorage（第 10 章）。主题/语言只是单值字符串，手动存更直观。

**约定：store 放根层还是 modules/？** 会话与偏好（user/theme/language）放 `store/` 根层，业务数据（news/favorite/history）放 `store/modules/`。命名统一 `useXxxStore`。

**action 返回值约定（全项目统一，读代码前先记住）**：不抛异常，返回 `{ success: boolean, message?: string, data?: any }`，调用方据此 toast；网络异常兜底为「网络请求失败」类文案。查询类 action 在未登录时可能带 `isLocal: true` 标记（表示结果来自本地态）。

---

## 10. store 逐个拆解：user / news / favorite / history / theme / language

### 10.1 user store（`store/user.js`，约 225 行）

```js
state: () => ({ userInfo: null, token: '', isLogin: false, userBio: '这是我的个人简介' }),

// 持久化配置（pinia-plugin-persistedstate v4 写法）
persist: {
  key: 'user-store',
  storage: localStorage
}
```

| action | 行为 | 要点 |
|--------|------|------|
| `login(userData)` | POST `/api/user/login` | 成功后三连：写 `token/userInfo/isLogin` + `setAuthToken(token)`；失败返回后端 message |
| `register(userData)` | POST `/api/user/register` | 成功即自动登录（与 login 相同的三连），Register 页注册完无需再登录 |
| `logout()` | 纯本地 | 清 state + `setAuthToken(null)`；localStorage 由 persist 插件随 state 更新 |
| `getUserInfoDetail()` | GET `/api/user/info` | `if (!this.token) return { success: false }` 先挡未登录；成功刷新 `userInfo` |
| `updateUserBio(bio)` | PUT `/api/user/update` | 只更新 bio 一个字段；成功后同步本地 `this.userInfo.bio` |
| `updatePassword(old, new)` | PUT `/api/user/password` | 旧密码错误时后端返回 400，action 原样带回 message |

注意 `userBio` 这个 state 字段是**兜底文案**，真实简介在 `userInfo.bio`，getter `getUserBio` 做了合并：`state.userInfo?.bio || state.userBio`。

### 10.2 news store（`store/modules/news.js`）

```js
state: () => ({
  newsList: [], newsDetail: {}, categories: [], currentCategory: 1,
  loading: false, refreshing: false, finished: false, categoriesLoading: false
}),
```

**分页是核心机制**：页码由"已加载条数"反推，不单独维护 page 状态：

```js
const params = {
  categoryId: this.currentCategory,
  page: isRefresh ? 1 : Math.ceil(this.newsList.length / 10) + 1,  // 由已加载条数推算页码
  pageSize: 10
}
// 响应后：追加而不是覆盖；返回条数 < pageSize 则 finished = true（配合 van-list 停止加载）
if (newsData.length < params.pageSize) {
  this.finished = true;
}
```

- `getNewsList(isRefresh)`：刷新时清空列表重来；否则追加。**改 pageSize 必须同步改这里的除数**（取舍见第 25 章）。
- `getCategories()`：返回 `{ success }`（对齐 action 约定）；**失败不造假数据**——`categories` 置空，由 Home/Category 显示「加载失败 + 重试」空态。成功后若 `currentCategory` 还是初始值 1 则设为第一个分类的 id。
- `changeCategory(categoryId)`：分类切换的统一入口——清列表、重置 finished、以刷新模式拉第一页。Home 的 Tab 切换和 Category 宫格点击都走它。
- `getNewsDetail(id)`：写入 `newsDetail`；后端的浏览量 +1 是响应后异步执行的，所以拿到的 `views` 是浏览前的值，**前端不要自己 +1**。
- `getCategoryName(categoryId)`：id → 中文名，给需要展示分类名的地方用。

### 10.3 favorite store（`store/modules/favorite.js`）——双轨模式的范本

每个操作都有两个方法：`xxxApi()`（调后端，要求登录，先查 `userStore.getLoginStatus`）与本地 `xxx()`（只动本地数组 + localStorage），由一个编排方法串联：

```js
async toggleFavorite(news) {
  if (this.isFavorite(news.id)) {
    const result = await this.removeFavoriteApi(news.id);   // 先调服务端
    if (result.success) {
      this.removeFavorite(news.id);                          // 成功再同步本地
      return false;                                          // false = 已取消收藏
    }
    return null;                                             // null = 操作失败
  }
  const result = await this.addFavoriteApi(news.id);
  if (result.success) {
    this.addFavorite(news);                                  // 本地条目带 favoriteTime: new Date().toLocaleString()
    return true;                                             // true = 已收藏
  }
  return null;
}
```

**返回值三态**：`true` 已收藏 / `false` 已取消 / `null` 失败——NewsDetail 靠它 toast 不同文案。

其他要点：

- `isFavorite(id)` getter：`state.favorites.some(item => item.id === id)`，详情页星标按钮由它驱动。
- `checkFavoriteStatusApi(newsId)`：未登录时**不报错**，回退本地状态并带 `isLocal: true`；登录时以服务端为准。
- 本地持久化 `saveFavorites()/loadFavorites()`：键 `news_favorites`，JSON 全量读写。
- 注意：`toggleFavorite` 的未登录场景不会走到 API 分支——页面层（NewsDetail）在调用前已拦截未登录并跳登录页。

### 10.4 history store（`store/modules/history.js`）

与 favorite 同构，但多两条本地规则：

```js
addHistory(news) {
  const existingIndex = this.history.findIndex(item => item.id === news.id);
  if (existingIndex !== -1) {
    this.history.splice(existingIndex, 1);   // 去重：先删旧记录
  }
  this.history.unshift({ ...news, viewTime: new Date().toLocaleString() });  // 最新在前
  if (this.history.length > 50) {
    this.history.pop();                       // 上限 50 条
  }
  this.saveHistory();
}
```

API 侧：`addHistoryApi/removeHistoryApi/clearHistoryApi/getHistoryListApi`。其中 `removeHistoryApi` 与 `clearHistoryApi` 在未登录时直接执行本地操作并返回 `{ success: true, isLocal: true }`（收藏模块的同类方法则是返回失败）——两个模块的未登录语义有意不同：历史可以纯本地用，收藏列表页要求登录后才有服务端数据。

### 10.5 theme store（`store/theme.js`）

内置 4 套主题（light/dark/blue/green），每套 4 个颜色。`applyTheme()` 把当前主题写进 CSS 变量：

```js
applyTheme() {
  const theme = this.themes[this.currentTheme];
  document.documentElement.style.setProperty('--background-color', theme.backgroundColor);
  document.documentElement.style.setProperty('--text-color', theme.textColor);
  document.documentElement.style.setProperty('--primary-color', theme.primaryColor);
  document.documentElement.style.setProperty('--secondary-color', theme.secondaryColor);
}
```

`setTheme(name)` = 改 state + 写 localStorage(`theme`) + `applyTheme()`；`initTheme()` 只做 applyTheme（main.js 挂载后调用，刷新恢复主题）。

### 10.6 language store（`store/language.js`）

只管 `currentLanguage` 的存取（localStorage `language`）。**注意它不负责切换 vue-i18n 的 locale**——Settings 页是"两步走"：`languageStore.setLanguage(v)`（持久化，下次启动生效）+ `locale.value = v`（让当前页面立即生效），见第 16 章。

---

## 11. 数据流转全景：一次打开详情的完整旅程

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

两个容易踩的观察点：

- ④ 做的是"双轨对齐"：服务端说已收藏而本地没有 → 补进本地；服务端说没收藏而本地有 → 从本地移除。返回值里的 `isLocal: true` 表示这次结果是本地兜底，不要拿它覆盖本地。
- 后端视角：详情接口的浏览量 +1 在**响应之后**由后端后台任务完成，所以前端拿到的 `views` 是本次浏览前的值。

---

## 12. 核心公共组件

`src/components/` 下只有三个，职责刻意保持单一：

| 组件 | 职责 | 关键 props / 逻辑 |
|------|------|-------------------|
| **TabBar.vue** | 底部导航（首页 / AI问答 / 我的） | `<van-tabbar route>` 路由模式；挂在每个主页面底部 |
| **NewsItem.vue** | 首页新闻条目（左文右图） | `props.news`；点击 `router.push('/news/detail/${id}')`；标题/摘要两行截断 |
| **NewsRecordList.vue** | 收藏列表与历史列表**共用**的记录列表 | `props.items / type('favorite'\|'history') / emptyText`；`emit('delete')` 交回父页面处理 |

NewsItem 全文很短，是"哑组件"的范本——只收 props、只管跳转，不发请求：

```html
<div class="news-item" @click="goToDetail">
  <div class="news-content">
    <h3 class="news-title">{{ news.title }}</h3>
    <p class="news-desc">{{ news.description }}</p>
    <div class="news-info">
      <span>{{ news.author }}</span>
      <span>{{ news.publishTime }}</span>
      <span>{{ news.views }} 阅读</span>
    </div>
  </div>
  <div class="news-image">
    <img :src="news.image" :alt="news.title">
  </div>
</div>
```

NewsRecordList 是"一个组件服务两个页面"的范本：差异点全部通过 props 声明，组件内部不写死业务：

```js
const props = defineProps({
  items: { type: Array, default: () => [] },
  // 'favorite' | 'history'，决定时间标签文案与删除语义
  type: {
    type: String,
    default: 'history',
    validator: (value) => ['favorite', 'history'].includes(value)
  },
  emptyText: { type: String, default: '' }
});

// 按 type 决定时间标签与取哪个时间字段
const timeLabel = computed(() =>
  props.type === 'favorite' ? t('favorite.timeLabel') : t('history.timeLabel')
);
const itemTime = (item) =>
  props.type === 'favorite' ? item.favoriteTime : item.viewTime;
```

删除动作只 `emit('delete', item)` 不实现——Favorite.vue 和 History.vue 各自决定删除前是否弹确认框、调用哪个 API（两个页面的确认框文案分别走 `favorite.confirmDelete` / `history.confirmDelete`）。

---

## 13. 页面逐个讲：Home（新闻流）

`src/views/Home.vue` 是最复杂的页面，三层结构：顶部 `van-tabs` 分类栏 → 中间 `van-pull-refresh` + `van-list` 无限滚动 → 底部 TabBar：

```
van-tabs (v-model:active="activeTab", swipeable)
  └─ van-tab × newsStore.categories     ← 分类为空时显示"加载失败 + 重试"空态
       └─ van-pull-refresh (@refresh → newsStore.getNewsList(true))
            └─ van-list (@load → newsStore.getNewsList(), :finished)
                 └─ news-item × newsStore.newsList
```

分类加载失败时的空态（数据诚实，不再造假分类）：

```html
<van-empty
  v-if="!newsStore.categories.length && !newsStore.categoriesLoading"
  :description="$t('common.loadFailed')"
>
  <van-button round type="primary" class="retry-button" @click="loadCategories">
    {{ $t('common.retry') }}
  </van-button>
</van-empty>
```

```js
// 加载分类，成功后再拉取列表；失败时页面显示重试空态
const loadCategories = () => {
  newsStore.getCategories().then((result) => {
    if (result?.success) {
      newsStore.getNewsList(true)
    }
  })
}
```

三个联动逻辑：

1. **分类切换**：`watch(activeTab)` → 按 Tab 索引从 `newsStore.categories[newVal]` 取 id → `newsStore.changeCategory(categoryId)`。模板直接遍历 `newsStore.categories`（历史上的"更多"占位条目已移除，Tab 与数组一一对应，索引语义简单）。
2. **分类页回跳**：Category.vue 点宫格后 `router.push({ path: '/home', query: { categoryId } })`；Home 里接住参数：

```js
watch(
  () => route.query.categoryId,
  (newCategoryId) => {
    if (newCategoryId) {
      const categoryId = parseInt(newCategoryId)
      const index = newsStore.categories.findIndex(cat => cat.id === categoryId)
      if (index !== -1) {
        activeTab.value = index        // 定位到对应 Tab
        newsStore.changeCategory(categoryId)
      }
    }
  },
  { immediate: true }                  // 首次挂载也检查（keepAlive 回来不触发 onMounted）
)
```

3. **分类名国际化**：Tab 标题不走 `category.name` 原文，而是经 `CATEGORY_NAME_KEY_MAP` 查 i18n key（第 17 章）。

`van-list` 的 `@load` 在滚动到底部自动触发，配合 store 的 `loading/finished` 状态实现无限加载；下拉刷新以 `isRefresh=true` 重置到第一页。右上角固定的"更多"按钮（`more-options` div）跳转 `/category`，它的 `top` 用 `v-bind('tabsTop + "px"')` 跟随分类栏位置——CSS 里用 JS 计算值的小技巧，值得一看。

---

## 14. 页面逐个讲：NewsDetail（详情与收藏/历史联动）

**挂载时的完整时序**（`NewsDetail.vue` 的 `onMounted`，注释即流程）：

```js
onMounted(async () => {
  await newsStore.getNewsDetail(newsId.value)   // ① 拉详情

  if (newsStore.newsDetail.id) {
    if (userStore.getLoginStatus) {
      try {
        await historyStore.addHistoryApi(newsStore.newsDetail.id)  // ② 服务端记历史
      } catch (error) { console.error('记录浏览历史API失败:', error) }
    }
  }

  favoriteStore.loadFavorites()                 // ③ 本地收藏态兜底

  if (userStore.getLoginStatus && newsStore.newsDetail.id) {   // ④ 服务端收藏态对齐
    const result = await favoriteStore.checkFavoriteStatusApi(newsStore.newsDetail.id)
    if (result.success && !result.isLocal) {
      if (result.isFavorite && !favoriteStore.isFavorite(newsStore.newsDetail.id)) {
        favoriteStore.addFavorite(newsStore.newsDetail)
      } else if (!result.isFavorite && favoriteStore.isFavorite(newsStore.newsDetail.id)) {
        favoriteStore.removeFavorite(newsStore.newsDetail.id)
      }
    }
  }
})
```

**收藏按钮的三态 toast**：

```js
const status = await favoriteStore.toggleFavorite(newsStore.newsDetail)
if (status === true)       showToast({ message: t('newsDetail.addedToFavorites'), position: 'bottom' })
else if (status === false) showToast({ message: t('newsDetail.removedFromFavorites'), position: 'bottom' })
else                       showToast({ message: t('newsDetail.operationFailed'), position: 'bottom' })
```

其余要点：

- **正文渲染**：后端存的是纯文本段落，`contentParagraphs` 计算属性按 `\n\n` 拆段渲染成 `<p>`，不引入富文本渲染器。
- **相关新闻**：用详情响应里的 `relatedNews` 数组渲染，点击 `router.push('/news/detail/${id}')`——注意第 6 章说的组件复用陷阱，这里跳转后 `onMounted` 不会重跑（第 25 章）。
- **星标按钮**：`:icon="isFavorite ? 'star' : 'star-o'"`，`isFavorite` 来自 favorite store 的 getter。
- 挂载完成前有个空态：`newsDetail.id` 没值时显示 `van-empty`（loading 文案）。

---

## 15. 页面逐个讲：AIChat（SSE 流式）

`src/views/AIChat.vue` 是全项目唯一不走 axios 的请求，因为需要逐字渲染的 SSE 流。请求发起（含停止生成的 signal）：

```js
abortController = new AbortController();
const response = await fetch(`${apiConfig.baseURL}${aiConfig.chatEndpoint}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json',
             'Authorization': `Bearer ${userStore.token}` },   // 手动带 token
  body: JSON.stringify({ message: userMessage, history }),
  signal: abortController.signal
});
```

**流解析的核心循环**：`response.body.getReader()` + `TextDecoder` 增量解码 → 按 `\n` 切行、剩余进 buffer → 只处理 `data: ` 开头的行 → `[DONE]` 表示结束 → 每个合法 JSON 取 `choices[0].delta.content` 追加并实时写入最后一条消息（打字机效果）：

```js
buffer += decoder.decode(value, { stream: true });
const lines = buffer.split('\n');
buffer = lines.pop() || '';              // 半截行留到下一轮

for (const line of lines) {
  if (!line.startsWith('data: ')) continue;
  const data = line.slice(6);
  if (data === '[DONE]') continue;
  const json = JSON.parse(data);         // SyntaxError 被捕获跳过，不中断流
  if (json.error) { throw new Error(json.error); }   // 后端业务错误帧
  const content = json.choices?.[0]?.delta?.content || '';
  if (content) {
    aiResponse += content;
    messages.value[messages.value.length - 1].content = aiResponse;  // 打字机
  }
}
```

**停止生成（用户点「停止」或离开页面）**：

- 模板上生成中「发送」按钮切换为「停止」：`@click="isLoading ? stopGeneration() : sendMessage()"`。
- `stopGeneration()` 执行 `abortController.abort()`；`onBeforeUnmount` 也调用它（页面刷新/关闭兜底）。
- `AbortError` 不当错误展示——占位消息还没有内容时直接移除，已生成的部分内容保留：

```js
} catch (error) {
  if (error?.name === 'AbortError') {
    const last = messages.value[messages.value.length - 1];
    if (last && last.role === 'assistant' && last.content === '') {
      messages.value.pop();              // 一个字都没生成就移除占位
    }
  } else {
    /* 其他错误：最后一条占位替换为错误文案 */
  }
} finally {
  abortController = null;
  isLoading.value = false;
}
```

其他值得注意的细节：

- **history 的裁剪**：发送前 `messages.value.slice(0, -2)` 排除当前用户消息和 AI 占位消息，只传历史轮次；后端再截取最近 10 条。
- **XSS 防护**：AI 回复是 Markdown，经 `marked.parse()` 转 HTML 后**必须**过 `DOMPurify.sanitize()` 再 `v-html`——模型输出不可信，这个顺序不能反：

```js
const formatMessage = (content) => {
  if (!content) return '';
  return DOMPurify.sanitize(marked.parse(content));
};
```

- **登录前置**：`sendMessage` 开头检查 `userStore.getLoginStatus`，未登录 toast 提示。
- 路由 `meta.keepAlive: true`，切到其他 Tab 再回来，对话记录还在。
- 自动滚动：`watch(messages, () => nextTick(scrollToBottom), { deep: true })`。

---

## 16. 页面逐个讲：Login / Register / My / Profile / Settings / Favorite / History

### Login.vue

- `van-form` + `van-field` 的 `rules` 做非空校验（用户名/密码必填），`@submit` 触发 `onSubmit`。
- 提交时先 `showToast({ type: 'loading', forbidClick: true, duration: 0 })` 防重复点击（注册页同款模式）。
- 成功后**按 redirect 回跳**（401 被登出时带来的参数）：

```js
const redirect = route.query.redirect;
router.push(typeof redirect === 'string' && redirect.startsWith('/') ? redirect : '/');
```

### Register.vue

- 比登录多一个确认密码字段，用自定义 `validator` 做一致性校验：

```js
:rules="[
  { required: true, message: $t('register.confirmPasswordRequired') },
  { validator: validatePassword, message: $t('register.passwordMismatch') }
]"
```

- 成功后 `router.push('/')`——user store 的 `register` action 成功即自动登录（写 token + userInfo），无需再登录。
- 注意：前端只校验非空和一致性；用户名 4~20 位字母/数字/下划线、密码 6~32 位的**强校验在后端**（400 返回字段明细，见第 8 章），前端展示后端 message。

### My.vue

- 登录态分流：已登录显示用户卡（点击进 `/profile`），未登录显示"去登录/去注册"按钮。
- 菜单 cell 里**收藏/历史有登录检查**（未登录 toast + 跳登录），设置/主题无。
- 退出登录：`showDialog` 确认 → `userStore.logout()` → 跳 `/login`：

```js
showDialog({ title: t('common.confirm'), message: t('my.logout') + '?', showCancelButton: true })
  .then((action) => {
    if (action === 'confirm') {
      userStore.logout();
      router.push('/login');
    }
  }).catch(() => {});
```

- `onMounted` 调 `userStore.getUserInfoDetail()` 刷新用户信息（keepAlive 页面，只在首次挂载拉一次）。
- "通知"菜单 cell 没绑点击事件，是占位。

### Profile.vue

- `onMounted` 先查登录态：未登录直接 `router.push('/login')`；已登录 loading toast + `getUserInfoDetail()` 刷新。
- 头像是写死的 Vant 猫图（`@vant/assets/cat.jpeg`），账号 ID 显示 `ID: heima-${token前5位}`——展示用的小把戏，不是真实业务字段。
- **编辑简介**用 `h()` 渲染函数在 showDialog 里画了一个 textarea（`showBioDialog`）——本项目唯一一处 render function 写法：

```js
showDialog({
  title: t('profile.editBio'),
  message: h('div', [ /* ... */, h('textarea', {
    value: newBioValue.value,
    onInput: (e) => { newBioValue.value = e.target.value },
  }) ])
}).then(async () => { /* 确认 → userStore.updateUserBio(newBioValue.value) */ })
```

- **修改密码**同样用 `h()` 在弹窗里画三个 input（旧密码/新密码/确认），确认后校验非空与一致性，再 `userStore.updatePassword(...)`。改密成功后本项目未做强制重新登录。

### Settings.vue

- 主题：`van-popup` 底部弹出主题列表（来自 `themeStore.getAllThemes`），点击 `themeStore.setTheme(id)` 立即生效。
- 语言：`van-radio-group` 选择，点确认后**两步走**：

```js
const changeLanguage = () => {
  languageStore.setLanguage(currentLanguage.value);   // ① 持久化（下次启动生效）
  locale.value = currentLanguage.value;               // ② 当前页面立即切换
  showToast(t('settings.languageChanged'));
};
```

- "隐私/通知/关于"三个 cell 无点击事件，是占位。
- 样式里用了主题 CSS 变量（`var(--background-color)`），是变量方案应用最完整的页面。

### Favorite.vue

- `onMounted` 调 `getFavoriteListApi()` 以服务端为准；**注意与 History 的不一致**：本页 API 失败时回退本地的代码被注释掉了（`// favoriteStore.loadFavorites()`），所以**游客打开收藏页会看到空列表**（哪怕本地有收藏）——已知取舍，见第 25 章。
- 删除单条：确认框 → `removeFavoriteApi(id)` 成功后 `removeFavorite(id)` 同步本地。
- 清空：导航栏右侧"清空"→ 确认框 → `clearFavoritesApi()`（内部会同步清本地）。

### History.vue

- 与 Favorite 结构对称（共用 NewsRecordList），但 `onMounted` 的回退是**启用的**：API 失败或未登录 → `historyStore.loadHistory()` 读本地——所以游客能正常看到自己的本地浏览历史。对照 Favorite 的注释状态，改这两个页面时注意保持各自的语义。
- 删除/清空失败且非本地操作时弹 `showDialog` 错误提示。

---

## 17. 国际化与分类名映射

i18n 实例在 `src/i18n/index.js` **模块级创建并 default 导出**（单例）：`legacy: false`（组合式 API）、初始 locale 读 `localStorage('language')`、`fallbackLocale: 'zh-CN'`。语言包在 `locales/zh-CN.js` 与 `en-US.js`，顶层按键分组（共 12 组）：`common / nav / home / aiChat / newsDetail / login / register / favorite / history / my / settings / profile`。

组件里两种用法：

```html
<van-nav-bar :title="$t('home.title')" />          <!-- 模板里 -->
const { t } = useI18n();  t('history.confirmDelete')  <!-- 逻辑里（如 toast 文案） -->
```

带参数的插值（详情页阅读数）：`$t('newsDetail.views', { n: newsStore.newsDetail.views })`，语言包里对应 `'阅读量 {n}'` 形式。

**切语言**（Settings.vue）：`languageStore.setLanguage(value)` 写 localStorage（下次启动生效）+ `locale.value = value` 立即生效，两步缺一不可（第 16 章）。

**分类名特殊处理**：后端分类表存的是中文（"头条"/"科技"...），直接展示无法翻译，所以有 `src/constants/categories.js`：

```js
// 后端返回的中文分类名 → i18n key（home.categories.*）
export const CATEGORY_NAME_KEY_MAP = {
  '头条': 'headline',
  '社会': 'society',
  // ...共 10 个
  '更多': 'more'
}
```

Home/Category 统一经 `getCategoryTranslation()` 查 `t('home.categories.' + key)`；**未收录的分类名原样展示**（英文环境下显示中文，可接受降级）。`categories.test.js` 的 3 个用例保证映射表与两份语言包始终一致——新增分类时三处要同步：语言包 ×2 + 映射表。

---

## 18. 主题系统：CSS 变量方案

theme store 的 `applyTheme()` 把 4 个颜色写进 `document.documentElement` 的 CSS 变量（第 10.5 节）。任何组件想适配主题，样式里直接引用变量：

```css
/* Settings.vue —— 变量方案应用最完整的页面 */
.settings-container {
  min-height: 100vh;
  background-color: var(--background-color);
  color: var(--text-color);
}
/* My.vue 的用户卡还用了 --primary-color */
```

可用变量：`--background-color` / `--text-color` / `--primary-color` / `--secondary-color`（随 light/dark/blue/green 四套主题切换）。

注意现状：**只有 My、Settings 等少数页面接了变量**，多数页面仍写死浅色色值（如 `background-color: #f7f8fa`）——深色主题下这些页面不会变。新增页面建议直接用变量，旧页面渐进迁移（第 25 章）。

---

## 19. 测试：vitest 的结构与写法

配置在 `vite.config.js` 的 `test` 字段：`environment: 'jsdom'`（提供 DOM/localStorage）、`globals: true`。现有 4 个文件 18 例：

| 文件 | 覆盖 |
|------|------|
| `src/api/request.test.js`（7 例） | Bearer 注入、localStorage 回退、无 token 不带头、401 清登录态并跳登录页（带 redirect）、登录接口 401 不劫持、非 401 不清态 |
| `src/store/user.test.js`（6 例） | 登录成功/业务失败/网络异常、注册自动登录、登出清态、未登录不发请求 |
| `src/components/NewsItem.test.js`（2 例） | 渲染与点击跳转 |
| `src/constants/categories.test.js`（3 例） | 分类映射与两份语言包的一致性 |

三种测试模式，各记住一个代表：

**模式一：mock 整个请求模块测 store**（`user.test.js`）。关键技巧是 `vi.hoisted`——mock 函数要提升到 `vi.mock` 工厂可用之前定义：

```js
const { mockRequest, mockSetAuthToken } = vi.hoisted(() => ({
  mockRequest: { post: vi.fn(), get: vi.fn(), put: vi.fn() },
  mockSetAuthToken: vi.fn(),
}))

vi.mock('../api/request', () => ({
  default: mockRequest,
  setAuthToken: mockSetAuthToken,
}))

// 用例内指定返回值，再断言 store 状态与调用参数
mockRequest.post.mockResolvedValueOnce(successBody)
const result = await store.login({ username: 'tester', password: 'secret' })
expect(mockSetAuthToken).toHaveBeenCalledWith('token-1')
```

**模式二：自定义 axios adapter 测拦截器**（`request.test.js`）。不 mock axios，而是传自定义 adapter 捕获拦截器处理后的最终请求配置：

```js
const makeAdapter = (status = 200, data = { code: 200 }) => {
  const captured = []
  const adapter = async (config) => {
    captured.push(config)          // 记录经过拦截器后的最终配置
    if (status >= 200 && status < 300) return response
    const error = new Error(`Request failed with status code ${status}`)
    error.response = response      // 非 2xx 手动抛错，触发响应拦截器
    throw error
  }
  return { adapter, captured }
}
// 断言：captured[0].headers.Authorization === 'Bearer token-abc'
```

该文件还有三个值得学的细节：`vi.mock('vant', () => ({ showToast: vi.fn() }))`（单测不真渲染 toast）；`beforeEach` 里 `await router.push('/')` 重置路由（401 跳转用例会真实导航，用例间要隔离）；异步导航断言用 `vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))`（router.push 是异步懒加载，单次 await 等不到）。

**模式三：mount 组件测渲染与交互**（`NewsItem.test.js`）。mock 掉 `useRouter` 即可测"点击跳转"：

```js
const pushSpy = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push: pushSpy }) }))

const wrapper = mount(NewsItem, { props: { news } })
await wrapper.find('.news-item').trigger('click')
expect(pushSpy).toHaveBeenCalledWith('/news/detail/7')
```

`categories.test.js` 则展示"一致性守卫"思路：遍历映射表断言每个 key 在两份语言包里都存在——语言包加键漏了另一份语言时测试直接红。

写法约定：测 store 用 `createPinia()` + `setActivePinia()`；涉及 localStorage 的用例 `beforeEach(() => localStorage.clear())`。跑法：`npm run test`（单次）/ `npm run test:watch`。

---

## 20. 动手演练 A：新增一个页面（端到端）

以新增一个"关于我们"页（路由 `/about`）为例，走完一遍所有触点：

1. **建组件** `src/views/About.vue`：

```html
<template>
  <div class="about-page">
    <van-nav-bar :title="$t('about.title')" left-arrow @click-left="router.back()" fixed />
    <van-cell-group inset>
      <van-cell title="Version" value="0.0.0" />
    </van-cell-group>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.about-page { padding-top: 46px; }
</style>
```

2. **注册路由**（`router/index.js` 的 routes 数组）：

```js
{
  path: '/about',
  name: 'About',
  component: () => import('../views/About.vue'),
  meta: { title: '关于', keepAlive: false }
}
```

3. **加语言包键**：`zh-CN.js` 和 `en-US.js` 各加一个顶层分组 `about: { title: '关于我们' }`（**两份都要加**；`categories.test.js` 只守分类键，其他键靠自觉）。
4. **加入口**：从 My.vue 菜单加一个 `<van-cell :title="$t('about.title')" is-link @click="router.push('/about')" />`（或挂 TabBar，视页面层级）。
5. **检查 Vant 注册**：本页用到的 `van-nav-bar / van-cell-group / van-cell` 已注册；若用了新组件（如 `van-collapse`），去 `main.js` 补 `app.use(Collapse)`。
6. **验证**：`npm run dev` 手点一遍 → `npm run lint` → `npm run test`（确认没破坏存量）。

## 21. 动手演练 B：对接一个新接口

假设后端新增了 `GET /api/news/search?keyword=x&page=1`。前端只动 store + 页面：

1. **对照 api-spec.md** 确认参数 alias（`keyword`、`page`、`pageSize`）与响应字段（驼峰）。
2. **在对应 store 加 action**（搜索属于新闻域 → `store/modules/news.js`）：

```js
async searchNews(keyword, page = 1) {
  try {
    const response = await request.get('/api/news/search', {
      params: { keyword, page, pageSize: 10 }
    });
    if (response.data && response.data.code === 200) {
      return { success: true, data: response.data.data };
    }
    return { success: false, message: response.data.message || '搜索失败' };
  } catch (error) {
    console.error('搜索失败:', error);
    return { success: false, message: '网络请求失败' };
  }
}
```

   对齐三条项目约定：**请求只写在 action 里**、**返回 `{success, message?, data?}` 不 throw**、**catch 里 `console.error`**。
3. **页面调用**：

```js
const res = await newsStore.searchNews(kw)
if (res.success) { /* 渲染 res.data.list */ } else { showToast(res.message) }
```

4. **需要新 store 吗**？只有跨页面共享的新数据域才建 `store/modules/search.js`（照 favorite.js 的结构抄），单页面临时状态用组件内 `ref` 即可。
5. **补测试**：在对应测试文件 mock `../api/request`（照抄 `user.test.js` 的 `vi.hoisted` 模式），至少覆盖成功与失败两分支。

## 22. 动手演练 C：新增公共组件与单元测试

以一个"列表空态组件"为例：

1. **设计 props/emits 先于写模板**：参考 NewsRecordList 的模式——差异点全走 props（`description`、`retryable`），动作只 emit 不实现。放在 `src/components/`，多词 PascalCase 命名。
2. **组件内不引 store**：数据由父页面传进来，保持可复用与可测试（公共组件依赖 store 会让测试必须搭 pinia）。
3. **测试照抄 NewsItem.test.js 的骨架**：

```js
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

// 组件里用了 useI18n / useRouter 就 mock 掉
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (k) => k }) }))

import EmptyState from './EmptyState.vue'

it('渲染描述文案', () => {
  const wrapper = mount(EmptyState, { props: { description: '加载失败' } })
  expect(wrapper.text()).toContain('加载失败')
})

it('点击重试按钮触发 retry 事件', async () => {
  const wrapper = mount(EmptyState, { props: { description: 'x', retryable: true } })
  await wrapper.find('button').trigger('click')
  expect(wrapper.emitted('retry')).toHaveLength(1)
})
```

4. **跑 `npm run test`**——新用例必须过，且存量 18 例不能红。
5. **判断要不要测 i18n 文案**：组件文案若走了 `$t`，mock 掉 `useI18n` 后断言的是 key 而非文案，键的真实性由语言包自查保证。

---

## 23. 开发约定与代码规范

**组件写法**

- 一律 `<script setup>` 组合式 API，不使用 Options API。
- 页面组件名 = 路由名单词（Home/Login/My...），ESLint 已关 `vue/multi-word-component-names`；公共组件用多词 PascalCase（NewsItem、TabBar）。
- Vant 函数式 API（`showToast`/`showDialog`/`showLoadingToast`/`showSuccessToast`/`showFailToast`/`closeToast`）从 `'vant'` 直接导入，不走全局注册。
- 反馈交互统一用 Vant 轻提示：操作前 loading toast（`forbidClick: true, duration: 0`，完成后手动 `close()`），成功/失败用对应类型。

**数据与请求**

- 接口调用只写在 store action 里；view 不直接发请求（AIChat 的 fetch 除外）。
- action 返回 `{ success, message?, data? }`，不 throw；catch 里 `console.error` 是既定实践（ESLint `no-console` 已关）。
- 新增接口时对照 `docs/api-spec.md` 的参数 alias（camelCase）——前端传参/取字段以 spec 为准（第 8 章对照表）。

**文案与国际化**

- 用户可见文案一律走 `$t()` / `t()`，键进两份语言包**同步维护**；禁止模板里写死中文。
- 与后端数据值相关的翻译（如分类名）走 `constants/` 映射表模式。

**样式**

- 组件样式全部 `<style scoped>`；覆盖 Vant 内部类用 `:deep()` 选择器（见 Home.vue）。
- 新页面主题色优先用 `var(--primary-color)` 等变量（第 18 章）。

**Lint / 格式 / 提交**

- `npm run lint` 必须零告警再提交；ESLint 管正确性，格式交给 Prettier（`npm run format`）。
- Prettier 约定：无分号、单引号、行宽 100、es5 逗号。历史文件风格不完全统一（部分带分号），改动时对所在文件现状从众即可，不必全量重排。
- ESLint 浏览器全局变量（window/localStorage/fetch/AbortController 等）在 `eslint.config.js` 的 `globals` 白名单维护，用到新全局先去确认。

---

## 24. 调试与排错手册

| 症状 | 大概率原因 | 手段 |
|------|-----------|------|
| 页面能开但所有列表为空 | 后端没启动 / `VITE_API_BASE_URL` 指错 | 先确认 `http://127.0.0.1:8000/docs` 可访问；Network 面板看请求打到哪 |
| 控制台报 CORS 错误 | 后端非 DEBUG_MODE 且白名单没配 | 用后端开发模式，或改走 `/api-proxy` 代理 |
| 刷新后掉登录态 | `user-store` 键被清 / persist 失效 | Application 面板看 localStorage；确认登录成功响应里有 token |
| 频繁被弹"登录已过期"并跳登录 | 接口持续 401（token 过期/后端不认） | Network 看具体哪个接口 401；重新登录后观察是否复发 |
| 某个 Vant 组件渲染成空白 | `main.js` 没注册该组件 | 去 main.js 补 `app.use(...)`（附录 C 对照） |
| AI 问答一直转圈无回复 | 后端 AI 提供方不可用（Key 无效 / Ollama 未起） | 看后端终端日志 `app.ai` 的 warning；前端 Network 里看 SSE 帧内容 |
| AI 生成了几个字后停住 | 误触了"停止"按钮 | 再发一次；AbortError 已处理，不会报错只是内容停住 |
| 接口返回 401 | token 过期（7 天）或没带 | 已登录操作会被自动引导到登录页（带 redirect 回跳）；Network 确认请求头有 `Authorization: Bearer ...` |
| 接口返回 400 | 参数不符合后端校验（如密码 <6 位） | 响应 `data` 是字段级错误明细，直接看 message |
| 分类 Tab 显示"加载失败" | 分类接口失败（后端挂了） | 点"重试"；修好后端后刷新即可，无假数据兜底 |
| 详情页点相关新闻内容没变 | 组件复用，`onMounted` 不重跑（第 25 章） | 已知问题；刷新页面可解，修复方向见取舍表 |
| 分类 Tab 标题显示中文原文 | 新分类没进 `CATEGORY_NAME_KEY_MAP` | 补映射 + 两份语言包（categories.test.js 会帮你查漏） |
| 改了代码页面没变 | Vite 热更新偶发失灵 | 硬刷新；重启 `npm run dev` |

调试心法：**打开 Vue Devtools 看 store 状态，打开 Network 面板看请求**——先分清"数据没拿到"还是"拿到了没渲染"，再决定往 store 还是组件里找。改完跑 `npm run test` 确认 18 例全绿。

---

## 25. 已知取舍与注意点

理解这些"有意为之或暂未做"的点，避免误改：

| 现状 | 为什么 | 改进方向 |
|------|--------|----------|
| 收藏/历史"本地 + API"双轨 | 游客也能收藏/留痕，登录后以服务端为准 | 保持现状；改收藏逻辑时两条路径都要动 |
| **详情页点相关新闻不重新拉取** | 路由只变 `:id` 参数，组件实例复用，`onMounted` 不重跑 | `onBeforeRouteUpdate` 或 `watch(() => route.params.id)` 里重新调 `getNewsDetail` |
| **游客打开收藏页是空列表**（本地回退被注释） | Favorite.vue 的 `loadFavorites()` 回退被注释；History.vue 的同类回退是启用的——两页语义不一致 | 二选一：要么恢复 Favorite 的本地回退，要么明确"收藏列表仅登录可见" |
| 没有路由级登录守卫 | 游客可浏览，写操作页面内拦截 + 401 全局兜底跳转 | 若加全局守卫，注意游客浏览体验 |
| news store 不持久化 | 新闻是易变数据，每次进页面重拉 | —— |
| 列表分页页码由 `newsList.length / 10` 推算 | 简单可靠（pageSize 固定 10）；改 pageSize 需同步改这里 | 改为后端返回的 `hasMore` 驱动即可解耦 |
| `getNewsDetail` 用 `?id=${id}` 拼 URL，其余接口用 `params` | 历史写法，行为等价 | 顺手统一成 `{ params: { id } }` |
| AI 的错误文案会留在 messages 里 | 简单直接；下一轮会作为 history 发给模型 | 发送 history 前过滤掉错误占位消息 |
| Profile 的账号 ID 显示 `heima-${token前5位}`、头像写死猫图 | 教学项目的展示占位，非真实业务字段 | 接真实头像上传/编号字段时替换 |
| My/Settings 里有无点击事件的占位菜单（通知/隐私/关于） | 预留入口 | 加功能时接上 |
| 部分页面颜色写死浅色值 | 主题变量方案是后期引入的 | 新页面用 CSS 变量，旧页面渐进迁移 |

---

## 附录 A：上手自查清单

- [ ] `npm install` 后 `npm run dev` 能打开首页，后端连通（列表有数据）
- [ ] 注册 → 登录 → 刷新页面不掉登录态（localStorage 出现 `user-store`）
- [ ] 能说清一次请求经过哪几层：view → store action → request.js → 后端（第 11 章）
- [ ] 能找到任意接口的前端实现位置（store action 里的字符串路径）
- [ ] 首页切换分类 / 下拉刷新 / 上拉加载的行为链路（第 13 章）
- [ ] 收藏按钮三态 toast 与双轨数据的关系（第 10.3、14 章）
- [ ] AIChat 的 SSE 解析循环、停止生成与 DOMPurify 的位置（第 15 章）
- [ ] 401 之后会发生什么：双清 → toast → 跳登录带 redirect → 登录回跳（第 7 章）
- [ ] `npm run test` 18 例全绿；`npm run lint` 零告警
- [ ] 新增一个 Vant 组件时知道去 main.js 注册（附录 C）
- [ ] 新增文案时两份语言包同步添加
- [ ] 看完三篇动手演练，知道新增页面/接口/组件分别动哪些文件

## 附录 B：localStorage 键速查

| 键 | 写入者 | 内容 |
|----|--------|------|
| `user-store` | pinia-plugin-persistedstate（仅 user store） | `{ userInfo, token, isLogin, userBio }` |
| `news_favorites` | favorite store 手动读写 | 本地收藏数组 |
| `news_history` | history store 手动读写 | 本地历史数组（最多 50 条） |
| `theme` | theme store | `'light' \| 'dark' \| 'blue' \| 'green'` |
| `language` | language store | `'zh-CN' \| 'en-US'` |

> 401 时 `request.js` 只清 `user-store`（登录态），其余键不受影响；"退出登录"在 `My.vue` 触发 user store 的 `logout()`。

## 附录 C：Vant 组件注册清单

`main.js` 里 `app.use(...)` 注册的全部 19 个 Vant 组件（模板里 `<van-xxx>` 能用的上限就在这里；另有 i18n/router/pinia 三个非 Vant 的 `app.use`）：

`Button` `NavBar` `Tabbar` `TabbarItem` `Tab` `Tabs` `List` `PullRefresh` `Cell` `CellGroup` `Grid` `GridItem` `Empty` `Form` `Field` `Image` `Toast` `Icon` `Popup`

另外这些**函数式 API 不需要注册**，直接 `import { xxx } from 'vant'`：`showToast` `showDialog` `showLoadingToast` `showSuccessToast` `showFailToast` `closeToast`。

组件注册名与模板标签的对应规则：注册名 PascalCase 折叠后与标签一致（如 `Tabbar` → `<van-tabbar>`）。新增页面发现组件不渲染且控制台无报错，八成是没注册。
