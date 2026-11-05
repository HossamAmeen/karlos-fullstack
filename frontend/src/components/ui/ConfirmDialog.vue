<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { confirmState as s, settleConfirm } from '@/utils/confirm'

function onKey(e: KeyboardEvent) {
  if (!s.open) return
  if (e.key === 'Escape') settleConfirm(false)
  if (e.key === 'Enter') settleConfirm(true)
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <Transition name="cf">
      <div v-if="s.open" class="cf-backdrop" @click.self="settleConfirm(false)">
        <div class="cf-box" role="alertdialog" aria-modal="true" :aria-label="s.title" dir="rtl">
          <span class="cf-icon" :data-tone="s.tone">
            <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <template v-if="s.tone === 'danger'">
                <path d="M3 6h18" />
                <path d="M8 6V4h8v2" />
                <path d="M19 6l-1 14H6L5 6" />
                <path d="M10 11v5M14 11v5" />
              </template>
              <template v-else>
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v4M12 16h.01" />
              </template>
            </svg>
          </span>
          <h2 class="cf-title">{{ s.title }}</h2>
          <p class="cf-message">{{ s.message }}</p>
          <div class="cf-actions">
            <button type="button" class="cf-btn cf-cancel" @click="settleConfirm(false)">
              {{ s.cancelText }}
            </button>
            <button
              type="button"
              class="cf-btn cf-ok"
              :data-tone="s.tone"
              autofocus
              @click="settleConfirm(true)"
            >
              {{ s.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cf-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(15 23 42 / 0.45);
  backdrop-filter: blur(4px);
}
.cf-box {
  width: min(24rem, 100%);
  display: grid;
  justify-items: center;
  gap: 0.5rem;
  padding: 1.5rem 1.25rem 1.25rem;
  text-align: center;
  background: hsl(var(--card, 0 0% 100%));
  color: hsl(var(--foreground, 222 47% 11%));
  border: 1px solid hsl(var(--border));
  border-radius: 1.25rem;
  box-shadow: 0 24px 60px rgb(0 0 0 / 0.25);
}
.cf-icon {
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background: #3b82f620;
  color: #3b82f6;
}
.cf-icon[data-tone='danger'] {
  background: #ef444420;
  color: #ef4444;
}
.cf-title {
  margin: 0.4rem 0 0;
  font-size: 1.15rem;
  font-weight: 700;
}
.cf-message {
  margin: 0;
  line-height: 1.7;
  color: hsl(var(--muted-foreground));
  font-size: 0.95rem;
}
.cf-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
  width: 100%;
  margin-top: 0.9rem;
}
.cf-btn {
  padding: 0.65rem 1rem;
  font: inherit;
  font-weight: 600;
  border: 1px solid transparent;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: transform 0.1s, filter 0.15s, background 0.15s;
}
.cf-btn:active {
  transform: scale(0.97);
}
.cf-cancel {
  background: hsl(var(--muted, 0 0% 96%));
  color: hsl(var(--foreground, 222 47% 11%));
  border-color: hsl(var(--border));
}
.cf-cancel:hover {
  filter: brightness(0.96);
}
.cf-ok {
  color: #fff;
  background: #2563eb;
}
.cf-ok[data-tone='danger'] {
  background: #dc2626;
}
.cf-ok:hover {
  filter: brightness(1.08);
}
.cf-ok:focus-visible,
.cf-cancel:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
.cf-enter-active,
.cf-leave-active {
  transition: opacity 0.15s ease;
}
.cf-enter-active .cf-box,
.cf-leave-active .cf-box {
  transition: transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1.2);
}
.cf-enter-from,
.cf-leave-to {
  opacity: 0;
}
.cf-enter-from .cf-box {
  transform: scale(0.9) translateY(8px);
}
</style>
