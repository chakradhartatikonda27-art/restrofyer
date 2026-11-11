# API Architecture & Endpoints Specification

## 1. Overview
The platform provides a versioned, RESTful API under `/api/v1` with JSON request/response payloads, OpenAPI documentation, and strict JWT Bearer authentication.

Interactive OpenAPI Documentation: `http://localhost:8000/api/v1/docs`

---

## 2. API Route Groups

### Authentication & Tenant Registration (`/api/v1/auth`)
- `POST /register`: Self-service tenant registration (creates tenant, first branch, owner user, trial subscription).
- `POST /login`: Restaurant staff login (returns JWT token with role, tenant_id, branch_id).
- `POST /platform-login`: SaaS platform super admin authentication.
- `GET /me`: Authenticated user profile and organization details.

### Platform Super Admin (`/api/v1/platform`)
- `GET /metrics`: Aggregated platform KPIs (MRR, ARR, active tenants, order counts).
- `GET /tenants`: Tenant directory with search, filter, and plan view.
- `PUT /tenants/{tenant_id}/status`: Activate or suspend restaurant tenant.
- `GET /plans`: Configured subscription plans and feature flags.
- `GET /audit-logs`: Platform-level security and administrative audit logs.

### Operations & Branches (`/api/v1/branches`, `/api/v1/users`)
- `GET /branches`: List branches for authenticated tenant.
- `POST /branches`: Create branch (enforces subscription plan branch limits).
- `GET /users`: List staff members.
- `POST /users`: Invite staff member with RBAC role.

### Menu Management (`/api/v1/menus`)
- `GET /menus/categories`: Categories with active items, variants, and modifiers.
- `POST /menus/categories`: Create category.
- `GET /menus/items`: Menu items list.
- `POST /menus/items`: Create menu item with variants and modifiers.
- `PATCH /menus/items/{id}/toggle-availability`: 86 / disable dish.

### Visual Tables & Reservations (`/api/v1/tables`, `/api/v1/reservations`)
- `GET /tables/areas`: Dining rooms / sections.
- `GET /tables`: Visual table floor plan with status badges and QR tokens.
- `POST /tables`: Create table with unique QR token.
- `POST /tables/{id}/release`: Free table back to Available.
- `GET /reservations`: Booking calendar.
- `POST /reservations`: Create reservation.
- `PATCH /reservations/{id}/status`: Update status (CheckedIn sets table to Occupied).

### POS & Kitchen KDS (`/api/v1/orders`, `/api/v1/invoices`, `/api/v1/kitchens`)
- `POST /orders`: High-speed POS order placement (routes KOTs to kitchen stations, snapshots prices).
- `GET /orders`: Filter orders by date, type, branch, status.
- `POST /invoices/orders/{order_id}/payments`: Process payment (Cash, Card, UPI, Split), complete order, trigger Recipe BOM inventory depletion, award loyalty points.
- `GET /kitchens/kots`: Live active kitchen tickets.
- `PATCH /kitchens/kots/{id}/status`: Transition KOT (`Preparing` -> `Ready` -> `Served`).

### Inventory, Recipes & Procurement (`/api/v1/inventory`, `/api/v1/recipes`, `/api/v1/procurement`)
- `GET /inventory/items`: Raw materials stock balances with low-stock alerts.
- `POST /inventory/movements`: Manual stock adjustments with audit reasons.
- `GET /recipes/{menu_item_id}`: Recipe BOM and calculated food cost.
- `POST /recipes`: Save BOM ingredients and yield portions.
- `GET /procurement/suppliers`: Vendor directory.
- `POST /procurement/purchase-orders`: Issue purchase order.
- `POST /procurement/goods-receipts`: Receive goods (GRN) and auto-increment inventory stock.

### Customer CRM & Loyalty (`/api/v1/crm`, `/api/v1/loyalty`)
- `GET /crm`: Customer list with LTV spend, visits, and segments (VIP, Returning, New).
- `POST /crm`: Create customer profile.
- `GET /loyalty/customers/{id}/transactions`: Double-entry points ledger history.

### Financials (`/api/v1/cash-registers`, `/api/v1/expenses`, `/api/v1/reports`)
- `GET /cash-registers/active-session`: Active drawer shift status.
- `POST /cash-registers/open`: Open shift with opening float.
- `POST /cash-registers/sessions/{id}/transactions`: Cash in / Cash out.
- `POST /cash-registers/sessions/{id}/close`: Close shift with variance formula.
- `GET /reports/sales`: Sales KPIs and order type breakdown.
- `GET /reports/profit-loss`: Revenue, Food Cost COGS, and Net Operating Profit.
- `GET /reports/export/sales-csv`: Downloadable CSV report.

### Public Customer Storefront & QR (`/api/v1/public`)
- `GET /public/{tenant_slug}/menu`: Public digital menu.
- `GET /public/table/{qr_token}`: QR token resolution to table and branch.
- `POST /public/{tenant_slug}/orders`: Online & Table QR order placement.
