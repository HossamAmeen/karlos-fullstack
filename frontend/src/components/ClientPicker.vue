<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

import { listClients, type Client } from '@/api/clients'
import UiInput from '@/components/ui/UiInput.vue'

const props = defineProps<{
  modelValue: number | string
  label?: string
  disabled?: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [id: number]
  select: [client: Client]
}>()

const text = ref(props.label ?? '')
const results = ref<Client[]>([])
const open = ref(false)
const loading = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
let requestId = 0

watch(
  () => props.modelValue,
  (value) => {
    if (value === '') text.value = ''
  },
)

watch(
  () => props.label,
  (value) => {
    text.value = value ?? ''
  },
)

async function search(term: string) {
  const current = ++requestId
  loading.value = true
  try {
    const data = await listClients({ search: term.trim() || undefined, limit: 20 })
    if (current === requestId) results.value = data.results
  } catch {
    if (current === requestId) results.value = []
  } finally {
    if (current === requestId) loading.value = false
  }
}

function onInput() {
  open.value = true
  clearTimeout(timer)
  timer = setTimeout(() => void search(text.value), 250)
}

function onFocus() {
  open.value = true
  void search('')
}

function choose(client: Client) {
  text.value = `${client.name} — ${client.phone}`
  open.value = false
  emit('update:modelValue', client.id)
  emit('select', client)
}

function onBlur() {
  // delay so a click on an option registers first
  setTimeout(() => {
    open.value = false
  }, 150)
}

onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div class="client-picker">
    <UiInput
      v-model="text"
      :disabled="disabled"
      placeholder="ابحث بالاسم أو رقم الهاتف..."
      autocomplete="off"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
    />
    <ul v-if="open && !disabled" class="client-picker-list">
      <li v-if="loading" class="muted">جاري البحث...</li>
      <li v-else-if="!results.length" class="muted">لا توجد نتائج</li>
      <li
        v-for="c in results"
        :key="c.id"
        :class="{ active: String(c.id) === String(modelValue) }"
        @mousedown.prevent="choose(c)"
      >
        <strong>{{ c.name }}</strong>
        <span class="muted">{{ c.phone }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.client-picker {
  position: relative;
}
.client-picker-list {
  position: absolute;
  top: calc(100% + 0.25rem);
  right: 0;
  left: 0;
  z-index: 30;
  max-height: 16rem;
  overflow-y: auto;
  margin: 0;
  padding: 0.25rem;
  list-style: none;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px hsl(0 0% 0% / 0.12);
}
.client-picker-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
}
.client-picker-list li:hover,
.client-picker-list li.active {
  background: hsl(var(--muted));
}
.muted {
  color: hsl(var(--muted-foreground));
}
</style>
