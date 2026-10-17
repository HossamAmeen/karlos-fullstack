<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { CostMethod, Service } from '@/api/services'
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
const services = useServicesStore()
const categories = useServiceCategoriesStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  service_category: '' as string | number,
  cost: '',
  cost_method: 'two_dimensions' as CostMethod,
  is_fixed_cost: false,
  is_additional_service: false,
  color: '#3b82f6',
})

const hasCategories = computed(() => categories.items.length > 0)

const costMethodLabels: Record<CostMethod, string> = {
  fixed: 'ثابت',
  quantity: 'كمية',
  one_dimension: 'بعد واحد (x×x)',
  two_dimensions: 'بعدين ((x+y)×2)',
}

function resetForm() {
  editingId.value = null
  form.name = ''
  form.service_category = categories.items[0]?.id ?? ''
  form.cost = ''
  form.cost_method = 'two_dimensions'
  form.is_fixed_cost = false
  form.is_additional_service = false
  form.color = '#3b82f6'
  formError.value = null
}

function openCreate() {
  if (!hasCategories.value) return
  resetForm()
  dialogOpen.value = true
}

function openEdit(service: Service) {
  editingId.value = service.id
  form.name = service.name
  form.service_category = service.service_category
  form.cost = service.cost
  form.cost_method = service.cost_method
  form.is_fixed_cost = service.is_fixed_cost
  form.is_additional_service = service.is_additional_service
  form.color = service.color
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
    await Promise.all([services.fetchAll(), categories.fetchAll()])
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
  if (form.service_category === '' || form.service_category == null) {
    formError.value = 'الخدمة الرئيسية مطلوبة.'
    return
  }
  if (!String(form.cost).trim()) {
    formError.value = 'السعر مطلوب.'
    return
  }
  if (!['fixed', 'quantity', 'one_dimension', 'two_dimensions'].includes(form.cost_method)) {
    formError.value = 'اختر طريقة حساب صحيحة.'
    return
  }

  const payload = {
    name: form.name.trim(),
    service_category: Number(form.service_category),
    cost: String(form.cost).trim(),
    cost_method: form.cost_method,
    is_fixed_cost: form.is_fixed_cost,
    is_additional_service: form.is_additional_service,
    color: form.color,
  }

  saving.value = true
  try {
    if (editingId.value) {
      await services.update(editingId.value, payload)
    } else {
      await services.create(payload)
    }
    closeDialog()
    await services.fetchAll()
  } catch (err) {
    await handleAuthError(err)
    formError.value = err instanceof ApiError ? 'تعذّر حفظ الخدمة.' : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}

async function onDelete(service: Service) {
  if (!confirm(`حذف الخدمة «${service.name}»؟`)) return
  try {
    await services.remove(service.id)
    if (editingId.value === service.id) closeDialog()
  } catch (err) {
    await handleAuthError(err)
  }
}

function formatPrice(value: string) {
  const number = Number(value)
  if (Number.isNaN(number)) return value
  return number.toLocaleString('ar-EG')
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section>
    <header class="page-header">
      <div>
        <h1>الخدمات</h1>
        <p>الخدمات التابعة للأقسام الرئيسية</p>
      </div>
      <UiButton :disabled="!hasCategories" @click="openCreate">خدمة جديدة</UiButton>
    </header>

    <p v-if="!categories.loading && !hasCategories" class="notice">
      أضف خدمة رئيسية أولًا من صفحة الخدمات الرئيسية.
    </p>

    <p v-if="services.error" class="ui-error">{{ services.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>اللون</th>
              <th>الاسم</th>
              <th>الخدمة الرئيسية</th>
              <th>السعر</th>
              <th>طريقة الحساب</th>
              <th>سعر ثابت</th>
              <th>خدمة إضافية</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="services.loading">
              <td colspan="8" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="services.items.length === 0">
              <td colspan="8" class="ui-empty">
                {{
                  hasCategories
                    ? 'لا توجد خدمات بعد.'
                    : 'أضف خدمة رئيسية أولًا من صفحة الخدمات الرئيسية.'
                }}
              </td>
            </tr>
            <tr v-for="service in services.items" :key="service.id">
              <td>
                <div
                  class="color-swatch"
                  :style="{ backgroundColor: service.color }"
                  :title="service.color"
                ></div>
              </td>
              <td>{{ service.name }}</td>
              <td>{{ service.service_category_name }}</td>
              <td>{{ formatPrice(service.cost) }}</td>
              <td>{{ costMethodLabels[service.cost_method] }}</td>
              <td>{{ service.is_fixed_cost ? 'نعم' : 'لا' }}</td>
              <td>{{ service.is_additional_service ? 'نعم' : 'لا' }}</td>
              <td>
                <div class="row-actions">
                  <UiButton variant="outline" size="sm" @click="openEdit(service)">تعديل</UiButton>
                  <UiButton variant="destructive" size="sm" @click="onDelete(service)">حذف</UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiCard>

    <UiDialog
      v-model:open="dialogOpen"
      :title="editingId ? 'تعديل خدمة' : 'خدمة جديدة'"
      description="أدخل بيانات الخدمة ثم احفظ."
    >
      <form @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="service-name">الاسم</UiLabel>
          <UiInput id="service-name" v-model="form.name" required />
        </div>
        <div class="ui-field">
          <UiLabel html-for="service-category">الخدمة الرئيسية</UiLabel>
          <UiSelect id="service-category" v-model="form.service_category" required>
            <option disabled value="">اختر الخدمة الرئيسية</option>
            <option v-for="category in categories.items" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </UiSelect>
        </div>
        <div class="ui-field">
          <UiLabel html-for="service-cost">السعر</UiLabel>
          <UiInput id="service-cost" v-model="form.cost" type="number" min="0" step="0.01" required />
        </div>
        <div class="ui-field">
          <UiLabel html-for="service-cost-method">طريقة حساب السعر</UiLabel>
          <UiSelect id="service-cost-method" v-model="form.cost_method" required>
            <option value="fixed">ثابت</option>
            <option value="quantity">كمية</option>
            <option value="one_dimension">بعد واحد (x×x)</option>
            <option value="two_dimensions">بعدين ((x+y)×2)</option>
          </UiSelect>
        </div>
        <div class="ui-field color-field">
          <UiLabel html-for="service-color">اللون</UiLabel>
          <div class="color-picker-wrap">
            <input
              id="service-color"
              v-model="form.color"
              type="color"
              class="color-picker-input"
            />
            <UiInput v-model="form.color" type="text" maxlength="7" class="color-text-input" />
          </div>
        </div>
        <label class="checkbox-field">
          <input v-model="form.is_fixed_cost" type="checkbox" />
          سعر ثابت
        </label>
        <label class="checkbox-field">
          <input v-model="form.is_additional_service" type="checkbox" />
          خدمة إضافية
        </label>

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
.notice {
  margin: 0 0 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  color: hsl(var(--muted-foreground));
  font-size: 0.925rem;
}

.checkbox-field {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.85rem;
  font-size: 0.925rem;
  color: hsl(var(--foreground));
  cursor: pointer;
}

.checkbox-field input {
  width: 1rem;
  height: 1rem;
  accent-color: hsl(var(--primary));
}

.color-swatch {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.375rem;
  border: 1px solid hsl(var(--border));
  cursor: pointer;
}

.color-picker-wrap {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.color-picker-input {
  width: 2.75rem;
  height: 2.75rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  cursor: pointer;
  padding: 0;
}

.color-picker-input::-webkit-color-swatch-wrapper {
  padding: 0.125rem;
}

.color-picker-input::-webkit-color-swatch {
  border: none;
  border-radius: calc(var(--radius) - 2px);
}

.color-text-input {
  flex: 1;
}
</style>
