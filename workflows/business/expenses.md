# Expenses Business Rules

Hierarchy: **ExpenseMainCategory** (e.g. المصنع, الرواتب) → **ExpenseCategory** (e.g. كهرباء, غاز, إيجار / عمال, مديرين) → **Expense**. An expense may optionally reference a **Client** (existing `clients` app).

All models inherit audit fields + soft delete from `BaseModel`.

## Entities

### ExpenseMainCategory (`/api/v1/expense-main-categories/`)

| Field | Type | Notes |
|-------|------|-------|
| id | integer | PK |
| name | string | required, unique among active rows |
| categories_count | integer | read-only, number of active sub-categories |

### ExpenseCategory (`/api/v1/expense-categories/`)

| Field | Type | Notes |
|-------|------|-------|
| id | integer | PK |
| main_category | integer (FK) | required |
| main_category_name | string | read-only |
| name | string | required, unique per main category among active rows |
| order_number | integer | default 0; sorts the filter buttons on the expenses page |
| is_shown | boolean | default true; whether the category appears as a filter button on the expenses page |
| expenses_count | integer | read-only, number of active expenses |

Filters: `main_category`, `name`, `is_shown`; search on name / main category name.

Retrieve (`GET /api/v1/expense-categories/{id}/`) additionally returns `total_amount` and `last_expenses` (latest 5: id, amount, description, expense_date, client_name). The list endpoint does not include them. The categories page "المصروفات" button links to `/expenses?main_category=&category=`, which pre-applies those filters.

### Expense (`/api/v1/expenses/`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | integer | auto | |
| amount | decimal | yes | strictly > 0 |
| description | string | yes | |
| expense_date | date | yes | |
| category | integer (FK) | yes | `ExpenseCategory` |
| category_name, main_category, main_category_name | read-only | | derived from `category`; the list shows the main category dynamically |
| client | integer (FK) | no | optional `Client` |
| client_name | string | read-only | |

Filters: `date`, `start_date`, `end_date`, `main_category`, `category`, `client`; search on description.

## Rules

1. Every authenticated user can CRUD all three expense resources.
2. Delete is a **soft delete**. A main category with active sub-categories, or a category with expenses, cannot be deleted (HTTP 400).
3. `Expense.amount` must be greater than zero.
4. Audit fields are read-only in the API.
5. The old static `category` enum (`factory`/`salaries`/`services`) and `service_category` were removed; migration `0002` deleted all pre-existing expenses.

## Summary — `GET /api/v1/expenses/summary/`

Respects the same filters as the list. Response:

```json
{
  "total_expenses": "150.00",
  "by_main_category": [
    {"main_category": 1, "main_category_name": "المصنع", "total": "100.00"}
  ]
}
```

## Frontend

Sidebar has a collapsible **المصروفات** group: الرئيسية (`/expense-main-categories`), الفرعية (`/expense-categories`), المصروفات (`/expenses`).
