<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useRouter } from 'vue-router'

import UiButton from '@/components/ui/UiButton.vue'
import { useAuthStore } from '@/stores/auth'
import { APP_VERSION } from '@/version'

const auth = useAuthStore()
const router = useRouter()

const navItems = [
  { name: 'clients', to: '/clients', label: 'العملاء' },
  { name: 'service-categories', to: '/service-categories', label: 'الخدمات الرئيسية' },
  { name: 'services', to: '/services', label: 'الخدمات' },
  { name: 'invoices', to: '/invoices', label: 'الفواتير' },
  { name: 'expenses', to: '/expenses', label: 'المصروفات' },
] as const

async function onLogout() {
  auth.logout()
  await router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell" dir="rtl" :class="{ auth: auth.isAuthenticated }">
    <aside v-if="auth.isAuthenticated" class="sidebar">
      <div class="sidebar-top">
        <div class="brand">
          <p class="brand-title">لوحة التحكم</p>
          <p class="brand-subtitle">لوحة المحترف</p>
        </div>

        <nav class="nav" aria-label="التنقل الرئيسي">
          <RouterLink
            v-for="item in navItems"
            :key="item.name"
            :to="item.to"
            class="nav-link"
            exact-active-class="nav-link-active"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <div class="sidebar-bottom">
        <p class="app-version" aria-label="إصدار التطبيق">{{ APP_VERSION }}</p>
        <UiButton variant="outline" class="logout-btn" @click="onLogout">
          تسجيل الخروج
        </UiButton>
      </div>
    </aside>

    <main class="content" :class="{ narrow: !auth.isAuthenticated }">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-shell.auth {
  display: grid;
  grid-template-columns: 1fr;
}

.sidebar {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 40;
  width: 16rem;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.5rem 1rem;
  background: hsl(var(--sidebar));
  border-left: 1px solid hsl(var(--sidebar-border));
}

.brand {
  padding: 0.25rem 0.5rem 1.5rem;
  border-bottom: 1px solid hsl(var(--border));
  margin-bottom: 1rem;
}

.brand-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: hsl(var(--foreground));
}

.brand-subtitle {
  margin: 0.15rem 0 0;
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
}

.nav {
  display: grid;
  gap: 0.35rem;
}

.nav-link {
  display: block;
  padding: 0.65rem 0.85rem;
  border-radius: calc(var(--radius) - 2px);
  color: hsl(var(--muted-foreground));
  font-weight: 600;
  font-size: 0.925rem;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-link:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

.nav-link-active {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.nav-link-active:hover {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.sidebar-bottom {
  padding-top: 1rem;
  border-top: 1px solid hsl(var(--border));
  display: grid;
  gap: 0.65rem;
}

.app-version {
  margin: 0;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: hsl(var(--muted-foreground));
}

.logout-btn {
  width: 100%;
}

.content {
  min-height: 100vh;
  padding: 1.5rem;
}

.app-shell.auth .content {
  margin-right: 16rem;
  width: calc(100% - 16rem);
  max-width: none;
}

.content.narrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

@media (max-width: 900px) {
  .sidebar {
    position: sticky;
    width: 100%;
    height: auto;
    border-left: none;
    border-bottom: 1px solid hsl(var(--sidebar-border));
  }

  .sidebar-top {
    display: grid;
    gap: 0.75rem;
  }

  .brand {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0.25rem;
  }

  .nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .sidebar-bottom {
    margin-top: 0.75rem;
  }

  .app-shell.auth .content {
    margin-right: 0;
    width: 100%;
  }
}
</style>
