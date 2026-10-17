<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { useAuthStore } from '@/stores/auth'
import { APP_VERSION } from '@/version'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  username: '',
  password: '',
})

const localError = ref<string | null>(null)

async function onSubmit() {
  localError.value = null
  try {
    await auth.login(form.username.trim(), form.password)
    await router.push({ name: 'clients' })
  } catch {
    localError.value = auth.error ?? 'فشل تسجيل الدخول'
  }
}
</script>

<template>
  <section class="login">
    <UiCard>
      <template #title>لوحة التحكم</template>
      <template #description>سجّل الدخول للوصول إلى لوحة المحترف</template>

      <form class="form" @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="username">اسم المستخدم</UiLabel>
          <UiInput
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            required
          />
        </div>

        <div class="ui-field">
          <UiLabel html-for="password">كلمة المرور</UiLabel>
          <UiInput
            id="password"
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            required
      />
        </div>

        <p v-if="localError" class="ui-error">{{ localError }}</p>

        <UiButton type="submit" :disabled="auth.loading" class="submit">
          {{ auth.loading ? 'جارٍ الدخول…' : 'تسجيل الدخول' }}
        </UiButton>
      </form>
    </UiCard>
    <p class="app-version" aria-label="إصدار التطبيق">{{ APP_VERSION }}</p>
  </section>
</template>

<style scoped>
.login {
  width: min(26rem, 100%);
}

.form {
  margin-top: 0.25rem;
}

.submit {
  width: 100%;
  margin-top: 0.5rem;
}

.ui-error {
  white-space: pre-line;
}

.app-version {
  margin: 0.85rem 0 0;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: hsl(var(--muted-foreground));
}
</style>
