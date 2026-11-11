# Database Architecture & Schema Specification

## 1. Overview
The platform database is modeled in PostgreSQL using normalized 3NF structures with UUID primary keys and defense-in-depth Row-Level Security (RLS). Decimal numeric types are enforced for all monetary values (`Numeric(10,2)`) to eliminate floating-point rounding errors.

---

## 2. Entity Groups & Relationships

```mermaid
erDiagram
    TENANTS ||--o{ SUBSCRIPTIONS : "has"
    TENANTS ||--o{ BRANCHES : "operates"
    TENANTS ||--o{ USERS : "employs"
    TENANTS ||--o{ MENUS : "defines"
    BRANCHES ||--o{ RESTAURANT_TABLES : "contains"
    BRANCHES ||--o{ ORDERS : "processes"
    BRANCHES ||--o{ KITCHENS : "maintains"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    ORDERS ||--o| INVOICES : "billed_by"
    ORDERS ||--o{ KOTS : "routes"
    KOTS ||--o{ KOT_ITEMS : "cooks"
    MENU_ITEMS ||--o| RECIPES : "composed_of"
    RECIPES ||--o{ RECIPE_ITEMS : "measures"
    INVENTORY_ITEMS ||--o{ RECIPE_ITEMS : "supplies"
    INVENTORY_ITEMS ||--o{ STOCK_MOVEMENTS : "tracks"
    CUSTOMERS ||--o| LOYALTY_ACCOUNTS : "owns"
    LOYALTY_ACCOUNTS ||--o{ LOYALTY_TRANSACTIONS : "logs"
    CASH_REGISTERS ||--o{ CASH_REGISTER_SESSIONS : "opens"
```

---

## 3. Core Tables Specification

### `tenants`
- `id`: String(36) UUID PK
- `name`: String(255)
- `slug`: String(100) UNIQUE
- `status`: String(50) (Active, Trial, Suspended, Deactivated)
- `currency`: String(10) (INR, USD, EUR, GBP)
- `timezone`: String(50)
- `onboarding_completed`: Boolean

### `orders`
- `id`: String(36) UUID PK
- `tenant_id`: String(36) FK (tenants.id)
- `branch_id`: String(36) FK (branches.id)
- `order_number`: String(50) (e.g. `ORD-261030-0001`)
- `order_type`: String(30) (DineIn, Takeaway, Delivery, Online, QR)
- `subtotal`: Numeric(10, 2)
- `discount_amount`: Numeric(10, 2)
- `tax_amount`: Numeric(10, 2)
- `service_charge`: Numeric(10, 2)
- `total_amount`: Numeric(10, 2)
- `status`: String(30) (Draft, Confirmed, InKitchen, Ready, Served, Completed, Cancelled)

### `order_items`
- `id`: String(36) UUID PK
- `order_id`: String(36) FK (orders.id)
- `menu_item_id`: String(36)
- `item_name`: String(255) (Snapshot)
- `unit_price`: Numeric(10, 2) (Immutable price snapshot)
- `cost_price`: Numeric(10, 2) (COGS snapshot)
- `quantity`: Integer
- `subtotal`: Numeric(10, 2)
- `modifiers`: JSON

### `recipes` & `recipe_items`
- `menu_item_id`: Links recipe to menu dish
- `yield_portions`: Portion multiplier
- `recipe_items.inventory_item_id`: Raw ingredient
- `recipe_items.quantity`: Quantity consumed per portion

### `cash_register_sessions`
- `opening_float`: Numeric(10, 2)
- `cash_sales`: Numeric(10, 2)
- `cash_in`: Numeric(10, 2)
- `cash_out`: Numeric(10, 2)
- `cash_refunds`: Numeric(10, 2)
- `expected_closing_cash`: Calculated formula
- `actual_closing_cash`: Counted physical cash
- `variance`: actual - expected
