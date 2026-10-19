import { describe, expect, it } from 'vitest'

import { applyDiscount, computeLineSubtotal, roundMoney } from '../pricing'

describe('pricing', () => {
  it('rounds money to 2 decimals', () => {
    expect(roundMoney(1.005)).toBe(1.01)
    expect(roundMoney(2.499)).toBe(2.5)
  })

  it('fixed ignores quantity and dimensions', () => {
    expect(computeLineSubtotal({ costMethod: 'fixed', unitPrice: 100, quantity: 5 })).toBe(100)
  })

  it('quantity multiplies unit price', () => {
    expect(computeLineSubtotal({ costMethod: 'quantity', unitPrice: 25, quantity: 3 })).toBe(75)
    expect(computeLineSubtotal({ costMethod: 'quantity', unitPrice: 25 })).toBe(0)
  })

  it('two dimensions uses perimeter, needs both sides', () => {
    expect(
      computeLineSubtotal({ costMethod: 'two_dimensions', unitPrice: 5, length: 3, width: 2 }),
    ).toBe(50)
    expect(computeLineSubtotal({ costMethod: 'two_dimensions', unitPrice: 5, length: 3 })).toBe(0)
  })

  it('manual measure overrides dimensions', () => {
    expect(
      computeLineSubtotal({ costMethod: 'two_dimensions', unitPrice: 5, length: 3, width: 2, measure: 4 }),
    ).toBe(20)
    expect(computeLineSubtotal({ costMethod: 'one_dimension', unitPrice: 10, measure: 2.5 })).toBe(25)
  })

  it('discount never goes below zero', () => {
    expect(applyDiscount(100, 30)).toBe(70)
    expect(applyDiscount(100, 500)).toBe(0)
  })
})
