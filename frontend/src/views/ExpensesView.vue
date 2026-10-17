<script setup lang="ts">
import { onMounted, reactive, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { Expense, ExpenseCategory } from '@/api/expenses'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'

import { useAuthStore } from '@/stores/auth'
import { useExpensesStore } from '@/stores/expenses'
import { useServiceCategoriesStore } from '@/stores/serviceCategories'

const auth = useAuthStore()
const expenses = useExpensesStore()
const serviceCategoriesStore = useServiceCategoriesStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  amount: '',
  description: '',
  expense_date: new Date().toISOString().split('T')[0],
  category: 'factory' as ExpenseCategory,
  service_category: null as number | null,
})

function resetForm() {
  editingId.value = null
  form.amount = ''
  form.description = ''
  form.expense_date = new Date().toISOString().split('T')[0]
  form.category = 'factory'
  form.service_category = null
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(expense: Expense) {
  editingId.value = expense.id
  form.amount = expense.amount
  form.description = expense.description
  form.expense_date = expense.expense_date
  form.category = expense.category
  form.service_category = expense.service_category
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
    await Promise.all([expenses.fetchAll(), serviceCategoriesStore.fetchAll()])
  } catch (err) {
    await handleAuthError(err)
  }
}

function applyFilters() {
  expenses.fetchAll().catch(handleAuthError)
}

function clearFilters() {
  expenses.search = ''
  expenses.dateFilter = ''
  expenses.startDateFilter = ''
  expenses.endDateFilter = ''
  expenses.categoryFilter = ''
  expenses.serviceCategoryFilter = null
  applyFilters()
}

async function onSubmit() {
  formError.value = null
  if (!form.amount || Number(form.amount) <= 0) {
    formError.value = 'المبلغ يجب أن يكون أكبر من صفر.'
    return
  }
  if (!form.description.trim()) {
    formError.value = 'الوصف مطلوب.'
    return
  }
  if (!form.expense_date) {
    formError.value = 'تاريخ المصروف مطلوب.'
    return
  }
  if (form.category === 'services' && !form.service_category) {
    formError.value = 'قسم الخدمات مطلوب للمصروفات من نوع خدمات.'
    return
  }

  const payload = {
    amount: form.amount,
    description: form.description.trim(),
    expense_date: form.expense_date,
    category: form.category,
    service_category: form.category === 'services' ? form.service_category : null,
  }

  saving.value = true
  try {
    if (editingId.value) {
      await expenses.update(editingId.value, payload)
    } else {
      await expenses.create(payload)
    }
    closeDialog()
  } catch (err) {
    await handleAuthError(err)
      if (err instanceof ApiError) {
          formError.value = err.message
      } else {
          formError.value = 'فشل الحفظ.'
      }
  } finally {
    saving.value = false
  }
}

async function onDelete(expense: Expense) {
  if (!confirm(`حذف المصروف «${expense.description}» بقيمة ${expense.amount}؟`)) return

  try {
    await expenses.remove(expense.id)
    if (editingId.value === expense.id) closeDialog()
  } catch (err) {
    await handleAuthError(err)
  }
}

const categoryLabel = (cat: string) => {
  if (cat === 'factory') return 'المصنع'
  if (cat === 'salaries') return 'الرواتب'
  if (cat === 'services') return 'الخدمات'
  return cat
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section>
    <header class="page-header">
      <div>
        <h1>إدارة المصروفات</h1>
        <p>متابعة وتلخيص جميع مصروفات المؤسسة</p>
      </div>
      <UiButton @click="openCreate">مصروف جديد</UiButton>
    </header>

    <div class="summary-cards" v-if="expenses.summary">
      <UiCard class="summary-card">
        <h3>إجمالي المصروفات</h3>
        <div class="summary-value">{{ expenses.summary.total_expenses }}</div>
      </UiCard>
      <UiCard class="summary-card">
        <h3>مصروفات المصنع</h3>
        <div class="summary-value">{{ expenses.summary.total_factory }}</div>
      </UiCard>
      <UiCard class="summary-card">
        <h3>الرواتب</h3>
        <div class="summary-value">{{ expenses.summary.total_salaries }}</div>
      </UiCard>
      <UiCard class="summary-card">
        <h3>الخدمات</h3>
        <div class="summary-value">{{ expenses.summary.total_services }}</div>
      </UiCard>
    </div>

    <UiCard class="filter-card">
      <div class="filters">
        <div class="ui-field">
          <UiLabel>بحث الوصف</UiLabel>
          <UiInput v-model="expenses.search" @keyup.enter="applyFilters" placeholder="كلمة بحث..." />
        </div>
        <div class="ui-field">
          <UiLabel>التصنيف</UiLabel>
          <UiSelect v-model="expenses.categoryFilter" @change="applyFilters">
            <option value="">الكل</option>
            <option value="factory">المصنع</option>
            <option value="salaries">الرواتب</option>
            <option value="services">الخدمات</option>
          </UiSelect>
        </div>
        <div class="ui-field" v-if="expenses.categoryFilter === 'services'">
          <UiLabel>قسم الخدمات</UiLabel>
          <UiSelect v-model="expenses.serviceCategoryFilter" @change="applyFilters">
            <option :value="null">الكل</option>
            <option v-for="cat in serviceCategoriesStore.items" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </UiSelect>
        </div>
        <div class="ui-field">
          <UiLabel>تاريخ محدد</UiLabel>
          <UiInput type="date" v-model="expenses.dateFilter" @change="applyFilters" />
        </div>
        <div class="ui-field">
          <UiLabel>من تاريخ</UiLabel>
          <UiInput type="date" v-model="expenses.startDateFilter" @change="applyFilters" />
        </div>
        <div class="ui-field">
          <UiLabel>إلى تاريخ</UiLabel>
          <UiInput type="date" v-model="expenses.endDateFilter" @change="applyFilters" />
        </div>
        <div class="filter-actions">
          <UiButton @click="applyFilters">تصفية</UiButton>
          <UiButton variant="outline" @click="clearFilters">مسح الفلاتر</UiButton>
        </div>
      </div>
    </UiCard>

    <p v-if="expenses.error" class="ui-error">{{ expenses.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>التاريخ</th>
              <th>التصنيف</th>
              <th>الوصف</th>
              <th>المبلغ</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="expenses.loading">
              <td colspan="5" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="expenses.items.length === 0">
              <td colspan="5" class="ui-empty">لا توجد مصروفات.</td>
            </tr>
            <tr v-for="expense in expenses.items" :key="expense.id">
              <td>{{ expense.expense_date }}</td>
              <td>
                {{ categoryLabel(expense.category) }}
                <span v-if="expense.category === 'services' && expense.service_category_name" class="service-badge">
                  ({{ expense.service_category_name }})
                </span>
              </td>
              <td>{{ expense.description }}</td>
              <td>{{ expense.amount }}</td>
              <td>
                <div class="row-actions">
                  <UiButton variant="outline" size="sm" @click="openEdit(expense)">تعديل</UiButton>
                  <UiButton variant="destructive" size="sm" @click="onDelete(expense)">حذف</UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiCard>

    <UiDialog
      v-model:open="dialogOpen"
      :title="editingId ? 'تعديل مصروف' : 'إضافة مصروف'"
      description="أدخل تفاصيل المصروف."
    >
      <form @submit.prevent="onSubmit">
        
        <div class="ui-field">
          <UiLabel html-for="expense-amount">المبلغ</UiLabel>
          <UiInput id="expense-amount" type="number" step="0.01" min="0.01" v-model="form.amount" required />
        </div>

        <div class="ui-field">
          <UiLabel html-for="expense-date">التاريخ</UiLabel>
          <UiInput id="expense-date" type="date" v-model="form.expense_date" required />
        </div>

        <div class="ui-field">
          <UiLabel html-for="expense-category">التصنيف الرئيسي</UiLabel>
          <UiSelect id="expense-category" v-model="form.category" required>
            <option value="factory">المصنع</option>
            <option value="salaries">الرواتب</option>
            <option value="services">الخدمات</option>
          </UiSelect>
        </div>

        <div class="ui-field" v-if="form.category === 'services'">
          <UiLabel html-for="expense-service-category">قسم الخدمات</UiLabel>
          <UiSelect id="expense-service-category" v-model="form.service_category" required>
            <option :value="null" disabled>اختر القسم</option>
            <option v-for="cat in serviceCategoriesStore.items" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </UiSelect>
        </div>

        <div class="ui-field">
          <UiLabel html-for="expense-desc">الوصف</UiLabel>
          <UiTextarea id="expense-desc" v-model="form.description" required :rows="3"></UiTextarea>
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
  </section>
</template>

<style scoped>
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.summary-card {
  padding: 1.5rem;
  text-align: center;
}
.summary-card h3 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.summary-value {
  font-size: 1.5rem;
  font-weight: bold;
  margin-top: 0.5rem;
}
.filter-card {
  margin-bottom: 2rem;
  padding: 1.5rem;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}
.filters .ui-field {
  margin-bottom: 0;
  flex: 1 1 150px;
}
.filter-actions {
  display: flex;
  gap: 0.5rem;
}
.service-badge {
  font-size: 0.8em;
  color: var(--text-muted);
}
</style>
