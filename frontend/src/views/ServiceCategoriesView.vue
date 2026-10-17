<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { ServiceCategory } from '@/api/serviceCategories'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
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
})

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
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(category: ServiceCategory) {
  editingId.value = category.id
  form.name = category.name
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
    await Promise.all([categories.fetchAll(), services.fetchAll()])
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

  const payload = { name: form.name.trim() }

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
              <th>الاسم</th>
              <th>عدد الخدمات</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="categories.loading">
              <td colspan="3" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="categories.items.length === 0">
              <td colspan="3" class="ui-empty">لا توجد خدمات رئيسية بعد.</td>
            </tr>
            <tr v-for="category in categories.items" :key="category.id">
              <td>{{ category.name }}</td>
              <td>{{ servicesCount(category.id) }}</td>
              <td>
                <div class="row-actions">
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
