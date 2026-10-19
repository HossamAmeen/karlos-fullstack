import { beforeEach, describe, expect, it } from 'vitest'

import { clearTokens, setTokens } from '@/api/client'
import router from '..'

describe('router guards', () => {
  beforeEach(async () => {
    localStorage.clear()
    clearTokens()
    await router.push('/login').catch(() => {})
  })

  const protectedPaths = [
    '/statistics', '/clients', '/clients/1', '/service-categories', '/services',
    '/invoices', '/invoices/new', '/invoices/1', '/expenses',
    '/expense-main-categories', '/expense-categories',
  ]

  it.each(protectedPaths)('redirects anonymous %s to login', async (path) => {
    await router.push(path)
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe(path)
  })

  it.each(protectedPaths)('allows authenticated %s', async (path) => {
    setTokens('a', 'r')
    await router.push(path)
    expect(router.currentRoute.value.path).toBe(path)
  })

  it('sends logged-in users away from login and / to clients', async () => {
    setTokens('a', 'r')
    await router.push('/statistics')
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('clients')
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('clients')
  })
})
