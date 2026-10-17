<script setup lang="ts">
defineProps<{
  htmlFor?: string
}>()
</script>

<template>
  <label class="ui-label" :for="htmlFor">
    <slot />
  </label>
</template>
