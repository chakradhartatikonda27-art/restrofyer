"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, ShoppingBag, MonitorCheck, LayoutGrid, Receipt,
  CalendarCheck, UtensilsCrossed, Layers, Package, Truck, Users,
  Coins, FileText, Settings, LogOut, ChevronDown, Building2, Store,
  ExternalLink
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { getStoredUser, clearAuthSession, getActiveBranch, setActiveBranch } from "@/lib/auth";
import { ThemeToggle } from "@/components/ThemeToggle";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
  subItems?: { name: string; href: string }[];
}

export default function AppWorkspaceLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [branches, setBranches] = useState<any[]>([]);
  const [currentBranchId, setCurrentBranchId] = useState<string>("");

  useEffect(() => {
    const profile = getStoredUser();
    if (!profile) {
      router.push("/auth/login");
      return;
    }
    setUser(profile);
    loadBranches();
  }, []);

  const loadBranches = async () => {
    try {
      const data = await apiRequest("/branches");
      setBranches(data);
      const stored = getActiveBranch();
      if (stored && data.some((b: any) => b.id === stored)) {
        setCurrentBranchId(stored);
      } else if (data.length > 0) {
        setCurrentBranchId(data[0].id);
        setActiveBranch(data[0].id);
      }
    } catch (err) {
      console.error("Error loading branches:", err);
    }
  };

  const handleBranchChange = (branchId: string) => {
    setCurrentBranchId(branchId);
    setActiveBranch(branchId);
    window.location.reload();
  };

  const handleLogout = () => {
    clearAuthSession();
    router.push("/");
  };

  const navGroups: { title: string; items: NavItem[] }[] = [
    {
      title: "Operations",
      items: [
        { name: "Dashboard", href: "/app/dashboard", icon: LayoutDashboard },
        { name: "POS Terminal", href: "/app/pos", icon: ShoppingBag, badge: "Live" },
        { name: "Kitchen (KDS)", href: "/app/kitchen", icon: MonitorCheck },
        { name: "Tables & Floor", href: "/app/tables", icon: LayoutGrid },
        { name: "Orders & Invoices", href: "/app/orders", icon: Receipt },
        { name: "Reservations", href: "/app/reservations", icon: CalendarCheck },
      ]
    },
    {
      title: "Menu & Kitchen",
      items: [
        {
          name: "Menus",
          href: "/app/menu",
          icon: UtensilsCrossed,
          subItems: [
            { name: "Cuisines", href: "/app/menu/cuisines" },
            { name: "Menu Items", href: "/app/menu/items" },
            { name: "Dish Categories", href: "/app/menu/categories" },
            { name: "Modifier Groups", href: "/app/menu/modifier-groups" },
            { name: "Item Modifiers", href: "/app/menu/modifiers" },
          ],
        },
        { name: "Recipe BOM & Costs", href: "/app/recipes", icon: Layers },
      ]
    },
    {
      title: "Inventory & CRM",
      items: [
        { name: "Inventory Stock", href: "/app/inventory", icon: Package },
        { name: "Purchasing & POs", href: "/app/purchasing", icon: Store },
        { name: "Customer CRM", href: "/app/customers", icon: Users },
        { name: "Delivery Dispatch", href: "/app/delivery", icon: Truck },
        { name: "Cash Register Shifts", href: "/app/cash-register", icon: Coins },
      ]
    },
    {
      title: "Intelligence",
      items: [
        { name: "Analytics & P&L", href: "/app/reports", icon: FileText },
        { name: "Settings & Staff", href: "/app/settings", icon: Settings },
      ]
    }
  ];

  const storefrontSlug = user?.tenant_slug || "bella-napoli";

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col md:flex-row">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-panel border-r border-line flex flex-col shrink-0">
        {/* Brand Header */}
        <div className="p-4 border-b border-line flex items-center justify-between">
          <Link href="/app/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-amber-400 flex items-center justify-center font-bold text-white shadow-md shadow-brand-500/20">
              R
            </div>
            <div>
              <div className="text-sm font-extrabold text-ink tracking-tight leading-none">
                {user?.tenant_name || "Restaurant OS"}
              </div>
              <div className="text-[10px] text-accent-brand font-semibold mt-0.5">Enterprise Cloud</div>
            </div>
          </Link>
        </div>

        {/* Branch Selector Dropdown */}
        {branches.length > 0 && (
          <div className="px-3 pt-3 pb-1">
            <label className="block text-[10px] uppercase font-bold text-ink-subtle px-2 mb-1">Active Location</label>
            <div className="relative">
              <Building2 className="w-3.5 h-3.5 text-ink-muted absolute left-3 top-2.5 pointer-events-none" />
              <select
                value={currentBranchId}
                onChange={(e) => handleBranchChange(e.target.value)}
                className="w-full pl-8 pr-8 py-1.5 bg-well border border-input-border rounded-lg text-xs font-semibold text-ink-2 focus:outline-none focus:ring-1 focus:ring-brand-500 appearance-none cursor-pointer shadow-sm"
              >
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-ink-subtle absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="flex-1 p-3 space-y-4 overflow-y-auto">
          {navGroups.map((group, idx) => (
            <div key={idx} className="space-y-1">
              <div className="text-[10px] uppercase font-bold text-ink-subtle px-2.5 py-1 tracking-wider">
                {group.title}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isDirectActive = pathname === item.href;
                const isSubActive = item.subItems?.some((s) => pathname === s.href);
                const isActive = isDirectActive || Boolean(isSubActive);
                return (
                  <div key={item.href} className="space-y-0.5">
                    <Link
                      href={item.href}
                      className={`flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-semibold transition ${
                        isDirectActive
                          ? "bg-tint-brand text-accent-brand border border-tint-brand-border"
                          : isSubActive
                          ? "text-accent-brand bg-well"
                          : "text-ink-muted hover:text-ink hover:bg-control"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className={`w-4 h-4 ${isActive ? "text-accent-brand" : "text-ink-muted"}`} />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-brand-600 text-white">
                          {item.badge}
                        </span>
                      )}
                    </Link>

                    {item.subItems && (
                      <div className="pl-8 space-y-0.5 pt-0.5 pb-1">
                        {item.subItems.map((sub) => {
                          const subActive = pathname === sub.href;
                          return (
                            <Link
                              key={sub.href}
                              href={sub.href}
                              className={`block px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition ${
                                subActive
                                  ? "bg-tint-brand text-accent-brand font-bold"
                                  : "text-ink-muted hover:text-ink hover:bg-control"
                              }`}
                            >
                              {sub.name}
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Customer Site Link */}
        <div className="px-3 py-2 border-t border-line">
          <Link
            href={`/customer/${storefrontSlug}`}
            target="_blank"
            className="flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink hover:bg-control transition"
          >
            <span>Customer Site</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* User Card & Sign Out */}
        <div className="p-3 border-t border-line bg-well-soft flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-control border border-line-strong flex items-center justify-center text-xs font-bold text-accent-brand shrink-0">
              {user?.full_name ? user.full_name[0] : "U"}
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-ink-2 truncate">{user?.full_name}</div>
              <div className="text-[10px] text-ink-subtle capitalize">{user?.role?.toLowerCase().replace("_", " ")}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-1.5 rounded-lg text-ink-muted hover:text-accent-rose hover:bg-tint-rose transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Workspace Viewport */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Workspace Top Header */}
        <header className="h-14 border-b border-line bg-panel-glass backdrop-blur px-6 flex items-center justify-between shrink-0 sticky top-0 z-30">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <span className="text-ink font-semibold">{user?.tenant_name}</span>
            <span>•</span>
            <span className="text-accent-brand font-medium">
              {branches.find(b => b.id === currentBranchId)?.name || "Main Location"}
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            <Link
              href="/app/tables"
              className="hidden sm:flex text-xs font-bold bg-control hover:bg-control-hover text-ink-2 border border-line-strong px-3 py-1.5 rounded-lg items-center gap-1.5 transition"
            >
              <LayoutGrid className="w-3.5 h-3.5 text-accent-brand" />
              <span>Tables</span>
            </Link>
            <Link
              href="/app/orders"
              className="hidden sm:flex text-xs font-bold bg-control hover:bg-control-hover text-ink-2 border border-line-strong px-3 py-1.5 rounded-lg items-center gap-1.5 transition"
            >
              <Receipt className="w-3.5 h-3.5 text-accent-brand" />
              <span>Recent Orders</span>
            </Link>
            <Link
              href="/app/pos"
              className="text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-lg shadow-sm shadow-brand-500/25 flex items-center gap-1.5 transition"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>POS</span>
            </Link>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="p-6 flex-1 bg-canvas">
          {children}
        </main>
      </div>
    </div>
  );
}
