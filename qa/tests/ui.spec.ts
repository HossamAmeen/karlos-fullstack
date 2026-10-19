import { expect, test, type Page } from '@playwright/test'

const USER = process.env.QA_USER ?? '01010079798'
const PASS = process.env.QA_PASS ?? 'admin'
const TAG = `QA-AUTO-${Date.now()}`

const PAGES: Array<[string, string, string]> = [
  ['Statistics', '/statistics', 'الإحصائيات'],
  ['Clients', '/clients', 'العملاء'],
  ['Service categories', '/service-categories', 'الخدمات'],
  ['Services', '/services', 'الخدمات'],
  ['Invoices', '/invoices', 'الفواتير'],
  ['New invoice', '/invoices/new', 'فاتورة'],
  ['Expenses', '/expenses', 'المصروفات'],
  ['Expense main categories', '/expense-main-categories', ''],
  ['Expense categories', '/expense-categories', ''],
]

async function login(page: Page, user = USER, pass = PASS) {
  await page.goto('/login')
  await page.locator('#username').fill(user)
  await page.locator('#password').fill(pass)
  await page.getByRole('button', { name: 'تسجيل الدخول' }).click()
  if (pass === PASS) await expect(page.locator('.sidebar, .menu-toggle').first()).toBeVisible()
}

function watch(page: Page) {
  const problems: string[] = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => {
    if (m.type() === 'error') problems.push(`console: ${m.text()}`)
  })
  page.on('response', (r) => {
    if (r.status() >= 404 && r.status() !== 409) problems.push(`HTTP ${r.status()} ${r.url()}`)
    if (r.url().includes('/api/') && r.status() >= 500) problems.push(`${r.status()} ${r.url()}`)
  })
  return problems
}

test.describe('Authentication', () => {
  test('login page renders with version', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.locator('.app-version')).toHaveText(/v\d+\.\d+\.\d+/)
  })

  test('wrong password shows an error and stays on login', async ({ page }) => {
    await login(page, USER, 'definitely-wrong')
    await expect(page.locator('.ui-error')).toContainText('اسم المستخدم أو كلمة المرور خطأ')
    await expect(page).toHaveURL(/\/login/)
  })

  test('empty form is blocked by validation', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click()
    await expect(page).toHaveURL(/\/login/)
  })

  test('valid login lands on the app and logout returns to login', async ({ page }) => {
    await login(page)
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.locator('.sidebar')).toBeVisible()
    await page.getByRole('button', { name: 'تسجيل الخروج' }).click()
    await expect(page).toHaveURL(/\/login/)
  })

  for (const [, path] of PAGES) {
    test(`anonymous ${path} redirects to login`, async ({ page }) => {
      await page.goto(path)
      await expect(page).toHaveURL(/\/login/)
    })
  }
})

test.describe('Pages (authenticated)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await expect(page.locator('.sidebar')).toBeVisible()
  })

  for (const [name, path, heading] of PAGES) {
    test(`${name} loads without errors`, async ({ page }) => {
      const problems = watch(page)
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      await expect(page.locator('h1').first()).toBeVisible()
      if (heading) await expect(page.locator('h1').first()).toContainText(heading)
      expect(problems).toEqual([])
    })
  }

  test('sidebar navigation reaches every section without reload', async ({ page }) => {
    for (const label of ['الإحصائيات', 'العملاء', 'الفواتير']) {
      await page.locator('.nav').getByRole('link', { name: label, exact: true }).click()
      await expect(page.locator('h1').first()).toBeVisible()
    }
  })
})

test.describe('Clients CRUD via UI', () => {
  test('create, edit, open statement, delete', async ({ page }) => {
    const problems = watch(page)
    await login(page)
    await page.goto('/clients')
    page.on('dialog', (d) => d.accept())

    await page.getByRole('button', { name: 'عميل جديد' }).click()
    await page.locator('#client-name').fill(TAG)
    await page.locator('#client-phone').fill(`0${Date.now().toString().slice(-10)}`)
    await page.getByRole('button', { name: 'حفظ' }).click()
    const row = page.locator('tr', { hasText: TAG })
    await expect(row).toBeVisible()

    await row.getByRole('button', { name: 'تعديل' }).click()
    await page.locator('#client-note').fill('edited by QA')
    await page.getByRole('button', { name: 'تحديث' }).click()
    await expect(page.locator('tr', { hasText: TAG })).toContainText('edited by QA')

    await row.getByRole('button', { name: 'كشف حساب' }).click()
    await expect(page).toHaveURL(/\/clients\/\d+/)
    await expect(page.locator('h1').first()).toBeVisible()
    await expect(page.locator('.stat-value').first()).toBeVisible()
    await page.waitForLoadState('networkidle')
    await page.goBack()

    await page.locator('tr', { hasText: TAG }).getByRole('button', { name: 'حذف' }).click()
    await expect(page.locator('tr', { hasText: TAG })).toHaveCount(0)
    expect(problems.filter((p) => !p.includes('400'))).toEqual([])
  })

  test('duplicate phone is rejected', async ({ page }) => {
    await login(page)
    await page.goto('/clients')
    page.on('dialog', (d) => d.accept())
    const phone = `0${Date.now().toString().slice(-10)}`
    for (const n of [`${TAG}-a`, `${TAG}-b`]) {
      await page.getByRole('button', { name: 'عميل جديد' }).click()
      await page.locator('#client-name').fill(n)
      await page.locator('#client-phone').fill(phone)
      await page.getByRole('button', { name: 'حفظ' }).click()
      if (n.endsWith('-b')) await expect(page.locator('.ui-error').first()).toBeVisible()
      else await expect(page.locator('tr', { hasText: n })).toBeVisible()
    }
    await page.getByRole('button', { name: 'إلغاء' }).click()
    await page.locator('tr', { hasText: `${TAG}-a` }).getByRole('button', { name: 'حذف' }).click()
    await expect(page.locator('tr', { hasText: `${TAG}-a` })).toHaveCount(0)
  })
})

test.describe('Responsive', () => {
  test.use({ viewport: { width: 375, height: 700 } })
  test('mobile: menu toggle works and no horizontal page scroll', async ({ page }) => {
    await login(page)
    await page.goto('/statistics')
    await page.getByLabel('القائمة').click()
    await expect(page.locator('.sidebar.open')).toBeVisible()
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow).toBeLessThanOrEqual(1)
  })
})
