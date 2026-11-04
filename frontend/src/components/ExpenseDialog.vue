<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { createExpense } from '@/api/expenses'
import ClientPicker from '@/components/ClientPicker.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import { useExpenseCategoriesStore } from '@/stores/expenseCategories'

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()

const lookups = useExpenseCategoriesStore()
const today = () => new Date().toISOString().split('T')[0]

const form = reactive({
  amount: '',
  description: '',
  expense_date: today(),
  main_category: null as number | null,
  category: null as number | null,
  client: '' as number | string,
})
const error = ref<string | null>(null)
const saving = ref(false)
const clientPickerKey = ref(0)

const formCategories = computed(() =>
  lookups.categories.filter((c) => c.main_category === form.main_category),
)

watch(
  () => form.main_category,
  () => {
    if (!formCategories.value.some((c) => c.id === form.category)) form.category = null
  },
)

watch(open, (value) => {
  if (!value) return
  form.amount = ''
  form.description = ''
  form.expense_date = today()
  form.main_category = null
  form.category = null
  form.client = ''
  clientPickerKey.value++
  error.value = null
  void lookups.fetchMainCategories()
  void lookups.fetchCategories(null, 'main_category__name,order_number,name')
})

async function submit() {
  error.value = null
  if (!form.amount || Number(form.amount) <= 0) {
    error.value = 'المبلغ مطلوب.'
    return
  }
  if (!form.category) {
    error.value = 'التصنيف الفرعي مطلوب.'
    return
  }
  if (!form.description.trim()) {
    error.value = 'الوصف مطلوب.'
    return
  }
  saving.value = true
  try {
    await createExpense({
      amount: form.amount,
      description: form.description.trim(),
      expense_date: form.expense_date,
      category: form.category,
      client: form.client === '' ? null : Number(form.client),
    })
    open.value = false
    emit('saved')
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UiDialog v-model:open="open" title="إضافة مصروف" description="أدخل تفاصيل المصروف.">
    <form @submit.prevent="submit">
      <div class="ui-field">
        <UiLabel html-for="exp-amount">المبلغ</UiLabel>
        <UiInput id="exp-amount" v-model="form.amount" type="number" min="0.01" :step="0.01" required />
      </div>
      <div class="ui-field">
        <UiLabel html-for="exp-date">التاريخ</UiLabel>
        <UiInput id="exp-date" v-model="form.expense_date" type="date" required />
      </div>
      <div class="ui-field">
        <UiLabel html-for="exp-main">التصنيف الرئيسي</UiLabel>
        <UiSelect id="exp-main" v-model="form.main_category" required>
          <option :value="null" disabled>اختر التصنيف الرئيسي</option>
          <option v-for="m in lookups.mainCategories" :key="m.id" :value="m.id">{{ m.name }}</option>
        </UiSelect>
      </div>
      <div class="ui-field">
        <UiLabel html-for="exp-cat">التصنيف الفرعي</UiLabel>
        <UiSelect id="exp-cat" v-model="form.category" :disabled="!form.main_category" required>
          <option :value="null" disabled>اختر التصنيف الفرعي</option>
          <option v-for="c in formCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </UiSelect>
      </div>
      <div class="ui-field">
        <UiLabel>العميل (اختياري)</UiLabel>
        <ClientPicker :key="clientPickerKey" v-model="form.client" />
        <UiButton v-if="form.client !== ''" type="button" variant="outline" size="sm" @click="form.client = ''">
          بدون عميل
        </UiButton>
      </div>
      <div class="ui-field">
        <UiLabel html-for="exp-desc">الوصف</UiLabel>
        <UiTextarea id="exp-desc" v-model="form.description" :rows="3" required />
      </div>

      <p v-if="error" class="ui-error">{{ error }}</p>

      <div class="ui-dialog-footer">
        <UiButton type="submit" :disabled="saving">{{ saving ? 'جارٍ الحفظ…' : 'حفظ' }}</UiButton>
        <UiButton type="button" variant="outline" @click="open = false">إلغاء</UiButton>
      </div>
    </form>
  </UiDialog>
</template>
