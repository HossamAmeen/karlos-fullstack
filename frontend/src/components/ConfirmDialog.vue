<script setup lang="ts">
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'

/**
 * Professional replacement for window.confirm / window.alert.
 * kind="confirm": two buttons, emits `confirm`.
 * kind="error" | "info": a single acknowledge button.
 */
const open = defineModel<boolean>('open', { default: false })

withDefaults(
  defineProps<{
    title: string
    message: string
    kind?: 'confirm' | 'error' | 'info'
    confirmLabel?: string
    cancelLabel?: string
    okLabel?: string
    danger?: boolean
    busy?: boolean
  }>(),
  {
    kind: 'confirm',
    confirmLabel: 'تأكيد',
    cancelLabel: 'إلغاء',
    okLabel: 'حسنًا',
    danger: false,
    busy: false,
  },
)

const emit = defineEmits<{ confirm: [] }>()
</script>

<template>
  <UiDialog v-model:open="open" :title="title">
    <div class="notice" :data-kind="kind">
      <span class="icon" aria-hidden="true">{{ kind === 'error' ? '!' : kind === 'info' ? 'i' : '?' }}</span>
      <p class="message">{{ message }}</p>
    </div>
    <div class="ui-dialog-footer">
      <template v-if="kind === 'confirm'">
        <UiButton :variant="danger ? 'destructive' : 'default'" :disabled="busy" @click="emit('confirm')">
          {{ busy ? 'جارٍ التنفيذ…' : confirmLabel }}
        </UiButton>
        <UiButton variant="outline" :disabled="busy" @click="open = false">{{ cancelLabel }}</UiButton>
      </template>
      <UiButton v-else @click="open = false">{{ okLabel }}</UiButton>
    </div>
  </UiDialog>
</template>

<style scoped>
.notice {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.25rem 0 1rem;
}
.icon {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  font-weight: 800;
  font-size: 1.1rem;
  background: hsl(var(--muted));
  color: hsl(var(--foreground));
}
.notice[data-kind='error'] .icon {
  background: hsl(0 70% 94%);
  color: hsl(0 65% 40%);
}
.notice[data-kind='confirm'] .icon {
  background: hsl(38 90% 92%);
  color: hsl(30 80% 35%);
}
.message {
  margin: 0;
  line-height: 1.7;
  font-size: 0.98rem;
  white-space: pre-line;
}
</style>
