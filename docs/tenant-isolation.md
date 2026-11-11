# Multi-Tenant Isolation & Security Architecture

## 1. Multi-Tenant Philosophy

The Restaurant CRM / ERP platform is designed as a true multi-tenant SaaS architecture where multiple independent restaurant enterprises operate within a shared infrastructure while strictly enforcing complete logical and physical isolation of their data, configurations, and operations.

### Core Isolation Principles
1. **Never Trust the Client**: Tenant ID is never accepted as a raw request parameter from frontend clients for authorization. It is strictly derived from the authenticated cryptographic JWT token, validated against tenant memberships in the database.
2. **Defense-in-Depth**:
   - **Layer 1: Network & Middleware Boundary**: Validates JWT, extracts `tenant_id`, enforces branch access rights, and checks subscription entitlements.
   - **Layer 2: Database Session Context**: Sets PostgreSQL session variables `SET LOCAL app.current_tenant_id = '<uuid>'` on each transaction.
   - **Layer 3: PostgreSQL Row-Level Security (RLS)**: PostgreSQL native kernel policies (`tenant_isolation_policy`) guarantee that even if an application bug omitted a `WHERE tenant_id = ...` clause, the database itself rejects or filters unauthorized rows.
   - **Layer 4: ORM Query Filtering**: The repository layer automatically attaches tenant boundaries to all queries.

---

## 2. PostgreSQL Row-Level Security (RLS) Specification

All tenant-owned tables (such as `branches`, `menus`, `orders`, `invoices`, `inventory_items`, `customers`, etc.) are protected with RLS:

```sql
-- Enable RLS on the table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Restrict all operations (SELECT, INSERT, UPDATE, DELETE) to the active tenant session
CREATE POLICY tenant_isolation_policy ON orders
    AS RESTRICTIVE
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```

### Super Admin Bypass Rule
Platform administrators accessing the system in Super Admin mode authenticate via `platform_users` and execute with `app.is_super_admin = 'true'`, allowing administrative oversight and aggregated SaaS analytics.

---

## 3. Branch-Level Authorization

Within an enterprise tenant:
- A user may have access to one branch, multiple branches, or all branches (Headquarters / Org Manager).
- Branch membership is resolved during authentication:
  - Branch Managers, Cashiers, Waiters, and KDS Staff are scoped to their assigned `branch_id`.
  - Organization Owners, Admins, and Accountants have tenant-wide branch switching capability.
- Every transactional entity (Orders, KOTs, Tables, Inventory, Cash Registers) contains both `tenant_id` and `branch_id`.

---

## 4. Feature Entitlement Guardrails

Subscription plans govern access to specialized modules:
- `Starter`: POS, Menu, Tables, Invoices. Single branch limit.
- `Growth`: Starter + KDS, CRM, Inventory. Up to 3 branches.
- `Professional`: Growth + Recipes, Loyalty, Online/QR Ordering, Delivery. Up to 10 branches.
- `Enterprise`: Full suite + Multi-branch consolidated reports, API access, Unlimited branches.

The backend API verifies entitlements before processing requests (`check_feature_entitlement(tenant_id, "inventory.enabled")`).
