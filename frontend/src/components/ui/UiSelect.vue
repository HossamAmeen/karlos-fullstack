<script setup lang="ts">
defineProps<{
  id?: string
  required?: boolean
  disabled?: boolean
}>()

const model = defineModel<string | number | null>({ default: '' })
</script>

<template>
  <select
    :id="id"
    v-model="model"
    class="ui-select"
    :required="required"
    :disabled="disabled"
  >
    <slot />
  </select>
</template>
