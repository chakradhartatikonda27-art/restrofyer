# System Architecture & Technical Specifications

## 1. Executive Architecture Summary

The **Restaurant CRM / ERP Multi-Tenant SaaS Platform** is engineered as a modular, cloud-native application serving independent restaurant enterprises and multi-branch hospitality groups.

### Technology Stack
- **Backend API**: Python 3.14 / FastAPI (asynchronous, high concurrency)
- **Data Persistence**: PostgreSQL with Row-Level Security (RLS) & transactional isolation
- **ORM & Migrations**: SQLAlchemy 2.0 with session-scoped tenant context injection & Alembic
- **Frontend SPA**: Next.js 14 App Router, React 18, TypeScript, Tailwind CSS
- **Authentication**: Cryptographic JWT Bearer tokens with Bcrypt password hashing
- **Security & Authorization**: Granular Role-Based Access Control (RBAC) & PostgreSQL kernel-enforced RLS

---

## 2. Multi-Tenant Hierarchy

```text
SaaS Platform Root
│
├── Platform Super Admin Portal (/platform)
│   ├── Tenant Lifecycle Management (Activation, Suspension)
│   ├── Real-time Platform Metrics (MRR, ARR, Error Rates)
│   └── Subscription Plans & Feature Entitlements
│
├── Tenant Organization A (e.g., "Bella Napoli Trattoria")
│   ├── Subscription Tier: Professional
│   ├── Branch 01: Jubilee Hills (Flagship)
│   │   ├── Front POS Terminal & Cash Register
│   │   ├── Kitchen Display System (KDS Stations: Pizza, Pasta, Bar)
│   │   ├── Dining Areas & Table Layout (Window, Terrace, VIP)
│   │   └── Branch Inventory & Recipe BOM Consumption
│   └── Branch 02: Hitec City
│
└── Tenant Organization B (e.g., "Spice Symphony Bistro")
    ├── Subscription Tier: Growth
    └── Branch 01: Banjara Hills
```

---

## 3. Core Operational Subsystems

1. **High-Speed POS & Billing**:
   - Sub-second touch ordering with variant prices, modifier popovers, split billing, and snapshot pricing.
2. **Real-time Kitchen Display System (KDS)**:
   - Dynamic station routing (e.g. Pizza Oven vs Grill vs Bar).
   - Lifecycle: `New` -> `Accepted` -> `Preparing` -> `Ready` -> `Served`.
3. **Recipe Bill of Materials (BOM) & Inventory Depletion**:
   - Bill of materials linking dishes to raw ingredients.
   - Real-time stock decrement on order completion and COGS calculation.
4. **Visual Floor Plan & Contactless QR Ordering**:
   - Interactive dining room grid with status badges (`Available`, `Occupied`, `Reserved`, `Cleaning`).
   - Per-table QR tokens for instant ordering without waiter intervention.
5. **Cash Register Shift Reconciliation**:
   - Formal opening float, shift transactions (Cash In, Cash Out), and closing variance formula.
6. **Double-Entry Loyalty Points Ledger**:
   - Immutable audit trail for customer reward points.
