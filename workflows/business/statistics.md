# Statistics

`GET /api/v1/statistics/` (JWT). Frontend page: `/statistics`.

- **Bills** = `Invoice.total` of **confirmed** invoices, dated by `issue_date`.
- **Expenses** = active `Expense.amount`, dated by `expense_date`.
- `current_money` = total bills − total expenses (all time).
- `month` / `year` = current calendar month / year, each with `invoices`, `expenses`, `profit` (`invoices − expenses`).

```json
{
  "total_invoices": "1500.00",
  "total_expenses": "320.00",
  "current_money": "1180.00",
  "month": { "invoices": "1000.00", "expenses": "200.00", "profit": "800.00" },
  "year": { "invoices": "1500.00", "expenses": "250.00", "profit": "1250.00" }
}
```

The client statement response also carries `total_expenses` (sum of expenses linked to that client). The client details page shows it as a box and has three buttons to switch between invoices, payments and expenses.
