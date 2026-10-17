<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { Client } from '@/api/clients'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import { useAuthStore } from '@/stores/auth'
import { useClientsStore } from '@/stores/clients'

const auth = useAuthStore()
const clients = useClientsStore()
const router = useRouter()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formError = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  phone: '',
  email: '',
  note: '',
})

function resetForm() {
  editingId.value = null
  form.name = ''
  form.phone = ''
  form.email = ''
  form.note = ''
  formError.value = null
}

function openCreate() {
  resetForm()
  dialogOpen.value = true
}

function openEdit(client: Client) {
  editingId.value = client.id
  form.name = client.name
  form.phone = client.phone
  form.email = client.email
  form.note = client.note
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
    await clients.fetchAll()
  } catch (err) {
    await handleAuthError(err)
  }
}

async function onSubmit() {
  formError.value = null
  if (!form.name.trim() || !form.phone.trim()) {
    formError.value = 'الاسم ورقم الهاتف مطلوبان.'
    return
  }

  const payload = {
    name: form.name.trim(),
    phone: form.phone.trim(),
    email: form.email.trim(),
    note: form.note.trim(),
  }

  saving.value = true
  try {
    if (editingId.value) {
      await clients.update(editingId.value, payload)
    } else {
      await clients.create(payload)
    }
    closeDialog()
    await clients.fetchAll()
  } catch (err) {
    await handleAuthError(err)
    formError.value = err instanceof ApiError ? 'تعذّر حفظ العميل.' : 'فشل الحفظ.'
  } finally {
    saving.value = false
  }
}

async function onDelete(client: Client) {
  if (!confirm(`حذف العميل «${client.name}»؟`)) return
  try {
    await clients.remove(client.id)
    if (editingId.value === client.id) closeDialog()
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
        <h1>العملاء</h1>
        <p>إدارة قائمة العملاء</p>
      </div>
      <UiButton @click="openCreate">عميل جديد</UiButton>
    </header>

    <p v-if="clients.error" class="ui-error">{{ clients.error }}</p>

    <UiCard>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>الاسم</th>
              <th>الهاتف</th>
              <th>البريد</th>
              <th>ملاحظات</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="clients.loading">
              <td colspan="5" class="ui-empty">جارٍ التحميل…</td>
            </tr>
            <tr v-else-if="clients.items.length === 0">
              <td colspan="5" class="ui-empty">لا يوجد عملاء بعد.</td>
            </tr>
            <tr v-for="client in clients.items" :key="client.id">
              <td>{{ client.name }}</td>
              <td>{{ client.phone }}</td>
              <td>{{ client.email || '—' }}</td>
              <td>{{ client.note || '—' }}</td>
              <td>
                <div class="row-actions">
                  <UiButton
                    variant="outline"
                    size="sm"
                    @click="router.push({ name: 'client-statement', params: { id: client.id } })"
                  >
                    كشف حساب
                  </UiButton>
                  <UiButton variant="outline" size="sm" @click="openEdit(client)">تعديل</UiButton>
                  <UiButton variant="destructive" size="sm" @click="onDelete(client)">حذف</UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiCard>

    <UiDialog
      v-model:open="dialogOpen"
      :title="editingId ? 'تعديل عميل' : 'عميل جديد'"
      description="أدخل بيانات العميل ثم احفظ."
    >
      <form @submit.prevent="onSubmit">
        <div class="ui-field">
          <UiLabel html-for="client-name">الاسم</UiLabel>
          <UiInput id="client-name" v-model="form.name" required />
        </div>
        <div class="ui-field">
          <UiLabel html-for="client-phone">رقم الهاتف</UiLabel>
          <UiInput id="client-phone" v-model="form.phone" required />
        </div>
        <div class="ui-field">
          <UiLabel html-for="client-email">البريد الإلكتروني</UiLabel>
          <UiInput id="client-email" v-model="form.email" type="email" />
        </div>
        <div class="ui-field">
          <UiLabel html-for="client-note">ملاحظات</UiLabel>
          <UiTextarea id="client-note" v-model="form.note" :rows="3" />
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
