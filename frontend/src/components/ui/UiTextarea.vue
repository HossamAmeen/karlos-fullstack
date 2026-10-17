<script setup lang="ts">
defineProps<{
  id?: string
  placeholder?: string
  rows?: number
  required?: boolean
  disabled?: boolean
}>()

const model = defineModel<string>({ default: '' })
</script>

<template>
  <textarea
    :id="id"
    v-model="model"
    class="ui-textarea"
    :placeholder="placeholder"
    :rows="rows ?? 3"
    :required="required"
    :disabled="disabled"
  />
</template>
