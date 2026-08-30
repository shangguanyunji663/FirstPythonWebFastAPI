/**
 * API配置文件
 * 包含API基础URL和AI问答功能的API参数
 *
 * AI 问答走后端代理接口（SSE 流式），密钥由后端 .env 管理，前端不持有任何 Key；
 * 提供方（智谱/本地 Ollama）在后端 .env 的 AI_PROVIDER 切换。
 */

// API基础URL配置：默认本机后端；可通过 frontend/.env.local 的 VITE_API_BASE_URL 覆盖
// 开发环境也可改用 Vite 代理（见 vite.config.js 的 /api-proxy）以摆脱 CORS 依赖
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
}

// AI 问答走后端代理接口（需要登录，Token 由 src/api/request.js 统一携带）
export const aiConfig = {
  chatEndpoint: '/api/ai/chat',
  historyEndpoint: '/api/ai/history',
}

