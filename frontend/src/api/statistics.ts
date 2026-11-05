import { apiFetch } from './client'

export interface PeriodStatistics {
  invoices: string
  expenses: string
  profit: string
}

export interface SeriesPoint {
  date: string
  invoices: string
  payments: string
  expenses: string
}

export interface RangeStatistics {
  date_from: string
  date_to: string
  invoices: string
  payments: string
  expenses: string
  profit: string
  group: 'day' | 'month'
  series: SeriesPoint[]
}

export interface Statistics {
  period: RangeStatistics
  total_invoices: string
  total_expenses: string
  today: { date: string; payments: string; expenses: string; cash: string }
  month: PeriodStatistics
  year: PeriodStatistics
}

export function getStatistics(params: { date_from?: string; date_to?: string } = {}) {
  const qs = new URLSearchParams()
  if (params.date_from) qs.set('date_from', params.date_from)
  if (params.date_to) qs.set('date_to', params.date_to)
  const q = qs.toString()
  return apiFetch<Statistics>(`/api/v1/statistics/${q ? `?${q}` : ''}`)
}
