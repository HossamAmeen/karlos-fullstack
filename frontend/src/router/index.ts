import { createRouter, createWebHistory } from 'vue-router'

import { getAccessToken } from '@/api/client'
import ClientsView from '@/views/ClientsView.vue'
import ClientStatementView from '@/views/ClientStatementView.vue'
import InvoiceEditorView from '@/views/InvoiceEditorView.vue'
import InvoicesView from '@/views/InvoicesView.vue'
import LoginView from '@/views/LoginView.vue'
import ServiceCategoriesView from '@/views/ServiceCategoriesView.vue'
import ServicesView from '@/views/ServicesView.vue'
import ExpenseCategoriesView from '@/views/ExpenseCategoriesView.vue'
import ExpenseMainCategoriesView from '@/views/ExpenseMainCategoriesView.vue'
import ExpensesView from '@/views/ExpensesView.vue'
import StatisticsView from '@/views/StatisticsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      redirect: { name: 'clients' },
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: StatisticsView,
    },
    {
      path: '/clients',
      name: 'clients',
      component: ClientsView,
    },
    {
      path: '/clients/:id',
      name: 'client-statement',
      component: ClientStatementView,
      props: true,
    },
    {
      path: '/service-categories',
      name: 'service-categories',
      component: ServiceCategoriesView,
    },
    {
      path: '/services',
      name: 'services',
      component: ServicesView,
    },
    {
      path: '/invoices',
      name: 'invoices',
      component: InvoicesView,
    },
    {
      path: '/invoices/new',
      name: 'invoice-new',
      component: InvoiceEditorView,
    },
    {
      path: '/invoices/:id',
      name: 'invoice-edit',
      component: InvoiceEditorView,
      props: true,
    },
    {
      path: '/expenses',
      name: 'expenses',
      component: ExpensesView,
    },
    {
      path: '/expense-main-categories',
      name: 'expense-main-categories',
      component: ExpenseMainCategoriesView,
    },
    {
      path: '/expense-categories',
      name: 'expense-categories',
      component: ExpenseCategoriesView,
    },
  ],
})

router.beforeEach((to) => {
  const isPublic = Boolean(to.meta.public)
  const authenticated = Boolean(getAccessToken())

  if (!isPublic && !authenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'login' && authenticated) {
    return { name: 'clients' }
  }

  return true
})

export default router
