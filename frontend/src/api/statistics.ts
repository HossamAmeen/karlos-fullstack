import { apiFetch } from './client'

export interface PeriodStatistics {
  invoices: string
  expenses: string
  profit: string
}

export interface Statistics {
  total_invoices: string
  total_expenses: string
  current_money: string
  month: PeriodStatistics
  year: PeriodStatistics
}

export function getStatistics() {
  return apiFetch<Statistics>('/api/v1/statistics/')
}
