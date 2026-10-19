import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 1,
  workers: 1,
  reporter: [
    ['list'],
    ['json', { outputFile: 'reports/ui-results.json' }],
    ['html', { outputFolder: 'reports/ui-html', open: 'never' }],
  ],
  outputDir: 'reports/ui-artifacts',
  use: {
    baseURL: process.env.QA_FRONT_URL ?? 'https://karlos-front.hossam-ameen.online',
    channel: 'chrome',
    locale: 'ar-EG',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
})
