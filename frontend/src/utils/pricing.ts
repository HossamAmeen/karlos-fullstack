import type { CostMethod } from '@/api/invoices'

export function roundMoney(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

export function computeLineSubtotal(opts: {
  costMethod: CostMethod
  unitPrice: number
  quantity?: number | null
  length?: number | null
  width?: number | null
}): number {
  const { costMethod, unitPrice, quantity, length, width } = opts
  if (costMethod === 'fixed') return roundMoney(unitPrice)
  if (costMethod === 'quantity') return roundMoney(unitPrice * (quantity ?? 0))
  if (costMethod === 'one_dimension') {
    const dim = width ?? length ?? 0
    return roundMoney(unitPrice * dim * dim)
  }
  if (costMethod === 'two_dimensions') {
    if (length == null || width == null) return 0
    return roundMoney(unitPrice * 2 * (length + width))
  }
  return 0
}

export function applyDiscount(amount: number, discount: number): number {
  return roundMoney(Math.max(0, amount - discount))
}
