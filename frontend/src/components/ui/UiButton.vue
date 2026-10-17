<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'
    size?: 'default' | 'sm' | 'icon'
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
  }>(),
  {
    variant: 'default',
    size: 'default',
    type: 'button',
    disabled: false,
  },
)
</script>

<template>
  <button
    :type="type"
    class="ui-btn"
    :class="[
      `ui-btn-${variant}`,
      size === 'sm' ? 'ui-btn-sm' : '',
      size === 'icon' ? 'ui-btn-icon' : '',
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
