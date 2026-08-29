/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置：默认本机后端；可通过 frontend/.env.local 的 VITE_API_BASE_URL 覆盖
// 开发环境也可改用 Vite 代理（见 vite.config.js 的 /api-proxy）以摆脱 CORS 依赖
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',

  // API Key 通过环境变量注入：在 frontend/.env.local 中配置 VITE_AI_API_KEY=sk-xxxx
  // 注意：真实 Key 不要写入任何被 git 追踪的文件
  apiKey: import.meta.env.VITE_AI_API_KEY || '',

  // 使用的模型
  model: 'qwen3-max-preview'
}
