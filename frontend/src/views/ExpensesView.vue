<script setup lang="ts">
import { onMounted, reactive, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { Expense } from '@/api/expenses'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'

import { useAuthStore } from '@/stores/auth'
import { useExpensesStore } from '@/stores/expenses'
import { useClientsStore } from '@/stores/clients'
import { useExpenseCategoriesStore } from '@/stores/expenseCategories'

const auth = useAuthStore()
const expenses = useExpensesStore()
const lookups = useExpenseCategoriesStore()
const clientsStore = useClientsStore()
const router = useRouter()

const CATEGORY_ORDERING = 'main_category__name,order_number,name'

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  amount: '',
  description: '',
  expense_date: new Date().toISOString().split('T')[0],
  main_category: null as number | null,
  category: null as number | null,
  client: null as number | null,
})

const formCategories = computed(() =>
  lookups.categories.filter((c) => c.main_category === form.main_category),
)
const filterCategories = computed(() =>
  lookups.categories.filter(
    (c) =>
      expenses.mainCategoryFilter == null || c.main_category === expenses.mainCategoryFilter,
  ),
)
const categoryButtons = computed(() => filterCategories.value.filter((c) => c.is_shown))

function selectCategory(id: number | null) {
  expenses.categoryFilter = id
  applyFilters()
}

watch(
  () => form.main_category,
  () => {
    if (!formCategories.value.some((c) => c.id === form.category)) form.category = null
  },
)

function resetForm() {
  editingId.value = null
  form.amount = ''
  form.description = ''
  form.expense_date = new Date().toISOString().split('T')[0]
  form.main_category = null
  form.category = null
  form.client = null
  formError.value = null
}

function openCreate() {
  resetForm()
  const selected = lookups.categories.find((c) => c.id === expenses.categoryFilter)
  if (selected) {
    form.main_category = selected.main_category
    form.category = selected.id
  } else if (expenses.mainCategoryFilter != null) {
    form.main_category = expenses.mainCategoryFilter
  }
  dialogOpen.value = true
}

function openEdit(expense: Expense) {
  editingId.value = expense.id
  form.amount = expense.amount
  form.description = expense.description
  form.expense_date = expense.expense_date
  form.main_category = expense.main_category
  form.category = expense.category
  form.client = expense.client
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
    await Promise.all([
      expenses.fetchAll(),
      lookups.fetchMainCategories(),
      lookups.fetchCategories(null, CATEGORY_ORDERING),
      clientsStore.fetchAll(),
    ])
  } catch (err) {
    await handleAuthError(err)
  }
}

function onMainFilterChange() {
  expenses.categoryFilter = null
  applyFilters()
}

function applyFilters() {
  expenses.page = 1
  expenses.fetchAll().catch(handleAuthError)
}

const totalPages = computed(() =>
  Math.max(1, Math.ceil(expenses.totalCount / expenses.pageSize)),
)

function goToPage(p: number) {
  if (p < 1 || p > totalPages.value || p === expenses.page) return
  expenses.page = p
  expenses.fetchAll().catch(handleAuthError)
}

function clearFilters() {
  expenses.search = ''
  expenses.dateFilter = ''
  expenses.startDateFilter = ''
  expenses.endDateFilter = ''
  expenses.mainCategoryFilter = null
  expenses.categoryFilter = null
  expenses.clientFilter = null
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
  if (!form.category) {
    formError.value = 'التصنيف الفرعي مطلوب.'
    return
  }

  const payload = {
    amount: form.amount,
    description: form.description.trim(),
    expense_date: form.expense_date,
    category: form.category,
    client: form.client,
  }

  saving.value = true
  try {
    if (editingId.value) {
      await expenses.update(editingId.value, payload)
    } else {
      await expenses.create(payload)
    }
    void lookups.fetchCategories(null, CATEGORY_ORDERING)
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
    void lookups.fetchCategories(null, CATEGORY_ORDERING)
    if (editingId.value === expense.id) closeDialog()
  } catch (err) {
    await handleAuthError(err)
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
      <UiCard
        v-for="row in expenses.summary.by_main_category"
        :key="row.main_category"
        class="summary-card"
      >
        <h3>{{ row.main_category_name }}</h3>
        <div class="summary-value">{{ row.total }}</div>
      </UiCard>
    </div>

    <div class="category-tabs">
      <UiButton
        :variant="expenses.categoryFilter == null ? 'default' : 'outline'"
        @click="selectCategory(null)"
      >
        الكل
      </UiButton>
      <UiButton
        v-for="c in categoryButtons"
        :key="c.id"
        :variant="expenses.categoryFilter === c.id ? 'default' : 'outline'"
        @click="selectCategory(c.id)"
      >
        {{ c.name }} ({{ c.expenses_count }})
      </UiButton>
    </div>

    <UiCard class="filter-card">
      <div class="filters">
        <div class="ui-field">
          <UiLabel>بحث الوصف</UiLabel>
          <UiInput v-model="expenses.search" @keyup.enter="applyFilters" placeholder="كلمة بحث..." />
        </div>
        <div class="ui-field">
          <UiLabel>التصنيف الرئيسي</UiLabel>
          <UiSelect v-model="expenses.mainCategoryFilter" @change="onMainFilterChange">
            <option :value="null">الكل</option>
            <option v-for="m in lookups.mainCategories" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </UiSelect>
        </div>
        <div class="ui-field">
          <UiLabel>التصنيف الفرعي</UiLabel>
          <UiSelect v-model="expenses.categoryFilter" @change="applyFilters">
            <option :value="null">الكل</option>
            <option v-for="c in filterCategories" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </UiSelect>
        </div>
        <div class="ui-field">
          <UiLabel>العميل</UiLabel>
          <UiSelect v-model="expenses.clientFilter" @change="applyFilters">
            <option :value="null">الكل</option>
            <option v-for="t in clientsStore.items" :key="t.id" :value="t.id">
              {{ t.name }}
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
              <th>#</th>
              <th>التاريخ</th>
              <th>التصنيف الفرعي</th>
              <th>العميل</th>
              <th>الوصف</th>
              <th>المبلغ</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="expenses.loading">
              <td colspan="7" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="expenses.items.length === 0">
              <td colspan="7" class="ui-empty">لا توجد مصروفات.</td>
            </tr>
            <tr v-for="(expense, i) in expenses.items" :key="expense.id">
              <td>{{ (expenses.page - 1) * expenses.pageSize + i + 1 }}</td>
              <td>{{ expense.expense_date }}</td>
              <td>{{ expense.category_name }}</td>
              <td>{{ expense.client_name || '—' }}</td>
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
      <div v-if="totalPages > 1" class="pagination">
        <UiButton variant="outline" size="sm" :disabled="expenses.page <= 1" @click="goToPage(expenses.page - 1)">
          السابق
        </UiButton>
        <span>صفحة {{ expenses.page }} من {{ totalPages }} ({{ expenses.totalCount }})</span>
        <UiButton variant="outline" size="sm" :disabled="expenses.page >= totalPages" @click="goToPage(expenses.page + 1)">
          التالي
        </UiButton>
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
          <UiLabel html-for="expense-main-category">التصنيف الرئيسي</UiLabel>
          <UiSelect id="expense-main-category" v-model="form.main_category" required>
            <option :value="null" disabled>اختر التصنيف الرئيسي</option>
            <option v-for="m in lookups.mainCategories" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </UiSelect>
        </div>

        <div class="ui-field">
          <UiLabel html-for="expense-category">التصنيف الفرعي</UiLabel>
          <UiSelect
            id="expense-category"
            v-model="form.category"
            :disabled="!form.main_category"
            required
          >
            <option :value="null" disabled>اختر التصنيف الفرعي</option>
            <option v-for="c in formCategories" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </UiSelect>
        </div>

        <div class="ui-field">
          <UiLabel html-for="expense-client">العميل (اختياري)</UiLabel>
          <UiSelect id="expense-client" v-model="form.client">
            <option :value="null">بدون عميل</option>
            <option v-for="t in clientsStore.items" :key="t.id" :value="t.id">
              {{ t.name }}
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
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 0 0.5rem;
}
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
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
</style>
