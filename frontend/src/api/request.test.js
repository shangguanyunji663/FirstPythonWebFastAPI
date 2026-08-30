import { beforeEach, describe, expect, it } from 'vitest'
import request, { setAuthToken } from './request'

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
  beforeEach(() => {
    localStorage.clear()
    setAuthToken(null)
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
})
