export type PaymentMethod = 'cash' | 'instapay' | 'wallet'

export const paymentMethodLabels: Record<PaymentMethod, string> = {
  cash: 'كاش',
  instapay: 'انستا',
  wallet: 'محفظة',
}

export const paymentMethodOptions: { value: PaymentMethod; label: string }[] = [
  { value: 'cash', label: paymentMethodLabels.cash },
  { value: 'instapay', label: paymentMethodLabels.instapay },
  { value: 'wallet', label: paymentMethodLabels.wallet },
]
