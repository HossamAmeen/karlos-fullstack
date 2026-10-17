<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { ExpenseMainCategory } from '@/api/expenseCategories'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { useAuthStore } from '@/stores/auth'
import { useExpenseCategoriesStore } from '@/stores/expenseCategories'

const auth = useAuthStore()
const store = useExpenseCategoriesStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)
const form = reactive({ name: '' })

function resetForm() {
  editingId.value = null
  form.name = ''
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(item: ExpenseMainCategory) {
  editingId.value = item.id
  form.name = item.name
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

async function onSubmit() {
  formError.value = null
  if (!form.name.trim()) {
    formError.value = 'الاسم مطلوب.'
    return
  }
  saving.value = true
  try {
    const payload = { name: form.name.trim() }
    if (editingId.value) await store.updateMainCategory(editingId.value, payload)
    else await store.createMainCategory(payload)
    closeDialog()
  } catch (err) {
    await handleAuthError(err)
    formError.value = err instanceof ApiError ? err.message : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}

async function onDelete(item: ExpenseMainCategory) {
  if (!confirm(`حذف التصنيف الرئيسي «${item.name}»؟`)) return
  try {
    await store.removeMainCategory(item.id)
  } catch (err) {
    await handleAuthError(err)
    if (err instanceof ApiError) alert(err.message)
  }
}

onMounted(() => {
  store.fetchMainCategories().catch(handleAuthError)
})
</script>

<template>
  <section>
    <header class="page-header">
      <div>
        <h1>التصنيفات الرئيسية للمصروفات</h1>
        <p>مثل: المصنع، الرواتب</p>
      </div>
      <UiButton @click="openCreate">تصنيف رئيسي جديد</UiButton>
    </header>

    <p v-if="store.error" class="ui-error">{{ store.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>الاسم</th>
              <th>عدد التصنيفات الفرعية</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.loading">
              <td colspan="3" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="store.mainCategories.length === 0">
              <td colspan="3" class="ui-empty">لا توجد تصنيفات رئيسية بعد.</td>
            </tr>
            <tr v-for="item in store.mainCategories" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.categories_count }}</td>
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
      :title="editingId ? 'تعديل تصنيف رئيسي' : 'تصنيف رئيسي جديد'"
      description="أدخل اسم التصنيف الرئيسي."
    >
      <form @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="main-category-name">الاسم</UiLabel>
          <UiInput id="main-category-name" v-model="form.name" required />
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
