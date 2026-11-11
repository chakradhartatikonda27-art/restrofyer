# Restaurant CRM / ERP User & Operations Guide

## 1. Demo User Profiles & Login Credentials

| Role | Name | Email | Password | Primary Workflow |
|---|---|---|---|---|
| **Platform Super Admin** | Super Administrator | `admin@restaurantsaas.com` | `SuperAdmin@2026!` | SaaS Tenant Management, MRR, Health Monitor |
| **Tenant Owner** | Marco Rossi (Bella Napoli) | `marco@bellanapoli.com` | `Owner@123` | Backoffice, P&L Reports, Branch Settings |
| **Branch Cashier** | Lucas D'Souza | `lucas@bellanapoli.com` | `Cashier@123` | High-speed POS, Split Billing, Drawer Shifts |
| **Kitchen Chef** | Mario Conti | `mario@bellanapoli.com` | `Chef@123` | Real-time KDS Board, Station Prep Pipeline |
| **Tenant 2 Owner** | Rajesh Verma (Spice Symphony) | `owner@spicesymphony.com` | `Owner@456` | Cross-Tenant Isolation Benchmark |

---

## 2. Key Operational Workflows

### A. Placing a Dine-in POS Order
1. Navigate to `/app/pos`.
2. Select your dining table from the top table picker (e.g. `T-01`).
3. Select dishes from the menu catalog. If a dish has variants (e.g. Margherita Regular vs Large) or modifiers (e.g. Extra Mozzarella), choose options and click "Add to Bill".
4. Review the itemized subtotal, tax breakdown, and service charge.
5. Click **"Pay & Send to Kitchen"**. Select payment tender (Cash, Card, UPI, or Split) and confirm.
6. The POS prints the tax invoice, marks the table as `Occupied`, dispatches a real-time KOT to the Kitchen Display (KDS), and automatically consumes recipe raw materials from inventory!

### B. Kitchen Display System (KDS) Line Cooking
1. Navigate to `/app/kitchen`.
2. Chefs view incoming KOT tickets filtered by station (e.g. `Woodfire Pizza Station`, `Fresh Pasta & Grill`).
3. When prep starts, click **"Start Preparing"** — the timer turns active amber.
4. When dishes are plated, click **"Mark Ready"** — the ticket turns green and notifies service staff.
5. When picked up by waiters, click **"Mark Dispatched / Served"**.

### C. Cash Register Drawer Shift Lifecycle
1. Navigate to `/app/cash-register`.
2. At shift opening, count physical drawer cash and click **"Open Shift Drawer"** with opening float (e.g. ₹2,000.00).
3. Record mid-shift float adjustments via **"Cash In / Out"**. Cash orders automatically increment the running drawer cash sales.
4. At shift end, click **"Close Shift & Reconcile"**. Enter the physical cash counted in the drawer.
5. The system computes the mathematical variance (`Variance = Actual Counted Cash - Expected Cash`) and logs an immutable audit trail.
