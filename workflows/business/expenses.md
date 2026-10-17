# Expenses Business Rules

## Entity: Expense

`Expense` inherits shared audit fields from `BaseModel`.

### Business fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | integer | auto | Primary key |
| amount | decimal | yes | Monetary amount, strictly > 0 |
| description | string | yes | Details about the expense |
| expense_date | date | yes | When the expense occurred |
| category | string enum | yes | `factory`, `salaries`, or `services` |
| service_category | integer (FK) | conditional | Required if `category == 'services'` |

### Audit fields (from BaseModel)

Same as ServiceCategory.

## Rules

1. Every authenticated user can list / create / update / delete expenses and service categories.
2. `ServiceCategory.name` is mandatory and unique among **active** categories (`deleted_at IS NULL`).
3. `Expense.amount` must be greater than zero.
4. `Expense.service_category` must reference an active `ServiceCategory` only if `category == 'services'`. Otherwise, it should be null.
5. Soft-deleting a service category does **not** cascade-delete its expenses.
6. Delete is a **soft delete**.
7. Audit fields are **read-only** in the API.
8. List endpoints support search and filtering (by date ranges and categories).
9. Summary API provides dashboard aggregates respecting the same filters.



## API contract — Expense (`/api/v1/expenses/`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/expenses/` | JWT | List active expenses (paginated Limit/Offset) |
| POST | `/api/v1/expenses/` | JWT | Create |
| GET | `/api/v1/expenses/{id}/` | JWT | Retrieve |
| PUT/PATCH | `/api/v1/expenses/{id}/` | JWT | Update |
| DELETE | `/api/v1/expenses/{id}/` | JWT | Soft delete |
| GET | `/api/v1/expenses/summary/` | JWT | Summary dashboard aggregates |
