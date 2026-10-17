<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { ExpenseCategory } from '@/api/expenseCategories'
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
const form = reactive({ name: '', main_category: null as number | null })

function resetForm() {
  editingId.value = null
  form.name = ''
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
    const payload = { name: form.name.trim(), main_category: form.main_category }
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

onMounted(() => {
  store.fetchMainCategories().catch(handleAuthError)
  void reload()
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

    <UiCard class="filter-card">
      <div class="ui-field">
        <UiLabel>التصنيف الرئيسي</UiLabel>
        <UiSelect v-model="mainFilter" @change="reload">
          <option :value="null">الكل</option>
          <option v-for="m in store.mainCategories" :key="m.id" :value="m.id">
            {{ m.name }}
          </option>
        </UiSelect>
      </div>
    </UiCard>

    <p v-if="store.error" class="ui-error">{{ store.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>الاسم</th>
              <th>التصنيف الرئيسي</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.loading">
              <td colspan="3" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="store.categories.length === 0">
              <td colspan="3" class="ui-empty">لا توجد تصنيفات فرعية.</td>
            </tr>
            <tr v-for="item in store.categories" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.main_category_name }}</td>
              <td>
                <div class="row-actions">
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
.filter-card {
  margin-bottom: 1.5rem;
  padding: 1rem 1.5rem;
}
.filter-card .ui-field {
  margin-bottom: 0;
  max-width: 20rem;
}
</style>
