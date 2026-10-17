import { describe, expect, it, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

import { ApiError } from '@/api/client'
import { useAuthStore } from '../auth'

const loginMock = vi.hoisted(() =>
  vi.fn(async () => ({ access: 'access-token', refresh: 'refresh-token' })),
)

vi.mock('@/api/auth', () => ({
  login: loginMock,
}))

vi.mock('@/api/client', async () => {
  const actual = await vi.importActual<typeof import('@/api/client')>('@/api/client')
  return {
    ...actual,
    getAccessToken: vi.fn(() => null),
    setTokens: vi.fn(),
    clearTokens: vi.fn(),
  }
})

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('logs in and marks authenticated', async () => {
    const store = useAuthStore()
    await store.login('admin', 'admin')
    expect(store.accessToken).toBe('access-token')
    expect(store.isAuthenticated).toBe(true)
  })

  it('shows an invalid credentials message for unauthorized login', async () => {
    loginMock.mockRejectedValueOnce(
      new ApiError('Request failed: 401', 401, { detail: 'boom' }, 'http://127.0.0.1:8000/api/auth/token/'),
    )

    const store = useAuthStore()

    await expect(store.login('admin', 'admin')).rejects.toBeInstanceOf(Error)
    expect(store.error).toBe('اسم المستخدم أو كلمة المرور خطأ')
  })

  it('shows a generic fallback on other login failures', async () => {
    loginMock.mockRejectedValueOnce(
      new ApiError('Request failed: 500', 500, { detail: 'boom' }, 'http://127.0.0.1:8000/api/auth/token/'),
    )

    const store = useAuthStore()

    await expect(store.login('admin', 'admin')).rejects.toBeInstanceOf(Error)
    expect(store.error).toBe('somthing get wrong contact with adminstratot')
  })
})
