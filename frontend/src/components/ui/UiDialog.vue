<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  title: string
  description?: string
  /** When true, Escape and backdrop clicks do not close the dialog. */
  persistent?: boolean
}>()

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && open.value && !props.persistent) {
    open.value = false
  }
}

function onBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget && !props.persistent) {
    open.value = false
  }
}

watch(open, (value) => {
  document.body.style.overflow = value ? 'hidden' : ''
})

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="ui-dialog-backdrop" @click="onBackdropClick">
      <div class="ui-dialog" role="dialog" aria-modal="true" :aria-label="title">
        <header class="ui-dialog-header">
          <h2 class="ui-dialog-title">{{ title }}</h2>
          <p v-if="description" class="ui-dialog-description">{{ description }}</p>
        </header>
        <slot />
        <footer v-if="$slots.footer" class="ui-dialog-footer">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>
