<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { getStatistics, type Statistics } from '@/api/statistics'
import UiCard from '@/components/ui/UiCard.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const stats = ref<Statistics | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getStatistics()
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      auth.logout()
      await router.push({ name: 'login' })
      return
    }
    error.value = 'تعذر تحميل الإحصائيات.'
  } finally {
    loading.value = false
  }
}

onMounted(() => void load())
</script>

<template>
  <section class="page">
    <header>
      <h1>الإحصائيات</h1>
      <p class="muted">الفواتير = الفواتير المؤكدة. الربح = الفواتير − المصروفات.</p>
    </header>

    <p v-if="loading" class="muted">جارٍ التحميل…</p>
    <p v-else-if="error" class="ui-error">{{ error }}</p>

    <template v-else-if="stats">
      <div class="stats">
        <UiCard>
          <p class="stat-label">إجمالي الفواتير</p>
          <p class="stat-value">{{ stats.total_invoices }}</p>
        </UiCard>
        <UiCard>
          <p class="stat-label">إجمالي المصروفات</p>
          <p class="stat-value">{{ stats.total_expenses }}</p>
        </UiCard>
        <UiCard>
          <p class="stat-label">الفلوس الحالية (الفواتير − المصروفات)</p>
          <p class="stat-value" :data-negative="Number(stats.current_money) < 0">
            {{ stats.current_money }}
          </p>
        </UiCard>
        <UiCard>
          <p class="stat-label">مكسب الشهر الحالي</p>
          <p class="stat-value" :data-negative="Number(stats.month.profit) < 0">
            {{ stats.month.profit }}
          </p>
          <p class="stat-sub">
            فواتير {{ stats.month.invoices }} · مصروفات {{ stats.month.expenses }}
          </p>
        </UiCard>
        <UiCard>
          <p class="stat-label">مكسب السنة</p>
          <p class="stat-value" :data-negative="Number(stats.year.profit) < 0">
            {{ stats.year.profit }}
          </p>
          <p class="stat-sub">
            فواتير {{ stats.year.invoices }} · مصروفات {{ stats.year.expenses }}
          </p>
        </UiCard>
      </div>
    </template>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}
h1 {
  margin: 0;
  font-size: 1.5rem;
}
.muted {
  color: hsl(var(--muted-foreground));
  margin: 0.35rem 0 0;
}
.stats {
  display: grid;
  gap: 0.75rem;
}
@media (min-width: 768px) {
  .stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
.stat-label {
  margin: 0;
  color: hsl(var(--muted-foreground));
  font-size: 0.9rem;
}
.stat-value {
  margin: 0.35rem 0 0;
  font-size: 1.4rem;
  font-weight: 700;
}
.stat-value[data-negative='true'] {
  color: hsl(var(--destructive));
}
.stat-sub {
  margin: 0.35rem 0 0;
  color: hsl(var(--muted-foreground));
  font-size: 0.85rem;
}
</style>
