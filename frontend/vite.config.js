import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 路径别名：组件内可用 @/store/user 代替 ../../store/user
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      // 开发环境代理：如将 api.js 的 baseURL 改为 '/api-proxy'，
      // 请求会转发到后端 8000 端口，可省去 CORS 依赖
      '/api-proxy': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api-proxy/, ''),
      },
    },
  },
})
