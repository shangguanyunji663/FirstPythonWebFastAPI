/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 *
 * AI 提供方通过 frontend/.env.local 的 VITE_AI_PROVIDER 切换：
 *   zhipu  —— 智谱开放平台（云端，需 VITE_AI_API_KEY）
 *   ollama —— 本地 Ollama（免费离线，无需真实 Key）
 */

// API基础URL配置：默认本机后端；可通过 frontend/.env.local 的 VITE_API_BASE_URL 覆盖
// 开发环境也可改用 Vite 代理（见 vite.config.js 的 /api-proxy）以摆脱 CORS 依赖
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
}

// AI 提供方注册表：均使用 OpenAI 兼容接口（含流式 SSE）
const AI_PROVIDERS = {
  zhipu: {
    apiEndpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    apiKey: import.meta.env.VITE_AI_API_KEY || '',
    model: import.meta.env.VITE_AI_MODEL || 'glm-4.7-flash',
  },
  ollama: {
    // Ollama 的 OpenAI 兼容端点；模型须已 ollama pull，如 qwen3:8b / llama3.1:8b
    apiEndpoint: `${import.meta.env.VITE_OLLAMA_BASE_URL || 'http://localhost:11434'}/v1/chat/completions`,
    apiKey: 'ollama', // Ollama 不校验 Key，但 Bearer 头需非空值
    model: import.meta.env.VITE_OLLAMA_MODEL || 'qwen3:8b',
  },
}

const activeProvider = AI_PROVIDERS[import.meta.env.VITE_AI_PROVIDER] || AI_PROVIDERS.zhipu

export const aiChatConfig = {
  provider: import.meta.env.VITE_AI_PROVIDER || 'zhipu',
  apiEndpoint: activeProvider.apiEndpoint,
  apiKey: activeProvider.apiKey,
  model: activeProvider.model,
}
