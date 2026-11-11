"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { apiRequest, API_BASE_URL } from "@/lib/api";
import { getStoredToken, getActiveBranch } from "@/lib/auth";

export default function ReportsAndAnalyticsPage() {
  const [salesData, setSalesData] = useState<any | null>(null);
  const [inventoryVal, setInventoryVal] = useState<any | null>(null);
  const [pnlData, setPnlData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const [sales, inv, pnl] = await Promise.all([
        apiRequest("/reports/sales"),
        apiRequest("/reports/inventory-valuation"),
        apiRequest("/reports/profit-loss")
      ]);
      setSalesData(sales);
      setInventoryVal(inv);
      setPnlData(pnl);
    } catch (err) {
      console.error("Reports loading error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    const token = getStoredToken();
    const branch = getActiveBranch();
    const url = `${API_BASE_URL}/reports/export/sales-csv`;

    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Branch-Id": branch || ""
      }
    })
      .then(res => res.blob())
      .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `sales_report_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Financial Analytics & Operational P&L</h1>
          <p className="text-xs text-ink-muted mt-1">Accurate database calculations for revenue, recipe food cost COGS, margins, and audit exports.</p>
        </div>

        <button
          onClick={handleExportCSV}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-600/20 transition flex items-center gap-1.5"
        >
          <Download className="w-4 h-4" /> Export Sales CSV
        </button>
      </div>

      {/* P&L Statement Card */}
      {pnlData && (
        <div className="p-6 rounded-2xl bg-panel border border-line shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <div>
              <h2 className="text-base font-bold text-ink">Operational Profit & Loss Statement (P&L)</h2>
              <p className="text-xs text-ink-muted">Recipe BOM ingredient COGS matched against realized billing</p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-tint-brand text-accent-brand border border-tint-brand-border">
              Gross Margin: {pnlData.gross_margin_percentage}%
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="p-3.5 rounded-xl bg-well border border-line">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Total Revenue</span>
              <div className="text-lg font-black text-ink mt-1">₹{pnlData.total_revenue.toLocaleString()}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-well border border-line">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Cost of Goods (COGS)</span>
              <div className="text-lg font-black text-accent-rose mt-1">-₹{pnlData.cost_of_goods_sold.toLocaleString()}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-well border border-line">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Gross Profit</span>
              <div className="text-lg font-black text-accent-emerald mt-1">₹{pnlData.gross_profit.toLocaleString()}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-well border border-line">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Operating Expenses</span>
              <div className="text-lg font-black text-accent-amber mt-1">-₹{pnlData.total_operating_expenses.toLocaleString()}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-tint-brand border border-tint-brand-border">
              <span className="text-[10px] uppercase font-bold text-accent-brand">Net Operating Profit</span>
              <div className="text-lg font-black text-accent-brand mt-1">₹{pnlData.net_operating_profit.toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}

      {/* Sales Summary & Top Items Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-ink">Revenue by Order Type & Payment</h3>

          {salesData && (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-semibold text-ink-muted mb-2 block">Order Types Breakdown</span>
                <div className="space-y-2">
                  {Object.entries(salesData.sales_by_order_type || {}).map(([type, amt]: [string, any]) => (
                    <div key={type} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-well border border-line">
                      <span className="font-semibold text-ink">{type}</span>
                      <span className="font-bold text-accent-brand">₹{amt.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-xs font-semibold text-ink-muted mb-2 block">Payment Methods Breakdown</span>
                <div className="space-y-2">
                  {Object.entries(salesData.sales_by_payment_method || {}).map(([method, amt]: [string, any]) => (
                    <div key={method} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-well border border-line">
                      <span className="font-semibold text-ink">{method}</span>
                      <span className="font-bold text-accent-emerald">₹{amt.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-ink">Best-Selling Menu Items</h3>
          <div className="space-y-2.5">
            {salesData?.top_selling_items?.map((item: any, idx: number) => (
              <div key={idx} className="p-3 rounded-xl bg-well border border-line flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-lg bg-tint-brand text-accent-brand font-bold flex items-center justify-center text-xs">
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="font-bold text-ink">{item.name}</div>
                    <div className="text-[10px] text-ink-subtle">{item.quantity} orders fulfilled</div>
                  </div>
                </div>
                <div className="text-right font-black text-ink">
                  ₹{item.revenue.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Inventory On-Hand Valuation Card */}
      {inventoryVal && (
        <div className="p-6 rounded-2xl bg-panel border border-line shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] uppercase font-bold text-ink-subtle">Warehouse Valuation</span>
            <h3 className="text-base font-bold text-ink mt-0.5">Total Raw Inventory Value On-Hand</h3>
            <p className="text-xs text-ink-muted mt-1">Calculated across {inventoryVal.total_items_count} tracked raw materials</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-black text-accent-emerald">
              ₹{inventoryVal.total_inventory_value.toLocaleString()}
            </div>
            <div className="text-xs text-accent-amber font-semibold mt-0.5">
              {inventoryVal.low_stock_items_count} items below reorder threshold
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
