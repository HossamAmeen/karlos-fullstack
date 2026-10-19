import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { Component } from 'vue'

import AboutView from '../AboutView.vue'
import ClientStatementView from '../ClientStatementView.vue'
import ClientsView from '../ClientsView.vue'
import ExpenseCategoriesView from '../ExpenseCategoriesView.vue'
import ExpenseMainCategoriesView from '../ExpenseMainCategoriesView.vue'
import ExpensesView from '../ExpensesView.vue'
import InvoiceEditorView from '../InvoiceEditorView.vue'
import InvoicesView from '../InvoicesView.vue'
import LoginView from '../LoginView.vue'
import ServiceCategoriesView from '../ServiceCategoriesView.vue'
import ServicesView from '../ServicesView.vue'
import StatisticsView from '../StatisticsView.vue'

const money = '0.00'
const statement = {
  client: { id: 1, name: 'Ali', phone: '0100', email: '', address: '', note: '' },
  total_charged: money,
  total_deposits: money,
  total_expenses: money,
  balance_due: money,
  invoices: [],
  deposits: [],
}
const statistics = {
  total_invoices: money,
  total_expenses: money,
  current_money: money,
  month: { invoices: money, expenses: money, profit: money },
  year: { invoices: money, expenses: money, profit: money },
}

function respond(url: string) {
  if (url.includes('/statement/')) return statement
  if (url.includes('/statistics/')) return statistics
  if (url.includes('/expenses/summary/')) return { total_expenses: money, by_main_category: [] }
  if (/\/invoices\/\d+\/$/.test(url.split('?')[0])) return null
  return { count: 0, next: null, previous: null, results: [] }
}

const cases: Array<[string, Component, string, Record<string, string>]> = [
  ['Login', LoginView, '/login', {}],
  ['About', AboutView, '/about', {}],
  ['Statistics', StatisticsView, '/statistics', {}],
  ['Clients', ClientsView, '/clients', {}],
  ['ClientStatement', ClientStatementView, '/clients/1', { id: '1' }],
  ['ServiceCategories', ServiceCategoriesView, '/service-categories', {}],
  ['Services', ServicesView, '/services', {}],
  ['Invoices', InvoicesView, '/invoices', {}],
  ['InvoiceEditor (new)', InvoiceEditorView, '/invoices/new', {}],
  ['Expenses', ExpensesView, '/expenses', {}],
  ['ExpenseMainCategories', ExpenseMainCategoriesView, '/expense-main-categories', {}],
  ['ExpenseCategories', ExpenseCategoriesView, '/expense-categories', {}],
]

describe('page smoke tests', () => {
  const calls: string[] = []

  beforeEach(() => {
    calls.length = 0
    setActivePinia(createPinia())
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        calls.push(url)
        const body = respond(url)
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        })
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it.each(cases)('%s renders without errors', async (_name, component, path, props) => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/:pathMatch(.*)*', component }],
    })
    router.push(path)
    await router.isReady()

    const errors: unknown[] = []
    const wrapper = mount(component, {
      props,
      global: {
        plugins: [createPinia(), router],
        config: { errorHandler: (e) => errors.push(e) },
      },
    })
    await flushPromises()

    expect(errors).toEqual([])
    expect(wrapper.html().length).toBeGreaterThan(0)
  })

  it.each(cases.filter(([n]) => !['Login', 'About'].includes(n)))(
    '%s loads its data from the API',
    async (_name, component, path, props) => {
      const router = createRouter({
        history: createMemoryHistory(),
        routes: [{ path: '/:pathMatch(.*)*', component }],
      })
      router.push(path)
      await router.isReady()
      mount(component, { props, global: { plugins: [createPinia(), router] } })
      await flushPromises()
      expect(calls.length).toBeGreaterThan(0)
      expect(calls.every((u) => u.includes('/api/'))).toBe(true)
    },
  )
})
