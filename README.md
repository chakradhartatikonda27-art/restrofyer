# restrofyer — Restaurant CRM / ERP Multi-Tenant SaaS Platform

An enterprise-grade, cloud-native Restaurant CRM / ERP Multi-Tenant SaaS platform engineered for independent restaurant groups and multi-branch hospitality chains.

Built with **FastAPI**, **PostgreSQL** with Row-Level Security (RLS), **SQLAlchemy 2.0**, and **Next.js 14** (App Router) with **Tailwind CSS**.

---

## 🌟 Key Subsystems & Features

- 🏢 **True Multi-Tenancy**: Complete isolation enforced at both the application layer and PostgreSQL kernel level via Row-Level Security (`SET LOCAL app.current_tenant_id`).
- 👑 **Platform Super Admin Portal** (`/platform`): Platform-wide MRR, ARR, active tenant tracking, tenant suspension/reactivation, and plan entitlements.
- ⚡ **Touch-Speed POS Terminal** (`/app/pos`): Variant & modifier pricing, split payments, cash register integration, hold/resume bills, and instant tax receipt generation.
- 👨‍🍳 **Real-time Kitchen Display System (KDS)** (`/app/kitchen`): Station-based KOT routing (Pizza, Grill, Bar), elapsed cooking timers, and stage transitions (`New` -> `Preparing` -> `Ready` -> `Served`).
- 📐 **Interactive Floor Plan** (`/app/tables`): Visual table grid, occupancy tracking (`Available`, `Occupied`, `Reserved`, `Cleaning`), and table release actions.
- 📱 **Contactless Table QR Ordering** (`/order/table/[qrCode]`): Dine-in guests scan table QR codes to place orders directly into the restaurant POS and kitchen without waiter delay.
- 🌐 **Public Online Storefront** (`/customer/[slug]`): Branded online ordering for takeaway and home delivery.
- 🍲 **Recipe Bill of Materials (BOM) & Food Costing** (`/app/recipes`): Bill of materials linking dishes to raw ingredients; automated stock depletion on order fulfillment and real-time gross margin % analysis.
- 📦 **Inventory & Procurement** (`/app/inventory`, `/app/purchasing`): Stock levels, low-stock reorder thresholds, Purchase Orders, and Goods Receipt Notes (GRN).
- 👥 **Customer CRM & Loyalty Ledger** (`/app/customers`): Guest profiles, lifetime spend, VIP segmentation, and double-entry loyalty points ledger.
- 💵 **Cash Register Shifts** (`/app/cash-register`): Opening float, cash in/out, and shift closing with automated variance calculation.
- 📊 **Financial Analytics & P&L** (`/app/reports`): Revenue, Food Cost (COGS), gross margin %, expenses, and CSV exports.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ (Python 3.14 tested)
- Node.js 18+ (Node 24 tested)

### 2. Backend Setup
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/api/v1/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Web application will be live at: `http://localhost:3000`

---

## 🧪 Automated Test Suite

Run the full pytest suite verifying tenant isolation, POS calculations, recipe inventory depletion, and cash register variance:
```bash
cd backend
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```
**Test Results: 12 passed** (100% test pass rate).

---

## 🔑 Demo Access Credentials

| Role | Email | Password | Target Portal |
|---|---|---|---|
| **Platform Super Admin** | `admin@restaurantsaas.com` | `SuperAdmin@2026!` | `/platform` |
| **Tenant Owner** (Bella Napoli) | `marco@bellanapoli.com` | `Owner@123` | `/app/dashboard` |
| **Front Cashier** (POS) | `lucas@bellanapoli.com` | `Cashier@123` | `/app/pos` |
| **Head Chef** (Kitchen KDS) | `mario@bellanapoli.com` | `Chef@123` | `/app/kitchen` |
| **Tenant 2 Owner** (Spice Symphony) | `owner@spicesymphony.com` | `Owner@456` | `/app/dashboard` |

---

## 📁 Repository Structure

```text
restaurant-saas/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Modular API routers (auth, platform, orders, kds, inventory, etc.)
│   │   ├── core/            # Database engine, config, security, deps, RBAC permissions
│   │   ├── models/          # SQLAlchemy 2.0 models with TenantMixin & BranchMixin
│   │   ├── schemas/         # Pydantic v2 validation schemas
│   │   ├── services/        # POS, KDS, inventory depletion, cash register services
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest automated test suites
│   ├── seed_data.py         # Multi-tenant realistic database seeder
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 App Router routes (/platform, /app/*, /customer/*, /order/*)
│   │   ├── components/      # UI components
│   │   └── lib/             # API client & auth session storage
│   ├── package.json
│   └── tailwind.config.ts
├── docs/                    # Complete architectural and operational documentation
└── README.md
```
