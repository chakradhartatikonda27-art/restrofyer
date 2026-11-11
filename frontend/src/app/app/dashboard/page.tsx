"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign, ShoppingBag, AlertTriangle,
  TrendingUp, MonitorCheck, LayoutGrid
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function WorkspaceDashboard() {
  const [salesReport, setSalesReport] = useState<any>(null);
  const [tables, setTables] = useState<any[]>([]);
  const [kots, setKots] = useState<any[]>([]);
  const [lowStock, setLowStock] = useState<any[]>([]);
  const [recentOrders, setRecentOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [sales, tbls, activeKots, inv, orders] = await Promise.all([
        apiRequest("/reports/sales"),
        apiRequest("/tables"),
        apiRequest("/kitchens/kots"),
        apiRequest("/inventory/items?low_stock_only=true"),
        apiRequest("/orders?limit=6")
      ]);
      setSalesReport(sales);
      setTables(tbls);
      setKots(activeKots);
      setLowStock(inv);
      setRecentOrders(orders);
    } catch (err) {
      console.error("Dashboard data error:", err);
    } finally {
      setLoading(false);
    }
  };

  const occupiedCount = tables.filter(t => t.status === "Occupied").length;
  const availableCount = tables.filter(t => t.status === "Available").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Restaurant Operations Dashboard</h1>
          <p className="text-xs text-ink-muted mt-1">Real-time operational status, sales metrics, kitchen pipeline, and table occupancy.</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/app/pos"
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <ShoppingBag className="w-4 h-4" /> Open POS Terminal
          </Link>
          <Link
            href="/app/kitchen"
            className="px-4 py-2 bg-control hover:bg-control-hover text-ink-2 border border-line-strong rounded-xl text-xs font-bold transition flex items-center gap-1.5"
          >
            <MonitorCheck className="w-4 h-4 text-accent-sky" /> Kitchen KDS
          </Link>
        </div>
      </div>

      {/* Low Stock Warning Banner */}
      {lowStock.length > 0 && (
        <div className="p-4 rounded-xl bg-tint-amber border border-tint-amber-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-accent-amber">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-accent-amber">
                Low Inventory Alert: {lowStock.length} raw ingredients below reorder threshold
              </div>
              <div className="text-[11px] text-ink-3 mt-0.5">
                Items: {lowStock.map(i => `${i.name} (${i.current_stock} ${i.uom})`).join(", ")}
              </div>
            </div>
          </div>
          <Link href="/app/inventory" className="text-xs font-bold text-accent-amber hover:underline underline-offset-4 shrink-0 ml-4">
            Manage Stock →
          </Link>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Sales */}
        <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
          <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
            <span>Total Gross Sales</span>
            <span className="p-1.5 rounded-lg bg-tint-emerald text-accent-emerald">
              <DollarSign className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black text-ink mt-2">
            ₹{salesReport?.total_sales?.toLocaleString() || "0.00"}
          </div>
          <div className="text-[11px] text-ink-subtle mt-1 flex items-center gap-1">
            <span className="text-accent-emerald font-semibold">{salesReport?.total_orders || 0} completed orders</span>
          </div>
        </div>

        {/* Active Dining Tables */}
        <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
          <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
            <span>Table Occupancy</span>
            <span className="p-1.5 rounded-lg bg-tint-brand text-accent-brand">
              <LayoutGrid className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black text-ink mt-2">
            {occupiedCount} <span className="text-xs text-ink-subtle font-normal">/ {tables.length} Total Tables</span>
          </div>
          <div className="text-[11px] text-ink-subtle mt-1">
            <span className="text-accent-emerald font-medium">{availableCount} available</span> • {tables.filter(t => t.status === "Reserved").length} reserved
          </div>
        </div>

        {/* Live Kitchen Orders */}
        <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
          <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
            <span>Active Kitchen KOTs</span>
            <span className="p-1.5 rounded-lg bg-tint-sky text-accent-sky">
              <MonitorCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black text-accent-sky mt-2">
            {kots.length}
          </div>
          <div className="text-[11px] text-ink-subtle mt-1">
            {kots.filter(k => k.status === "Preparing").length} currently in preparation
          </div>
        </div>

        {/* Average Order Value */}
        <div className="p-5 rounded-2xl bg-panel border border-line shadow-sm">
          <div className="flex items-center justify-between text-ink-muted text-xs font-semibold">
            <span>Average Order Value (AOV)</span>
            <span className="p-1.5 rounded-lg bg-tint-purple text-accent-purple">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black text-ink mt-2">
            ₹{salesReport?.average_order_value || "0.00"}
          </div>
          <div className="text-[11px] text-ink-subtle mt-1">
            Discounts: ₹{salesReport?.total_discounts || "0.00"}
          </div>
        </div>
      </div>

      {/* Middle Split: Live Kitchen Ticket Board & Floor Occupancy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active KOTs Quick Pipeline */}
        <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-ink">Live Kitchen Display Pipeline</h2>
              <p className="text-xs text-ink-muted">Current active tickets cooking across stations</p>
            </div>
            <Link href="/app/kitchen" className="text-xs font-semibold text-accent-brand hover:underline">
              View KDS Board →
            </Link>
          </div>

          {kots.length === 0 ? (
            <div className="p-8 text-center text-xs text-ink-subtle bg-well rounded-xl border border-line">
              No active KOTs in the kitchen right now.
            </div>
          ) : (
            <div className="space-y-3">
              {kots.slice(0, 4).map((kot) => (
                <div key={kot.id} className="p-3.5 rounded-xl bg-well border border-line flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-ink">{kot.kot_number}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-control text-ink-3 font-semibold border border-line-strong">
                        {kot.station_name || "Main Kitchen"}
                      </span>
                    </div>
                    <div className="text-[11px] text-ink-muted mt-1">
                      {kot.items.map((i: any) => `${i.quantity}x ${i.item_name}`).join(", ")}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                      kot.status === "Preparing" ? "bg-tint-amber text-accent-amber border border-tint-amber-border" :
                      kot.status === "Ready" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                      "bg-tint-sky text-accent-sky border border-tint-sky-border"
                    }`}>
                      {kot.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Visual Floor Status Snapshot */}
        <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-ink">Table Floor Plan Snapshot</h2>
              <p className="text-xs text-ink-muted">Real-time table status and seating</p>
            </div>
            <Link href="/app/tables" className="text-xs font-semibold text-accent-brand hover:underline">
              Manage Tables →
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {tables.slice(0, 8).map((tbl) => {
              const isOccupied = tbl.status === "Occupied";
              const isReserved = tbl.status === "Reserved";
              const isCleaning = tbl.status === "Cleaning";
              return (
                <div
                  key={tbl.id}
                  className={`p-3 rounded-xl border text-center transition ${
                    isOccupied ? "bg-tint-amber border-tint-amber-border text-accent-amber" :
                    isReserved ? "bg-tint-blue border-tint-blue-border text-accent-blue" :
                    isCleaning ? "bg-tint-purple border-tint-purple-border text-accent-purple" :
                    "bg-tint-emerald border-tint-emerald-border text-accent-emerald"
                  }`}
                >
                  <div className="text-xs font-black">{tbl.table_number}</div>
                  <div className="text-[10px] text-ink-muted mt-0.5">{tbl.capacity} Seats</div>
                  <div className="text-[9px] uppercase font-bold mt-1 tracking-wider">{tbl.status}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Orders Live Table */}
      <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-ink">Recent POS & Online Orders</h2>
            <p className="text-xs text-ink-muted">Latest transactions processed at this branch</p>
          </div>
          <Link href="/app/orders" className="text-xs font-semibold text-accent-brand hover:underline">
            View All Invoices →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Order Number</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Table / Customer</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {recentOrders.map((ord) => (
                <tr key={ord.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-3 font-bold text-ink">{ord.order_number}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-control text-ink-3 text-[10px]">
                      {ord.order_type}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-ink-3">
                    {ord.table_number ? `Table ${ord.table_number}` : ord.customer_name || "Walk-in"}
                  </td>
                  <td className="py-3 px-3 font-bold text-ink">
                    ₹{ord.total_amount.toFixed(2)}
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      ord.status === "Completed" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                      ord.status === "InKitchen" ? "bg-tint-amber text-accent-amber border border-tint-amber-border" :
                      "bg-control text-ink-3"
                    }`}>
                      {ord.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right text-ink-subtle text-[11px]">
                    {new Date(ord.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
