import { beforeEach, describe, expect, it, vi } from 'vitest'
import request, { setAuthToken } from './request'
import router from '../router'

// 单测只关心拦截器行为，不真渲染 vant 组件（showToast 在 jsdom 下的挂载不在本文件断言范围）
vi.mock('vant', () => ({ showToast: vi.fn() }))

// 自定义 axios adapter：捕获拦截器处理后的请求配置，并按给定状态码返回。
// 内置 adapter 的 validateStatus/settle 逻辑不作用于自定义 adapter，
// 这里手动模拟：非 2xx 抛出带 response 的错误，触发响应拦截器的错误分支
const makeAdapter = (status = 200, data = { code: 200 }) => {
  const captured = []
  const adapter = async (config) => {
    captured.push(config)
    const response = { data, status, statusText: String(status), headers: {}, config }
    if (status >= 200 && status < 300) {
      return response
    }
    const error = new Error(`Request failed with status code ${status}`)
    error.response = response
    error.config = config
    throw error
  }
  return { adapter, captured }
}

describe('axios 统一封装', () => {
  beforeEach(async () => {
    localStorage.clear()
    setAuthToken(null)
    await router.push('/')  // 用例间重置路由，隔离 401 跳转副作用
  })

  it('setAuthToken 后所有请求统一携带 Bearer Token', async () => {
    setAuthToken('token-abc')
    const { adapter, captured } = makeAdapter()
    await request.get('/api/user/info', { adapter })
    expect(captured[0].headers.Authorization).toBe('Bearer token-abc')
  })

  it('模块内 token 丢失（页面刷新）时回退读取 localStorage 持久化 token', async () => {
    localStorage.setItem('user-store', JSON.stringify({ token: 'persisted-token' }))
    const { adapter, captured } = makeAdapter()
    await request.get('/api/user/info', { adapter })
    expect(captured[0].headers.Authorization).toBe('Bearer persisted-token')
  })

  it('无 token 时不携带 Authorization 头', async () => {
    const { adapter, captured } = makeAdapter()
    await request.get('/api/news/categories', { adapter })
    expect(captured[0].headers.Authorization).toBeUndefined()
  })

  it('401 响应清理本地登录态并继续抛错，后续请求不再携带 token', async () => {
    setAuthToken('expired-token')
    localStorage.setItem('user-store', JSON.stringify({ token: 'expired-token' }))

    const { adapter } = makeAdapter(401, { code: 401, message: '无效的令牌' })
    await expect(request.get('/api/user/info', { adapter })).rejects.toBeTruthy()
    expect(localStorage.getItem('user-store')).toBeNull()

    const { adapter: adapter2, captured } = makeAdapter()
    await request.get('/api/user/info', { adapter: adapter2 })
    expect(captured[0].headers.Authorization).toBeUndefined()
  })

  it('非 401 错误不影响本地登录态', async () => {
    setAuthToken('valid-token')
    localStorage.setItem('user-store', JSON.stringify({ token: 'valid-token' }))

    const { adapter } = makeAdapter(500)
    await expect(request.get('/api/news/list', { adapter })).rejects.toBeTruthy()
    expect(JSON.parse(localStorage.getItem('user-store')).token).toBe('valid-token')
  })

  it('401 且非登录接口：清登录态并跳转 /login（带 redirect 回跳参数）', async () => {
    setAuthToken('expired-token')
    localStorage.setItem('user-store', JSON.stringify({ token: 'expired-token' }))
    await router.push('/favorite')

    const { adapter } = makeAdapter(401, { code: 401, message: '无效的令牌' })
    await expect(request.get('/api/favorite/list', { adapter })).rejects.toBeTruthy()
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))

    expect(router.currentRoute.value.query.redirect).toBe('/favorite')
    expect(localStorage.getItem('user-store')).toBeNull()
  })

  it('登录接口自身的 401（密码错误）不触发跳转，由表单自行提示', async () => {
    await router.push('/login')

    const { adapter } = makeAdapter(401, { code: 401, message: '用户名或密码错误' })
    await expect(
      request.post('/api/user/login', { username: 'a', password: 'b' }, { adapter })
    ).rejects.toBeTruthy()
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBeUndefined()
  })
})
