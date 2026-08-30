import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// vi.hoisted：mock 函数要提升到 vi.mock 工厂可用之前定义
const { mockRequest, mockSetAuthToken } = vi.hoisted(() => ({
  mockRequest: { post: vi.fn(), get: vi.fn(), put: vi.fn() },
  mockSetAuthToken: vi.fn(),
}))

vi.mock('../api/request', () => ({
  default: mockRequest,
  setAuthToken: mockSetAuthToken,
}))

import { useUserStore } from './user'

const successBody = {
  data: {
    code: 200,
    data: { token: 'token-1', userInfo: { id: 1, username: 'tester' } },
  },
}

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('登录成功：写入用户信息与 token，并向请求模块注入 token', async () => {
    mockRequest.post.mockResolvedValueOnce(successBody)
    const store = useUserStore()

    const result = await store.login({ username: 'tester', password: 'secret' })

    expect(result.success).toBe(true)
    expect(store.isLogin).toBe(true)
    expect(store.token).toBe('token-1')
    expect(store.userInfo.username).toBe('tester')
    expect(mockSetAuthToken).toHaveBeenCalledWith('token-1')
    expect(mockRequest.post).toHaveBeenCalledWith('/api/user/login', {
      username: 'tester',
      password: 'secret',
    })
  })

  it('登录失败（业务 code 非 200）：返回后端错误信息', async () => {
    mockRequest.post.mockResolvedValueOnce({ data: { code: 400, message: '用户名或密码错误' } })
    const store = useUserStore()

    const result = await store.login({ username: 'x', password: 'y' })

    expect(result.success).toBe(false)
    expect(result.message).toBe('用户名或密码错误')
    expect(store.isLogin).toBe(false)
  })

  it('登录请求异常：返回兜底文案', async () => {
    mockRequest.post.mockRejectedValueOnce({ message: 'Network Error' })
    const store = useUserStore()

    const result = await store.login({ username: 'x', password: 'y' })

    expect(result.success).toBe(false)
    expect(result.message).toBe('登录请求失败，请稍后再试')
  })

  it('注册成功自动登录', async () => {
    mockRequest.post.mockResolvedValueOnce(successBody)
    const store = useUserStore()

    const result = await store.register({ username: 'tester', password: 'secret' })

    expect(result.success).toBe(true)
    expect(store.isLogin).toBe(true)
    expect(mockSetAuthToken).toHaveBeenCalledWith('token-1')
  })

  it('登出：清空登录状态并释放 token', () => {
    const store = useUserStore()
    store.userInfo = { id: 1 }
    store.token = 'token-1'
    store.isLogin = true

    store.logout()

    expect(store.token).toBe('')
    expect(store.isLogin).toBe(false)
    expect(store.userInfo).toBeNull()
    expect(mockSetAuthToken).toHaveBeenCalledWith(null)
  })

  it('未登录时获取用户信息直接返回失败，不发请求', async () => {
    const store = useUserStore()

    const result = await store.getUserInfoDetail()

    expect(result.success).toBe(false)
    expect(mockRequest.get).not.toHaveBeenCalled()
  })
})
