import { apiFetch, setTokens } from './client'

export interface TokenPair {
  access: string
  refresh: string
}

export interface LoginPayload {
  username: string
  password: string
}

export async function login(payload: LoginPayload): Promise<TokenPair> {
  const tokens = await apiFetch<TokenPair>('/api/auth/token/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  setTokens(tokens.access, tokens.refresh)
  return tokens
}
