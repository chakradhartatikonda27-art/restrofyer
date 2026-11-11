"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  LayoutGrid, MonitorCheck, ShoppingBag, Layers,
  Receipt, BarChart3, Sparkles, ArrowRight
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function LandingPage() {
  const router = useRouter();
  const [loadingRole, setLoadingRole] = useState<string | null>(null);

  const handleQuickLogin = async (email: string, pass: string, isSuperAdmin: boolean = false, targetRoute: string = "/app/dashboard") => {
    setLoadingRole(email);
    try {
      const endpoint = isSuperAdmin ? "/auth/platform-login" : "/auth/login";
      const res = await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify({ email, password: pass })
      });

      // Fetch user profile
      localStorage.setItem("saas_auth_token", res.access_token);
      const profile = await apiRequest("/auth/me");
      saveAuthSession(res.access_token, profile);

      router.push(isSuperAdmin ? "/platform" : targetRoute);
    } catch (err: any) {
      alert(`Login failed: ${err.message}`);
    } finally {
      setLoadingRole(null);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-line bg-panel-glass backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-amber-400 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white font-bold text-xl">
              R
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight text-ink">Resto<span className="text-brand-600">SaaS</span></span>
              <span className="text-xs ml-2 px-2 py-0.5 rounded-full bg-tint-brand text-accent-brand border border-tint-brand-border font-medium">Enterprise ERP</span>
            </div>
          </div>
          <div className="flex items-center gap-3 sm:gap-4">
            <ThemeToggle />
            <Link href="/auth/login" className="text-sm font-medium text-ink-3 hover:text-ink px-3 py-2 rounded-lg transition">
              Sign In
            </Link>
            <Link href="/auth/register" className="text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg shadow-md shadow-brand-500/25 transition">
              Start Free Trial
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6 max-w-7xl mx-auto text-center flex-1 flex flex-col justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-well border border-line text-xs font-semibold text-accent-brand mb-6 mx-auto shadow-sm">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multi-Tenant Architecture • PostgreSQL Row-Level Security • Real-time KDS</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-ink max-w-4xl mx-auto leading-tight">
          The Operating System for Modern <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--hero-from)] to-[var(--hero-to)]">Restaurants & Multi-Branch Chains</span>
        </h1>
        <p className="mt-6 text-lg text-ink-muted max-w-2xl mx-auto">
          High-speed POS, real-time Kitchen Display System (KDS), Recipe BOM inventory costing, visual table floor plans, dual-entry loyalty ledgers, and cash register shifts.
        </p>

        {/* Instant Role Evaluation Bar */}
        <div className="mt-12 p-6 rounded-2xl bg-panel border border-line max-w-5xl mx-auto shadow-xl">
          <div className="text-xs uppercase tracking-wider text-ink-muted font-semibold mb-4 text-left">
            ⚡ Quick-Launch Demo Roles (1-Click Authenticated Access)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
            <button
              onClick={() => handleQuickLogin("admin@restaurantsaas.com", "SuperAdmin@2026!", true, "/platform")}
              disabled={!!loadingRole}
              className="p-3.5 rounded-xl bg-well hover:bg-control border border-line text-left transition group relative overflow-hidden disabled:opacity-50"
            >
              <div className="text-xs font-bold text-accent-amber flex items-center justify-between">
                <span>Platform Admin</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-ink font-semibold mt-1 truncate">SaaS Super Portal</div>
              <div className="text-[10px] text-ink-subtle mt-0.5">MRR, ARR, Tenants</div>
            </button>

            <button
              onClick={() => handleQuickLogin("marco@bellanapoli.com", "Owner@123", false, "/app/dashboard")}
              disabled={!!loadingRole}
              className="p-3.5 rounded-xl bg-well hover:bg-control border border-line text-left transition group relative overflow-hidden disabled:opacity-50"
            >
              <div className="text-xs font-bold text-accent-brand flex items-center justify-between">
                <span>Tenant Owner</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-ink font-semibold mt-1 truncate">Bella Napoli Trattoria</div>
              <div className="text-[10px] text-ink-subtle mt-0.5">Full Backoffice & Analytics</div>
            </button>

            <button
              onClick={() => handleQuickLogin("owner@spicesymphony.com", "Owner@456", false, "/app/menu")}
              disabled={!!loadingRole}
              className="p-3.5 rounded-xl bg-well hover:bg-control border border-line text-left transition group relative overflow-hidden disabled:opacity-50"
            >
              <div className="text-xs font-bold text-accent-purple flex items-center justify-between">
                <span>Menu ERP (Hyd)</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-ink font-semibold mt-1 truncate">Spice Symphony Bistro</div>
              <div className="text-[10px] text-ink-subtle mt-0.5">Veg Curries, Modifiers & CSV</div>
            </button>

            <button
              onClick={() => handleQuickLogin("lucas@bellanapoli.com", "Cashier@123", false, "/app/pos")}
              disabled={!!loadingRole}
              className="p-3.5 rounded-xl bg-well hover:bg-control border border-line text-left transition group relative overflow-hidden disabled:opacity-50"
            >
              <div className="text-xs font-bold text-accent-emerald flex items-center justify-between">
                <span>Front Cashier</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-ink font-semibold mt-1 truncate">POS Terminal</div>
              <div className="text-[10px] text-ink-subtle mt-0.5">Touch billing, split payments</div>
            </button>

            <button
              onClick={() => handleQuickLogin("mario@bellanapoli.com", "Chef@123", false, "/app/kitchen")}
              disabled={!!loadingRole}
              className="p-3.5 rounded-xl bg-well hover:bg-control border border-line text-left transition group relative overflow-hidden disabled:opacity-50"
            >
              <div className="text-xs font-bold text-accent-sky flex items-center justify-between">
                <span>Head Chef</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-ink font-semibold mt-1 truncate">Kitchen Display (KDS)</div>
              <div className="text-[10px] text-ink-subtle mt-0.5">Station routing & live KOTs</div>
            </button>
          </div>
          {loadingRole && (
            <div className="mt-3 text-xs text-accent-brand animate-pulse font-medium">
              Authenticating session for {loadingRole}...
            </div>
          )}
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 text-left max-w-6xl mx-auto">
          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-brand text-accent-brand flex items-center justify-center mb-4">
              <ShoppingBag className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">Touch-Speed POS Terminal</h3>
            <p className="text-sm text-ink-muted mt-2">
              Variant pricing snapshots, modifier popovers, split billing, hold & resume orders, and receipt generation.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-sky text-accent-sky flex items-center justify-center mb-4">
              <MonitorCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">Real-Time Kitchen KDS</h3>
            <p className="text-sm text-ink-muted mt-2">
              Station-based KOT item routing (Pizza, Grill, Bar), live elapsed prep timers, and status pipelines.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-emerald text-accent-emerald flex items-center justify-center mb-4">
              <Layers className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">Recipe BOM & Food Costing</h3>
            <p className="text-sm text-ink-muted mt-2">
              Automatic raw ingredient consumption on order completion, low-stock reorder alerts, and Goods Receipt (GRN).
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-purple text-accent-purple flex items-center justify-center mb-4">
              <LayoutGrid className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">Visual Floor Plan & QR Tables</h3>
            <p className="text-sm text-ink-muted mt-2">
              Interactive dining rooms, table status badges (Available, Occupied, Reserved, Cleaning), and instant QR table ordering.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-amber text-accent-amber flex items-center justify-center mb-4">
              <Receipt className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">Cash Register Shifts</h3>
            <p className="text-sm text-ink-muted mt-2">
              Opening float, cash in/out, shift closing with automated formula and variance audit logging.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-panel border border-line hover:border-line-strong shadow-sm transition">
            <div className="w-12 h-12 rounded-xl bg-tint-rose text-accent-rose flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">SaaS Multi-Tenancy & P&L</h3>
            <p className="text-sm text-ink-muted mt-2">
              PostgreSQL Row-Level Security, multi-branch consolidated reports, COGS, gross margin %, and CSV exports.
            </p>
          </div>
        </div>

        {/* Public Storefront Preview link */}
        <div className="mt-16 text-center text-sm text-ink-muted">
          Want to test the customer online ordering experience?{" "}
          <Link href="/customer/bella-napoli" className="text-accent-brand hover:underline font-semibold underline-offset-4">
            Visit Bella Napoli Public Storefront →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-line py-8 text-center text-xs text-ink-subtle">
        RestoSaaS Platform © 2026. Designed for Independent Restaurants and Multi-Branch Hospitality Enterprises.
      </footer>
    </div>
  );
}
