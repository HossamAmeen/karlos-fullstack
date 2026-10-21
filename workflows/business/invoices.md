# Invoices, payments & client deposits

## Invoice lifecycle

`draft` → `confirmed` → (optional) `cancelled`

Totals are server-authoritative. Only drafts are editable.

## Pieces (physical items)

An invoice is a list of **pieces**. A piece is one physical item (for example glass `3 × 2`) that can carry **one or more services**, each with its own price.

Example: piece `3 × 2` with area glass + perimeter polish + a fixed install fee.

| Field | Meaning |
|-------|---------|
| `length` / `width` | **Centimetres** (converted to metres, ÷100, when pricing). Shared dimensions for every service on the piece. Required when any service uses `area` or `perimeter`. |
| `quantity` | How many identical pieces. Default `1`. Must be `> 0`. |
| `piece_subtotal` | Sum of service `line_total` values **for one** piece |
| `piece_total` | `piece_subtotal × quantity` |
| `items` | Services applied to this piece |

Invoice `subtotal` = sum of all `piece_total`. Invoice `total` = `subtotal` minus invoice `discount_amount`.

### Piece rules

1. A piece must have at least one service.
2. Dimensions live on the piece, not on each service. Changing `length` / `width` recalculates every service on that piece.
3. When selecting a service in the invoice editor, if piece dimensions (`length` and `width`) are blank, they auto-fill from the service's `default_length` and `default_width` if configured.
4. `area` uses `length × width`. `perimeter` uses `2 × (length + width)`. `length` / `width` are entered in cm and divided by 100 before pricing; `measure` is already in metres.
5. Dimension services (`area` / `perimeter`) accept an optional item-level `measure` (e.g. `30` for `2×(5+10)`). When set, line subtotal = `unit_price × measure`, `length`/`width` are ignored (and not required). The editor pre-fills it from the dimensions and lets the user override it; piece `quantity` (count) then multiplies the piece subtotal.
6. `fixed` and `quantity` services may sit on a piece that also has dimensions; `quantity` on an **item** is still the service count (holes, units), not the piece count.
7. Deleting the last service on a piece deletes the piece.
8. Confirm still requires at least one service (hence at least one piece).

### API — pieces

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/invoices/{id}/pieces/` | Create a piece with one or more services |
| PATCH | `/api/v1/invoices/{id}/pieces/{piece_id}/` | Update dimensions / quantity / notes |
| DELETE | `/api/v1/invoices/{id}/pieces/{piece_id}/` | Soft-delete the piece and its services |
| POST | `/api/v1/invoices/{id}/items/` | Add one service. Omit `piece` to create a new 1-service piece; send `piece` to attach to an existing piece |
| PATCH / DELETE | `/api/v1/invoices/{id}/items/{item_id}/` | Update or remove one service |

#### Create piece payload

```json
{
  "length": "3.000",
  "width": "2.000",
  "quantity": "1.000",
  "notes": "",
  "items": [
    { "service": 1, "unit_price": "10.00" },
    { "service": 2, "unit_price": "5.00" },
    { "service": 3, "quantity": "4" }
  ]
}
```

#### Invoice response (pieces)

```json
{
  "subtotal": "220.00",
  "total": "220.00",
  "pieces": [
    {
      "id": 1,
      "length": "3.000",
      "width": "2.000",
      "quantity": "2.000",
      "notes": "",
      "piece_subtotal": "110.00",
      "piece_total": "220.00",
      "position": 1,
      "items": [
        {
          "id": 1,
          "piece": 1,
          "service": 1,
          "service_name": "Glass",
          "cost_method": "area",
          "unit_price": "10.00",
          "line_total": "60.00"
        },
        {
          "id": 2,
          "piece": 1,
          "service": 2,
          "service_name": "Polish",
          "cost_method": "perimeter",
          "unit_price": "5.00",
          "line_total": "50.00"
        }
      ]
    }
  ],
  "items": [ "...same service rows flattened..." ]
}
```

`items` on the invoice is a flattened read-only list of every service (same rows as nested `pieces[].items`).

### Invoice money fields

| Field | Meaning |
|-------|---------|
| `total` | Final invoice total after discounts |
| `amount_paid` | Sum of payments linked to this invoice |
| `amount_remaining` | `max(total − amount_paid, 0)` (read-only) |
| `payment_status` | `unpaid` \| `partial` \| `paid` (read-only) |
| `is_settled` | `true` when the invoice is fully paid (`amount_remaining = 0`) |

## Payment (deposit) entity

`Payment` stores every receipt from a client.

| Field | Required | Notes |
|-------|----------|-------|
| client | yes | Owner of the deposit |
| invoice | no | Set when paying against a confirmed invoice |
| amount | yes | `> 0` |
| paid_at | yes | Defaults to today |
| notes | no | Free text |

### Rules

1. Invoice-linked payments only on `confirmed` invoices.
2. Payment amount cannot exceed the invoice’s current `amount_remaining`.
3. Recording a payment increments `Invoice.amount_paid`.
4. Standalone payments (no invoice) are general client deposits.
5. Soft-deleted clients cannot receive payments.

## Confirm with payment

`POST /api/v1/invoices/{id}/confirm/`

```json
{ "amount_paid": "40.00" }
```

- Omit or `0` → confirm unpaid (`amount_paid` stays `0`).
- Equal to `total` → fully paid.
- Less than `total` → partial; remainder stays on the client balance via statement math.

## Pay after confirm

`POST /api/v1/invoices/{id}/pay/`

```json
{ "amount": "60.00", "notes": "cash", "paid_at": "2026-07-26" }
```

## Client statement

`GET /api/v1/clients/{id}/statement/`

```json
{
  "client": { "...": "..." },
  "total_charged": "100.00",
  "total_deposits": "50.00",
  "balance_due": "50.00",
  "invoices": [
    {
      "id": 1,
      "number": "INV-2026-00001",
      "issue_date": "2026-07-26",
      "status": "confirmed",
      "total": "100.00",
      "amount_paid": "30.00",
      "amount_remaining": "70.00",
      "payment_status": "partial"
    }
  ],
  "deposits": [
    {
      "id": 1,
      "amount": "30.00",
      "paid_at": "2026-07-26",
      "notes": "",
      "invoice": 1,
      "invoice_number": "INV-2026-00001",
      "created_at": "2026-07-26T12:00:00Z"
    }
  ]
}
```

### Balance formula

- `total_charged` = sum of **confirmed** invoice `total`
- `total_deposits` = sum of **all** client `Payment.amount`
- `balance_due` = `total_charged − total_deposits`

Cancelled invoices are listed for history but excluded from `total_charged`.

## Standalone deposit

`POST /api/v1/clients/{id}/deposits/`

```json
{ "amount": "20.00", "notes": "advance" }
```

Returns the refreshed statement (HTTP 201).

## UX mapping

| UI action | API |
|-----------|-----|
| Confirm with full/partial/no pay | `POST .../confirm/` + optional `amount_paid` |
| Record more payment on confirmed bill | `POST .../pay/` |
| Client page «كشف حساب» | `GET .../statement/` |
| Add deposit on client page | `POST .../deposits/` |
