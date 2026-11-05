<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { getStatistics, type Statistics } from '@/api/statistics'
import UiCard from '@/components/ui/UiCard.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const now = new Date()
const year = ref<number>(now.getFullYear())
// 0 = whole year
const month = ref<number>(now.getMonth() + 1)

const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i)
const months = [
  'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
]

const pad = (n: number) => String(n).padStart(2, '0')
const range = computed(() => {
  const y = year.value
  if (month.value === 0) return { from: `${y}-01-01`, to: `${y}-12-31` }
  const last = new Date(y, month.value, 0).getDate()
  return { from: `${y}-${pad(month.value)}-01`, to: `${y}-${pad(month.value)}-${pad(last)}` }
})

const stats = ref<Statistics | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getStatistics({ date_from: range.value.from, date_to: range.value.to })
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
watch([year, month], () => void load())

const todayCards = computed<Card[]>(() => {
  const t = stats.value?.today
  if (!t) return []
  return [
    { key: 't-pay', label: 'مدفوعات اليوم', value: t.payments, icon: 'M3 7h18v12H3z M3 11h18 M7 15h3', tone: 'green' },
    { key: 't-exp', label: 'مصروفات اليوم', value: t.expenses, icon: 'M12 3v18 M16 7H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H8', tone: 'red' },
    { key: 't-cash', label: 'فلوس الخزنة اليوم', value: t.cash, icon: 'M4 8h16v12H4z M8 8V5h8v3 M12 12v4', tone: 'violet', negative: Number(t.cash) < 0 },
  ]
})

const period = computed(() => stats.value?.period ?? null)

interface Card {
  key: string
  label: string
  value: string
  icon: string
  tone: string
  negative?: boolean
}
const cards = computed<Card[]>(() => {
  const p = period.value
  if (!p) return []
  return [
    { key: 'invoices', label: 'الفواتير', value: p.invoices, icon: 'M7 3h8l4 4v14H7z M15 3v4h4 M10 12h6 M10 16h6', tone: 'blue' },
    { key: 'payments', label: 'المدفوعات', value: p.payments, icon: 'M3 7h18v12H3z M3 11h18 M7 15h3', tone: 'green' },
    { key: 'expenses', label: 'المصروفات', value: p.expenses, icon: 'M12 3v18 M16 7H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H8', tone: 'red' },
    { key: 'profit', label: 'الربح', value: p.profit, icon: 'M3 17l6-6 4 4 8-8 M15 7h6v6', tone: 'violet', negative: Number(p.profit) < 0 },
  ]
})

// grouped bar chart (SVG), time flows right -> left (RTL)
const W = 720
const H = 280
const PAD = { l: 12, r: 56, t: 14, b: 44 }
const SERIES = [
  { k: 'invoices', name: 'فواتير' },
  { k: 'payments', name: 'مدفوعات' },
  { k: 'expenses', name: 'مصروفات' },
] as const

function niceMax(v: number) {
  if (v <= 0) return 1
  const p = 10 ** Math.floor(Math.log10(v))
  const n = v / p
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p
}
const fmt = (n: number) =>
  n >= 1_000_000 ? `${+(n / 1_000_000).toFixed(1)}M` : n >= 1000 ? `${+(n / 1000).toFixed(1)}k` : String(n)

const hover = ref<number | null>(null)
const chart = computed(() => {
  const s = period.value?.series ?? []
  const raw = Math.max(0, ...s.flatMap((x) => [Number(x.invoices), Number(x.payments), Number(x.expenses)]))
  const max = niceMax(raw)
  const h = H - PAD.t - PAD.b
  const innerW = W - PAD.l - PAD.r
  const slot = innerW / Math.max(1, s.length)
  const bw = Math.max(2, Math.min(14, slot / 3.6))
  const xc = (i: number) => W - PAD.r - slot * (i + 0.5)
  const yv = (v: number) => PAD.t + h - (v / max) * h
  const grid = [0, 1, 2, 3, 4].map((i) => ({ y: yv((max / 4) * i), t: fmt((max / 4) * i) }))
  const bars = s.flatMap((x, i) =>
    SERIES.map((d, j) => {
      const v = Number(x[d.k])
      const bh = Math.max(v > 0 ? 2 : 0, (v / max) * h)
      return { k: d.k, i, x: xc(i) + (1 - j) * (bw + 1) - bw / 2, y: PAD.t + h - bh, w: bw, h: bh }
    }),
  )
  const step = Math.max(1, Math.ceil(s.length / 10))
  const labels = s
    .map((x, i) => ({ i, t: period.value?.group === 'month' ? x.date.slice(5, 7) : x.date.slice(8), x: xc(i) }))
    .filter((l) => l.i % step === 0)
  return { bars, labels, grid, slot, xc, s }
})
const tip = computed(() => {
  if (hover.value === null || !period.value) return null
  const p = period.value.series[hover.value]
  if (!p) return null
  return { p, left: (chart.value.xc(hover.value) / W) * 100 }
})
const xTitle = computed(() => (period.value?.group === 'month' ? 'الشهر' : 'يوم الشهر'))
</script>

<template>
  <section class="page">
    <header class="head">
      <div>
        <h1>الإحصائيات</h1>
        <p class="muted">الفواتير = الفواتير المؤكدة. الربح = الفواتير − المصروفات.</p>
      </div>
      <div class="filters">
        <label>
          <span>السنة</span>
          <UiSelect v-model="year">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </UiSelect>
        </label>
        <label>
          <span>الشهر</span>
          <UiSelect v-model="month">
            <option :value="0">كل السنة</option>
            <option v-for="(m, i) in months" :key="m" :value="i + 1">{{ m }}</option>
          </UiSelect>
        </label>
      </div>
    </header>

    <p v-if="loading && !stats" class="muted">جارٍ التحميل…</p>
    <p v-else-if="error" class="ui-error">{{ error }}</p>

    <template v-else-if="stats">
      <h2 class="sub-title">اليوم <span dir="ltr" class="muted">{{ stats.today.date }}</span></h2>
      <div class="stats three">
        <UiCard v-for="c in todayCards" :key="c.key">
          <div class="box">
            <span class="icon" :data-tone="c.tone">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path :d="c.icon" />
              </svg>
            </span>
            <div>
              <p class="stat-label">{{ c.label }}</p>
              <p class="stat-value" :data-negative="c.negative">{{ c.value }}</p>
              <p class="stat-sub">اليوم: <bdi>{{ stats.today.date }}</bdi></p>
            </div>
          </div>
        </UiCard>
      </div>

      <h2 class="sub-title">الفترة المحددة</h2>
      <div class="stats" :class="{ dim: loading }">
        <UiCard v-for="c in cards" :key="c.key">
          <div class="box">
            <span class="icon" :data-tone="c.tone">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path :d="c.icon" />
              </svg>
            </span>
            <div>
              <p class="stat-label">{{ c.label }}</p>
              <p class="stat-value" :data-negative="c.negative">{{ c.value }}</p>
              <p class="stat-sub">من <bdi>{{ range.from }}</bdi> إلى <bdi>{{ range.to }}</bdi></p>
            </div>
          </div>
        </UiCard>
      </div>

      <UiCard>
        <div class="chart-head">
          <div>
            <strong>الحركة خلال الفترة</strong>
            <p class="muted small">
              من <bdi>{{ range.from }}</bdi> إلى <bdi>{{ range.to }}</bdi>
            </p>
          </div>
          <span class="legend">
            <span v-for="d in SERIES" :key="d.k" class="chip"><i :class="['dot', d.k]" /> {{ d.name }}</span>
          </span>
        </div>

        <div class="chart-wrap" @mouseleave="hover = null">
          <svg :viewBox="`0 0 ${W} ${H}`" class="chart" role="img" aria-label="رسم بياني للفواتير والمدفوعات والمصروفات">
            <defs>
              <linearGradient v-for="d in SERIES" :id="`g-${d.k}`" :key="d.k" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :class="['stop-top', d.k]" />
                <stop offset="100%" :class="['stop-bot', d.k]" />
              </linearGradient>
            </defs>
            <g v-for="g in chart.grid" :key="g.y">
              <line :x1="PAD.l" :x2="W - PAD.r" :y1="g.y" :y2="g.y" class="grid" />
              <text :x="W - PAD.r + 8" :y="g.y + 3.5" class="tick" text-anchor="start">{{ g.t }}</text>
            </g>
            <rect
              v-if="hover !== null"
              :x="chart.xc(hover) - chart.slot / 2"
              :y="PAD.t"
              :width="chart.slot"
              :height="H - PAD.t - PAD.b"
              class="hl"
              rx="4"
            />
            <rect
              v-for="(b, i) in chart.bars"
              :key="i"
              :x="b.x" :y="b.y" :width="b.w" :height="b.h"
              :fill="`url(#g-${b.k})`"
              rx="2.5"
            />
            <text v-for="l in chart.labels" :key="l.i" :x="l.x" :y="H - PAD.b + 16" class="tick" text-anchor="middle">{{ l.t }}</text>
            <text :x="(W - PAD.r + PAD.l) / 2" :y="H - 6" class="axis-title" text-anchor="middle">{{ xTitle }}</text>
            <text :x="W - 4" :y="PAD.t - 3" class="axis-title" text-anchor="end">المبلغ</text>
            <rect
              v-for="(_, i) in chart.s"
              :key="`h${i}`"
              :x="chart.xc(i) - chart.slot / 2" :y="PAD.t" :width="chart.slot" :height="H - PAD.t - PAD.b"
              fill="transparent"
              @mouseenter="hover = i"
            />
          </svg>
          <div v-if="tip" class="tip" :style="{ left: `${tip.left}%` }">
            <b><bdi>{{ tip.p.date }}</bdi></b>
            <span><i class="dot invoices" /> فواتير: {{ tip.p.invoices }}</span>
            <span><i class="dot payments" /> مدفوعات: {{ tip.p.payments }}</span>
            <span><i class="dot expenses" /> مصروفات: {{ tip.p.expenses }}</span>
          </div>
        </div>

        <ul class="explain">
          <li><b>المحور الأفقي (السفلي):</b> الزمن — {{ xTitle }}، ويتحرك من اليمين إلى اليسار.</li>
          <li><b>المحور الرأسي (الجانبي):</b> المبلغ بالجنيه (k = ألف، M = مليون).</li>
          <li><b>الأعمدة:</b> كل مجموعة = فواتير مؤكدة، مدفوعات مستلمة، مصروفات في نفس الفترة. مرّر الماوس لرؤية القيم.</li>
        </ul>
      </UiCard>

      <h2 class="sub-title">إجماليات عامة</h2>
      <div class="stats">
        <UiCard>
          <p class="stat-label">إجمالي الفواتير</p>
          <p class="stat-value">{{ stats.total_invoices }}</p>
        </UiCard>
        <UiCard>
          <p class="stat-label">إجمالي المصروفات</p>
          <p class="stat-value">{{ stats.total_expenses }}</p>
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
.head {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: space-between;
  align-items: flex-end;
}
.filters {
  display: flex;
  gap: 0.75rem;
}
.filters label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
}
h1 {
  margin: 0;
  font-size: 1.5rem;
}
.sub-title {
  margin: 0.5rem 0 0;
  font-size: 1.05rem;
}
.muted {
  color: hsl(var(--muted-foreground));
  margin: 0.35rem 0 0;
}
.stats {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.stats.dim {
  opacity: 0.6;
}
.stats.three {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
@media (min-width: 900px) {
  .stats.three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
.box {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  align-items: flex-start;
}
.icon {
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.75rem;
  flex: none;
}
.icon[data-tone='blue'] { background: #3b82f620; color: #3b82f6; }
.icon[data-tone='green'] { background: #10b98120; color: #10b981; }
.icon[data-tone='red'] { background: #ef444420; color: #ef4444; }
.icon[data-tone='violet'] { background: #8b5cf620; color: #8b5cf6; }
.stat-label {
  margin: 0;
  color: hsl(var(--muted-foreground));
  font-size: 0.9rem;
}
.stat-value {
  margin: 0.2rem 0 0;
  font-size: 1.3rem;
  font-weight: 700;
}
.stat-value[data-negative='true'] {
  color: hsl(var(--destructive));
}
@media (max-width: 640px) {
  .box {
    flex-direction: row;
    align-items: center;
    gap: 0.75rem;
  }
  .stats.three {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}
.stat-sub {
  margin: 0.25rem 0 0;
  color: hsl(var(--muted-foreground));
  font-size: 0.72rem;
  white-space: nowrap;
  direction: rtl;
  text-align: right;
}
.chart-head {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.legend {
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.dot {
  display: inline-block;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
}
.dot.invoices { background: #3b82f6; }
.dot.payments { background: #10b981; }
.dot.expenses { background: #ef4444; }
.stop-top.invoices { stop-color: #60a5fa; }
.stop-bot.invoices { stop-color: #2563eb; }
.stop-top.payments { stop-color: #34d399; }
.stop-bot.payments { stop-color: #059669; }
.stop-top.expenses { stop-color: #f87171; }
.stop-bot.expenses { stop-color: #dc2626; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: hsl(var(--muted, 0 0% 96%));
}
.small {
  font-size: 0.8rem;
  margin: 0.2rem 0 0;
}
.chart-wrap {
  position: relative;
}
.chart {
  width: 100%;
  height: auto;
  display: block;
}
.grid {
  stroke: hsl(var(--border));
  stroke-dasharray: 3 4;
}
.hl {
  fill: hsl(var(--muted-foreground) / 0.08);
}
.tick {
  font-size: 11px;
  fill: hsl(var(--muted-foreground));
}
.axis-title {
  font-size: 11px;
  font-weight: 600;
  fill: hsl(var(--muted-foreground));
}
.tip {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: grid;
  gap: 0.15rem;
  padding: 0.5rem 0.7rem;
  font-size: 0.8rem;
  background: hsl(var(--card, 0 0% 100%));
  border: 1px solid hsl(var(--border));
  border-radius: 0.6rem;
  box-shadow: 0 6px 20px rgb(0 0 0 / 0.12);
  pointer-events: none;
  white-space: nowrap;
  z-index: 2;
}
.explain {
  margin: 0.75rem 0 0;
  padding: 0 1.1rem 0 0;
  display: grid;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
}
</style>
