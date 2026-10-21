<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { expenseCategoriesApi, type ExpenseCategory } from '@/api/expenseCategories'
import {
  retrieveServiceCategory,
  type ServiceCategory,
  type ServiceCategoryDetail,
} from '@/api/serviceCategories'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { useAuthStore } from '@/stores/auth'
import { useServiceCategoriesStore } from '@/stores/serviceCategories'
import { useServicesStore } from '@/stores/services'

const auth = useAuthStore()
const categories = useServiceCategoriesStore()
const services = useServicesStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  expense_category: '' as string | number,
})

const expenseCategories = ref<ExpenseCategory[]>([])

const iconFile = ref<File | null>(null)
const iconCleared = ref(false)
const iconPreview = ref<string | null>(null)

function setIconPreview(url: string | null) {
  if (iconPreview.value?.startsWith('blob:')) URL.revokeObjectURL(iconPreview.value)
  iconPreview.value = url
}

function onIconChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null
  iconFile.value = file
  iconCleared.value = false
  setIconPreview(file ? URL.createObjectURL(file) : null)
}

function clearIcon() {
  iconFile.value = null
  iconCleared.value = true
  setIconPreview(null)
}

function iconPayload(): File | null | undefined {
  if (iconFile.value) return iconFile.value
  return iconCleared.value ? null : undefined
}

const serviceCountByCategory = computed(() => {
  const counts = new Map<number, number>()
  for (const service of services.items) {
    counts.set(service.service_category, (counts.get(service.service_category) ?? 0) + 1)
  }
  return counts
})

function servicesCount(categoryId: number) {
  return serviceCountByCategory.value.get(categoryId) ?? 0
}

function resetForm() {
  editingId.value = null
  form.name = ''
  form.expense_category = ''
  iconFile.value = null
  iconCleared.value = false
  setIconPreview(null)
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(category: ServiceCategory) {
  editingId.value = category.id
  form.name = category.name
  form.expense_category = category.expense_category ?? ''
  iconFile.value = null
  iconCleared.value = false
  setIconPreview(category.icon)
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

async function load() {
  try {
    services.search = ''
    services.categoryFilter = null
    await Promise.all([
      categories.fetchAll(),
      services.fetchAll(),
      expenseCategoriesApi.list().then((data) => {
        expenseCategories.value = data.results
      }),
    ])
  } catch (err) {
    await handleAuthError(err)
  }
}

async function onSubmit() {
  formError.value = null
  if (!form.name.trim()) {
    formError.value = 'الاسم مطلوب.'
    return
  }

  const payload = {
    name: form.name.trim(),
    expense_category: form.expense_category === '' ? null : Number(form.expense_category),
    icon: iconPayload(),
  }

  saving.value = true
  try {
    if (editingId.value) {
      await categories.update(editingId.value, payload)
    } else {
      await categories.create(payload)
    }
    closeDialog()
    await categories.fetchAll()
  } catch (err) {
    await handleAuthError(err)
    formError.value = err instanceof ApiError ? 'تعذّر حفظ الخدمة الرئيسية.' : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}

async function onDelete(category: ServiceCategory) {
  const count = servicesCount(category.id)
  const message =
    count > 0
      ? `حذف الخدمة الرئيسية «${category.name}» سيؤدي أيضًا إلى حذف ${count} خدمة مرتبطة. هل تريد المتابعة؟`
      : `حذف الخدمة الرئيسية «${category.name}»؟`

  if (!confirm(message)) return

  try {
    await categories.remove(category.id)
    await services.fetchAll()
    if (editingId.value === category.id) closeDialog()
  } catch (err) {
    await handleAuthError(err)
  }
}

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const detail = ref<ServiceCategoryDetail | null>(null)

async function openDetail(category: ServiceCategory) {
  detail.value = null
  detailError.value = null
  detailOpen.value = true
  detailLoading.value = true
  try {
    detail.value = await retrieveServiceCategory(category.id)
  } catch (err) {
    await handleAuthError(err)
    detailError.value = err instanceof ApiError ? err.message : 'فشل التحميل.'
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section>
    <header class="page-header">
      <div>
        <h1>الخدمات الرئيسية</h1>
        <p>إدارة الأقسام الرئيسية وعدد الخدمات التابعة لها</p>
      </div>
      <UiButton @click="openCreate">خدمة رئيسية</UiButton>
    </header>

    <p v-if="categories.error" class="ui-error">{{ categories.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>#</th>
              <th>الأيقونة</th>
              <th>الاسم</th>
              <th>عدد الخدمات</th>
              <th>تصنيف المصروفات</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="categories.loading">
              <td colspan="6" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="categories.items.length === 0">
              <td colspan="6" class="ui-empty">لا توجد خدمات رئيسية بعد.</td>
            </tr>
            <tr v-for="(category, i) in categories.items" :key="category.id">
              <td>{{ i + 1 }}</td>
              <td>
                <img v-if="category.icon" :src="category.icon" alt="" class="icon-cell" />
              </td>
              <td>{{ category.name }}</td>
              <td>{{ servicesCount(category.id) }}</td>
              <td>{{ category.expense_category_name ?? '—' }}</td>
              <td>
                <div class="row-actions">
                  <UiButton variant="outline" size="sm" @click="openDetail(category)">تفاصيل</UiButton>
                  <UiButton variant="outline" size="sm" @click="openEdit(category)">تعديل</UiButton>
                  <UiButton variant="destructive" size="sm" @click="onDelete(category)">حذف</UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiCard>

    <UiDialog
      v-model:open="dialogOpen"
      :title="editingId ? 'تعديل خدمة رئيسية' : 'خدمة رئيسية جديدة'"
      description="أدخل اسم الخدمة الرئيسية."
    >
      <form @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="category-name">الاسم</UiLabel>
          <UiInput id="category-name" v-model="form.name" required />
        </div>

        <div class="ui-field">
          <UiLabel html-for="category-expense">تصنيف المصروفات</UiLabel>
          <UiSelect id="category-expense" v-model="form.expense_category">
            <option value="">— بدون —</option>
            <option v-for="ec in expenseCategories" :key="ec.id" :value="ec.id">
              {{ ec.main_category_name }} / {{ ec.name }}
            </option>
          </UiSelect>
        </div>

        <div class="ui-field">
          <UiLabel html-for="category-icon">الأيقونة</UiLabel>
          <div class="icon-field">
            <img v-if="iconPreview" :src="iconPreview" alt="" class="icon-img" />
            <input id="category-icon" type="file" accept="image/*" @change="onIconChange" />
            <UiButton v-if="iconPreview" type="button" variant="outline" size="sm" @click="clearIcon">
              إزالة
            </UiButton>
          </div>
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
      :title="detail ? detail.name : 'تفاصيل الخدمة الرئيسية'"
      description="ملخص الفواتير المؤكدة والمصروفات المرتبطة."
    >
      <p v-if="detailLoading" class="detail-empty">جارٍ التحميل…</p>
      <p v-else-if="detailError" class="ui-error">{{ detailError }}</p>
      <template v-else-if="detail">
        <h3 class="detail-subtitle">الفواتير</h3>
        <div class="detail-stats">
          <div class="stat stat-main">
            <span class="stat-label">إجمالي مبالغ الفواتير</span>
            <strong class="stat-value">{{ detail.invoices_total }}</strong>
          </div>
          <div class="stat">
            <span class="stat-label">عدد الفواتير</span>
            <strong class="stat-value">{{ detail.invoices_count }}</strong>
          </div>
        </div>

        <h3 class="detail-subtitle">آخر 5 فواتير</h3>
        <p v-if="detail.last_invoices.length === 0" class="detail-empty">
          لا توجد فواتير مؤكدة بعد.
        </p>
        <ul v-else class="detail-list">
          <li v-for="inv in detail.last_invoices" :key="inv.id" class="detail-item">
            <div class="item-info">
              <span class="item-desc">{{ inv.number }} · {{ inv.client_name }}</span>
              <span class="item-meta">{{ inv.issue_date }} · إجمالي الفاتورة {{ inv.invoice_total }}</span>
            </div>
            <span class="item-amount">{{ inv.category_amount }}</span>
          </li>
        </ul>

        <h3 class="detail-subtitle detail-gap">
          المصروفات<template v-if="detail.expense_category_name"> — {{ detail.expense_category_name }}</template>
        </h3>
        <p v-if="!detail.expense_category" class="detail-empty">لم يتم ربط تصنيف مصروفات.</p>
        <div v-else class="detail-stats">
          <div class="stat stat-main">
            <span class="stat-label">إجمالي المصروفات</span>
            <strong class="stat-value">{{ detail.expenses_total }}</strong>
          </div>
          <div class="stat">
            <span class="stat-label">عدد المصروفات</span>
            <strong class="stat-value">{{ detail.expenses_count }}</strong>
          </div>
        </div>

        <div class="ui-dialog-footer">
          <UiButton variant="outline" @click="detailOpen = false">إغلاق</UiButton>
        </div>
      </template>
    </UiDialog>
  </section>
</template>

<style scoped>
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
.detail-gap {
  margin-top: 1.25rem;
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
}
.item-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.item-desc {
  font-weight: 500;
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
.icon-field {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.icon-img {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.375rem;
  border: 1px solid hsl(var(--border));
  object-fit: cover;
}

.icon-cell {
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  border: 1px solid hsl(var(--border));
  object-fit: cover;
  display: block;
}
</style>
