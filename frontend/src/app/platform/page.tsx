"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldAlert, Building2, CreditCard, Activity,
  Search, RefreshCw, LogOut, Layers
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { clearAuthSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function PlatformSuperAdminPortal() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [tenants, setTenants] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, t, p, logs] = await Promise.all([
        apiRequest("/platform/metrics"),
        apiRequest(`/platform/tenants${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
        apiRequest("/platform/plans"),
        apiRequest("/platform/audit-logs")
      ]);
      setMetrics(m);
      setTenants(t);
      setPlans(p);
      setAuditLogs(logs);
    } catch (err: any) {
      console.error(err);
      if (err.message.includes("Super Admin") || err.message.includes("credentials")) {
        router.push("/auth/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStatusToggle = async (tenantId: string, currentStatus: string) => {
    const nextStatus = currentStatus === "Active" ? "Suspended" : "Active";
    setUpdatingId(tenantId);
    try {
      await apiRequest(`/platform/tenants/${tenantId}/status?status_val=${nextStatus}`, {
        method: "PUT"
      });
      await loadData();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const filteredTenants = tenants.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.contact_email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col">
      {/* Top Admin Bar */}
      <header className="border-b border-line bg-panel-glass backdrop-blur px-8 h-16 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-tint-amber text-accent-amber border border-tint-amber-border flex items-center justify-center font-bold">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <span className="font-extrabold text-lg text-ink">SaaS Platform <span className="text-accent-amber">Super Admin</span></span>
            <span className="text-[10px] ml-2 px-2 py-0.5 rounded bg-control text-ink-muted border border-line-strong">Multi-Tenant Root</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <button
            onClick={() => { clearAuthSession(); router.push("/"); }}
            className="flex items-center gap-1.5 text-xs text-ink-muted hover:text-accent-rose font-semibold px-3 py-1.5 rounded-lg border border-line hover:border-tint-rose-border transition"
          >
            <LogOut className="w-3.5 h-3.5" /> Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="p-8 max-w-7xl mx-auto w-full space-y-8 flex-1">
        {/* Metric Cards Row */}
        {metrics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
              <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
                <span>Monthly Recurring Revenue</span>
                <CreditCard className="w-4 h-4 text-accent-emerald" />
              </div>
              <div className="text-2xl font-black text-accent-emerald mt-2">
                ${metrics.monthly_recurring_revenue.toLocaleString()}
              </div>
              <div className="text-[11px] text-ink-subtle mt-1">ARR: ${metrics.annual_recurring_revenue.toLocaleString()}</div>
            </div>

            <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
              <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
                <span>Active Restaurant Tenants</span>
                <Building2 className="w-4 h-4 text-accent-brand" />
              </div>
              <div className="text-2xl font-black text-ink mt-2">
                {metrics.active_tenants} <span className="text-xs font-normal text-ink-subtle">/ {metrics.total_tenants} Total</span>
              </div>
              <div className="text-[11px] text-ink-subtle mt-1">{metrics.suspended_tenants} suspended, {metrics.trial_tenants} trials</div>
            </div>

            <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
              <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
                <span>Total Branches Deployed</span>
                <Layers className="w-4 h-4 text-accent-sky" />
              </div>
              <div className="text-2xl font-black text-accent-sky mt-2">
                {metrics.total_branches}
              </div>
              <div className="text-[11px] text-ink-subtle mt-1">{metrics.active_users} active staff accounts</div>
            </div>

            <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
              <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
                <span>Platform Orders Processed</span>
                <Activity className="w-4 h-4 text-accent-amber" />
              </div>
              <div className="text-2xl font-black text-accent-amber mt-2">
                {metrics.total_orders_processed}
              </div>
              <div className="text-[11px] text-accent-emerald mt-1">System Health: 100% Operational</div>
            </div>
          </div>
        )}

        {/* Tenants Section */}
        <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-bold text-ink">Restaurant Tenants Management</h2>
              <p className="text-xs text-ink-muted mt-0.5">Manage customer organizations, subscriptions, and access statuses.</p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search tenants or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-sm"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink-3 shadow-sm"
              >
                <option value="">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Suspended">Suspended</option>
                <option value="Trial">Trial</option>
              </select>

              <button
                onClick={loadData}
                className="p-2 rounded-lg bg-control hover:bg-control-hover text-ink-3 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Restaurant Organization</th>
                  <th className="py-3 px-4">Contact & Slug</th>
                  <th className="py-3 px-4">Subscription Plan</th>
                  <th className="py-3 px-4">Branches</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line font-medium">
                {filteredTenants.map((t) => (
                  <tr key={t.id} className="hover:bg-row-hover transition">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-ink">{t.name}</div>
                      <div className="text-[10px] text-ink-subtle">{t.business_type} • {t.country}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="text-ink-3">{t.contact_email}</div>
                      <div className="text-[10px] text-ink-subtle font-mono">/{t.slug}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-1 rounded-full bg-control border border-line-strong text-ink-2 text-[11px] font-semibold">
                        {t.plan_name}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-ink-3">
                      {t.branch_count} {t.branch_count === 1 ? 'branch' : 'branches'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                        t.status === "Active" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                        t.status === "Suspended" ? "bg-tint-rose text-accent-red border border-tint-rose-border" :
                        "bg-tint-amber text-accent-amber border border-tint-amber-border"
                      }`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {t.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleStatusToggle(t.id, t.status)}
                        disabled={updatingId === t.id}
                        className={`text-xs px-3 py-1 rounded-lg font-semibold transition border ${
                          t.status === "Active"
                            ? "bg-tint-rose border-tint-rose-border text-accent-red hover:opacity-80"
                            : "bg-tint-emerald border-tint-emerald-border text-accent-emerald hover:opacity-80"
                        }`}
                      >
                        {updatingId === t.id ? "Updating..." : t.status === "Active" ? "Suspend Tenant" : "Reactivate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Subscription Plans & Platform Audit Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-ink mb-4">Configured Subscription Plans</h3>
            <div className="space-y-3">
              {plans.map((p) => (
                <div key={p.id} className="p-4 rounded-xl bg-well border border-line flex items-center justify-between">
                  <div>
                    <div className="font-bold text-sm text-ink">{p.name}</div>
                    <div className="text-xs text-ink-muted mt-0.5">
                      Max {p.branch_limit} branches • {p.user_limit} users • {p.pos_terminal_limit} POS
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-accent-amber">${p.monthly_price}/mo</div>
                    <div className="text-[10px] text-ink-subtle">${p.annual_price}/yr</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-ink mb-4">Platform Security & Audit Logs</h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-2.5 rounded-lg bg-well border border-line text-xs flex items-center justify-between">
                  <div>
                    <span className="font-mono text-accent-amber font-semibold">{log.action}</span>
                    <span className="text-ink-subtle ml-2">by {log.actor_email || "System"}</span>
                  </div>
                  <span className="text-[10px] text-ink-subtle">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
