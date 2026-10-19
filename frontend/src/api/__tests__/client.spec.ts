import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiFetch, clearTokens, getAccessToken, setTokens } from '../client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

describe('api client', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('stores and clears tokens', () => {
    setTokens('a', 'r')
    expect(getAccessToken()).toBe('a')
    clearTokens()
    expect(getAccessToken()).toBeNull()
  })

  it('sends bearer token and parses json', async () => {
    setTokens('tok', 'r')
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    expect(await apiFetch('/api/v1/clients/')).toEqual({ ok: true })
    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1]
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer tok')
  })

  it('returns undefined on 204', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 204 })))
    expect(await apiFetch('/x', { method: 'DELETE' })).toBeUndefined()
  })

  it('throws ApiError carrying status and body', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ detail: 'nope' }, 400)))
    await expect(apiFetch('/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      body: { detail: 'nope' },
    })
    await expect(apiFetch('/x')).rejects.toBeInstanceOf(ApiError)
  })
})
