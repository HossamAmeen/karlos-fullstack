<script setup lang="ts">
defineProps<{
  id?: string
  type?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  min?: string | number
  step?: string | number
  autocomplete?: string
}>()

const model = defineModel<string | number>({ default: '' })
</script>

<template>
  <input
    :id="id"
    v-model="model"
    class="ui-input"
    :type="type ?? 'text'"
    :placeholder="placeholder"
    :required="required"
    :disabled="disabled"
    :min="min"
    :step="step"
    :autocomplete="autocomplete"
  />
</template>
