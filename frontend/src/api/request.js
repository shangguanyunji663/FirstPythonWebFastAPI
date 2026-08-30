/**
 * axios 统一封装
 * 统一注入 baseURL、超时、Bearer Token 与 401 处理，各 store 不再各自拼接地址和请求头
 */
import axios from 'axios';
import { showToast } from 'vant';
import router from '../router';
import i18n from '../i18n';
import { apiConfig } from '../config/api';

const request = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 10000,
});

// 模块内保存 token：登录后由 user store 调用 setAuthToken 注入
let authToken = null;

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

// 从持久化的用户 store（localStorage）兜底读取 token：页面刷新后模块内 token 会丢失
function readPersistedToken() {
  try {
    const saved = localStorage.getItem('user-store');
    return saved ? JSON.parse(saved).token || null : null;
  } catch {
    return null;
  }
}

// 响应拦截器：401 清理本地登录态；非登录/注册接口的 401 引导重新登录并回跳原页面
request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      setAuthToken(null);
      localStorage.removeItem('user-store');
      const url = error.config?.url || '';
      // 登录/注册接口自身的 401（如密码错误）由表单提示，不劫持跳转
      const isAuthEndpoint = url.includes('/api/user/login') || url.includes('/api/user/register');
      if (!isAuthEndpoint && router.currentRoute.value.path !== '/login') {
        showToast({ message: i18n.global.t('common.loginExpired'), position: 'bottom' });
        router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } });
      }
    }
    return Promise.reject(error);
  }
);

export default request;
