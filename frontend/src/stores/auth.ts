import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { login as loginRequest } from '@/api/auth'
import { ApiError, clearTokens, getAccessToken } from '@/api/client'

const LOGIN_ERROR_MESSAGE = 'somthing get wrong contact with adminstratot'
const INVALID_CREDENTIALS_MESSAGE = 'اسم المستخدم أو كلمة المرور خطأ'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(getAccessToken())
  const error = ref<string | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  async function login(username: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const tokens = await loginRequest({ username, password })
      accessToken.value = tokens.access
    } catch (err) {
      accessToken.value = null
      clearTokens()
      error.value = err instanceof ApiError && err.status === 401
        ? INVALID_CREDENTIALS_MESSAGE
        : LOGIN_ERROR_MESSAGE
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearTokens()
    accessToken.value = null
  }

  return { accessToken, isAuthenticated, error, loading, login, logout }
})
