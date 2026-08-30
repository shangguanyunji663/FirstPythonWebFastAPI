import { createI18n } from 'vue-i18n';
import zhCN from './locales/zh-CN.js';
import enUS from './locales/en-US.js';

// 模块级单例：request.js 等非组件模块 import 后可用 i18n.global.t() 取当前语言文案
const i18n = createI18n({
  legacy: false, // 使用组合式API
  locale: localStorage.getItem('language') || 'zh-CN', // 默认中文
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
});

// 兼容 main.js 的装配入口：返回同一单例
export function setupI18n() {
  return i18n;
}

// 默认导出单例：供 request.js 等非组件模块使用
export default i18n;

// 动态切换语言
export function setI18nLanguage(i18n, locale) {
  if (i18n.mode === 'legacy') {
    i18n.global.locale = locale;
  } else {
    i18n.global.locale.value = locale;
  }
  document.querySelector('html').setAttribute('lang', locale);
}