# Statistics

`GET /api/v1/statistics/` (JWT). Frontend page: `/statistics`.

- **Bills** = `Invoice.total` of **confirmed** invoices, dated by `issue_date`.
- **Expenses** = active `Expense.amount`, dated by `expense_date`.
- `today` = `{date, payments, expenses, cash}` for the current day; `cash` (فلوس الخزنة اليوم) = payments − expenses.
- Optional query `date_from` / `date_to` (`YYYY-MM-DD`); default = current month. Response `period` has `date_from`, `date_to`, `invoices`, `payments` (sum of `Payment.amount` by `paid_at`), `expenses`, `profit`, `group` (`day`, or `month` when range > 62 days) and `series` (per-bucket invoices/payments/expenses for the chart).
- The page filters by year + month (month "all" = whole year; default current year/month), shows the date range in each box, 4 icon boxes (invoices, payments, expenses, profit) and a simple SVG bar chart.
- `month` / `year` = current calendar month / year, each with `invoices`, `expenses`, `profit` (`invoices − expenses`).

```json
{
  "total_invoices": "1500.00",
  "total_expenses": "320.00",
  "today": { "date": "2026-11-05", "payments": "90.00", "expenses": "30.00", "cash": "60.00" },
  "month": { "invoices": "1000.00", "expenses": "200.00", "profit": "800.00" },
  "year": { "invoices": "1500.00", "expenses": "250.00", "profit": "1250.00" }
}
```

The client statement response also carries `total_expenses` (sum of expenses linked to that client). The client details page shows it as a box and has three buttons to switch between invoices, payments and expenses.

Demo data for the chart: `python manage.py seed_statistics` (`--clear` removes it; rows are tagged `[seed-stats]`).
