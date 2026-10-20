<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import {
  expenseCategoriesApi,
  type ExpenseCategory,
  type ExpenseCategoryDetail,
} from '@/api/expenseCategories'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { useAuthStore } from '@/stores/auth'
import { useExpenseCategoriesStore } from '@/stores/expenseCategories'

const auth = useAuthStore()
const store = useExpenseCategoriesStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)
const mainFilter = ref<number | null>(null)
const form = reactive({
  name: '',
  main_category: null as number | null,
  order_number: 0,
  is_shown: true,
})

function resetForm() {
  editingId.value = null
  form.name = ''
  form.order_number = 0
  form.is_shown = true
  form.main_category = mainFilter.value
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(item: ExpenseCategory) {
  editingId.value = item.id
  form.name = item.name
  form.order_number = item.order_number
  form.is_shown = item.is_shown
  form.main_category = item.main_category
  formError.value = null
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  resetForm()
}

async function handleAuthError(err: unknown) {
  if (err instanceof ApiError && err.status === 401) {
    auth.logout()
    await router.push({ name: 'login' })
  }
}

function reload() {
  return store.fetchCategories(mainFilter.value).catch(handleAuthError)
}

async function onSubmit() {
  formError.value = null
  if (!form.main_category) {
    formError.value = 'التصنيف الرئيسي مطلوب.'
    return
  }
  if (!form.name.trim()) {
    formError.value = 'الاسم مطلوب.'
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      main_category: form.main_category,
      order_number: Number(form.order_number) || 0,
      is_shown: form.is_shown,
    }
    if (editingId.value) await store.updateCategory(editingId.value, payload)
    else await store.createCategory(payload)
    closeDialog()
    await reload()
  } catch (err) {
    await handleAuthError(err)
    formError.value = err instanceof ApiError ? err.message : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}

async function onDelete(item: ExpenseCategory) {
  if (!confirm(`حذف التصنيف «${item.name}»؟`)) return
  try {
    await store.removeCategory(item.id)
    await reload()
  } catch (err) {
    await handleAuthError(err)
    if (err instanceof ApiError) alert(err.message)
  }
}

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const detail = ref<ExpenseCategoryDetail | null>(null)

async function openDetail(item: ExpenseCategory) {
  detail.value = null
  detailError.value = null
  detailOpen.value = true
  detailLoading.value = true
  try {
    detail.value = await expenseCategoriesApi.retrieve(item.id)
  } catch (err) {
    await handleAuthError(err)
    detailError.value = err instanceof ApiError ? err.message : 'فشل التحميل.'
  } finally {
    detailLoading.value = false
  }
}

function goToExpenses(item: ExpenseCategory) {
  void router.push({
    name: 'expenses',
    query: { main_category: item.main_category, category: item.id },
  })
}

function selectMain(id: number) {
  mainFilter.value = id
  void reload()
}

onMounted(async () => {
  try {
    await store.fetchMainCategories()
  } catch (err) {
    await handleAuthError(err)
    return
  }
  const first = store.mainCategories[0]
  if (first) selectMain(first.id)
})
</script>

<template>
  <section>
    <header class="page-header">
      <div>
        <h1>التصنيفات الفرعية للمصروفات</h1>
        <p>مثل: كهرباء، غاز، إيجار تحت المصنع</p>
      </div>
      <UiButton @click="openCreate">تصنيف فرعي جديد</UiButton>
    </header>

    <div class="main-tabs">
      <UiButton
        v-for="m in store.mainCategories"
        :key="m.id"
        :variant="mainFilter === m.id ? 'default' : 'outline'"
        @click="selectMain(m.id)"
      >
        {{ m.name }}
      </UiButton>
    </div>

    <p v-if="store.error" class="ui-error">{{ store.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>#</th>
              <th>الاسم</th>
              <th>التصنيف الرئيسي</th>
              <th>الترتيب</th>
              <th>يظهر في المصروفات</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.loading">
              <td colspan="6" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="store.categories.length === 0">
              <td colspan="6" class="ui-empty">لا توجد تصنيفات فرعية.</td>
            </tr>
            <tr v-for="(item, i) in store.categories" :key="item.id">
              <td>{{ i + 1 }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.main_category_name }}</td>
              <td>{{ item.order_number }}</td>
              <td>{{ item.is_shown ? 'نعم' : 'لا' }}</td>
              <td>
                <div class="row-actions">
                  <UiButton variant="outline" size="sm" @click="goToExpenses(item)">المصروفات</UiButton>
                  <UiButton variant="outline" size="sm" @click="openDetail(item)">تفاصيل</UiButton>
                  <UiButton variant="outline" size="sm" @click="openEdit(item)">تعديل</UiButton>
                  <UiButton variant="destructive" size="sm" @click="onDelete(item)">حذف</UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiCard>

    <UiDialog
      v-model:open="dialogOpen"
      :title="editingId ? 'تعديل تصنيف فرعي' : 'تصنيف فرعي جديد'"
      description="اختر التصنيف الرئيسي وأدخل الاسم."
    >
      <form @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="cat-main">التصنيف الرئيسي</UiLabel>
          <UiSelect id="cat-main" v-model="form.main_category" required>
            <option :value="null" disabled>اختر التصنيف الرئيسي</option>
            <option v-for="m in store.mainCategories" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </UiSelect>
        </div>
        <div class="ui-field">
          <UiLabel html-for="cat-name">الاسم</UiLabel>
          <UiInput id="cat-name" v-model="form.name" required />
        </div>
        <div class="ui-field">
          <UiLabel html-for="cat-order">رقم الترتيب</UiLabel>
          <UiInput id="cat-order" v-model="form.order_number" type="number" min="0" />
        </div>
        <div class="ui-field">
          <label class="shown-check">
            <input v-model="form.is_shown" type="checkbox" />
            إظهار في صفحة المصروفات
          </label>
        </div>
        <p v-if="formError" class="ui-error">{{ formError }}</p>
        <div class="ui-dialog-footer">
          <UiButton type="submit" :disabled="saving">
            {{ saving ? 'جارٍ الحفظ…' : editingId ? 'تحديث' : 'حفظ' }}
          </UiButton>
          <UiButton type="button" variant="outline" @click="closeDialog">إلغاء</UiButton>
        </div>
      </form>
    </UiDialog>

    <UiDialog
      v-model:open="detailOpen"
      :title="detail ? detail.name : 'تفاصيل التصنيف'"
      description="ملخص التصنيف وآخر 5 مصروفات."
    >
      <div v-if="detailLoading" class="detail-skeleton" aria-busy="true">
        <span /><span /><span />
      </div>
      <p v-else-if="detailError" class="ui-error">{{ detailError }}</p>
      <template v-else-if="detail">
        <div class="detail-badges">
          <span class="badge">{{ detail.main_category_name }}</span>
          <span class="badge" :class="detail.is_shown ? 'badge-on' : 'badge-off'">
            {{ detail.is_shown ? 'ظاهر في المصروفات' : 'مخفي' }}
          </span>
        </div>

        <div class="detail-stats">
          <div class="stat stat-main">
            <span class="stat-label">إجمالي المصروفات</span>
            <strong class="stat-value">{{ detail.total_amount }}</strong>
          </div>
          <div class="stat">
            <span class="stat-label">عدد المصروفات</span>
            <strong class="stat-value">{{ detail.expenses_count }}</strong>
          </div>
        </div>

        <h3 class="detail-subtitle">آخر المصروفات</h3>
        <p v-if="detail.last_expenses.length === 0" class="detail-empty">
          لا توجد مصروفات في هذا التصنيف بعد.
        </p>
        <ul v-else class="detail-list">
          <li v-for="e in detail.last_expenses" :key="e.id" class="detail-item">
            <div class="item-info">
              <span class="item-desc">{{ e.description || '—' }}</span>
              <span class="item-meta">
                {{ e.expense_date }}<template v-if="e.client_name"> · {{ e.client_name }}</template>
              </span>
            </div>
            <span class="item-amount">{{ e.amount }}</span>
          </li>
        </ul>

        <div class="ui-dialog-footer">
          <UiButton @click="detailOpen = false; goToExpenses(detail)">عرض كل المصروفات</UiButton>
          <UiButton variant="outline" @click="detailOpen = false">إغلاق</UiButton>
        </div>
      </template>
    </UiDialog>
  </section>
</template>

<style scoped>
.shown-check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
}
.badge-on {
  background: hsl(142 70% 94%);
  color: hsl(142 70% 25%);
}
.badge-off {
  background: hsl(0 80% 95%);
  color: hsl(0 60% 40%);
}
.detail-stats {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.9rem 1rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--muted));
}
.stat-main {
  background: hsl(var(--primary));
  border-color: transparent;
  color: hsl(var(--primary-foreground));
}
.stat-label {
  font-size: 0.8rem;
  opacity: 0.75;
}
.stat-value {
  font-size: 1.5rem;
  font-variant-numeric: tabular-nums;
}
.detail-subtitle {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  color: hsl(var(--muted-foreground));
}
.detail-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 0.9rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: background 0.15s;
}
.detail-item:hover {
  background: hsl(var(--muted));
}
.item-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.item-desc {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-meta {
  font-size: 0.78rem;
  color: hsl(var(--muted-foreground));
}
.item-amount {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.detail-empty {
  padding: 1.5rem;
  text-align: center;
  border: 1px dashed hsl(var(--border));
  border-radius: var(--radius);
  color: hsl(var(--muted-foreground));
}
.detail-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.detail-skeleton span {
  height: 3rem;
  border-radius: var(--radius);
  background: linear-gradient(90deg, hsl(var(--muted)), hsl(var(--border)), hsl(var(--muted)));
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer {
  to { background-position: -200% 0; }
}
.main-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
</style>
