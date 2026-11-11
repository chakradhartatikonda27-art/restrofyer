"use client";

import { useEffect, useState } from "react";
import {
  Search, Printer, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function OrdersAndBillingPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [orderTypeFilter, setOrderTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);

  useEffect(() => {
    loadOrders();
  }, [statusFilter, orderTypeFilter]);

  const loadOrders = async () => {
    setLoading(true);
    try {
      let query = "/orders?limit=100";
      if (statusFilter) query += `&status_filter=${statusFilter}`;
      if (orderTypeFilter) query += `&order_type=${orderTypeFilter}`;
      const data = await apiRequest(query);
      setOrders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = orders.filter(o =>
    o.order_number.toLowerCase().includes(search.toLowerCase()) ||
    (o.customer_name && o.customer_name.toLowerCase().includes(search.toLowerCase())) ||
    (o.table_number && o.table_number.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Orders, Invoices & Billing</h1>
          <p className="text-xs text-ink-muted mt-1">Audit log of all dine-in, takeaway, and online orders with itemized invoices.</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-panel border border-line flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search order #, customer, table..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink-3"
          >
            <option value="">All Statuses</option>
            <option value="Completed">Completed</option>
            <option value="InKitchen">InKitchen</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Cancelled">Cancelled</option>
          </select>

          <select
            value={orderTypeFilter}
            onChange={(e) => setOrderTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink-3"
          >
            <option value="">All Types</option>
            <option value="DineIn">DineIn</option>
            <option value="Takeaway">Takeaway</option>
            <option value="Delivery">Delivery</option>
            <option value="QR">QR Table</option>
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Order #</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Table / Guest</th>
                <th className="py-3 px-4">Items</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Cashier</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filteredOrders.map((ord) => (
                <tr key={ord.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-4 font-bold text-ink">{ord.order_number}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-control text-ink-3 font-semibold text-[10px]">
                      {ord.order_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-ink-3">
                    {ord.table_number ? `Table ${ord.table_number}` : ord.customer_name || "Walk-in"}
                  </td>
                  <td className="py-3 px-4 text-ink-muted truncate max-w-xs">
                    {ord.items.map((i: any) => `${i.quantity}x ${i.item_name}`).join(", ")}
                  </td>
                  <td className="py-3 px-4 font-black text-ink">
                    ₹{ord.total_amount.toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      ord.status === "Completed" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                      ord.status === "InKitchen" ? "bg-tint-amber text-accent-amber border border-tint-amber-border" :
                      "bg-control text-ink-3"
                    }`}>
                      {ord.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-ink-muted">{ord.cashier_name || "N/A"}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setSelectedOrder(ord)}
                      className="px-2.5 py-1 rounded-lg bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold transition"
                    >
                      View Invoice
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoice Detail Drawer Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Invoice Details</h3>
                <p className="text-xs text-ink-muted font-mono">{selectedOrder.order_number}</p>
              </div>
              <button onClick={() => setSelectedOrder(null)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-well border border-line text-xs space-y-2">
              <div className="flex justify-between text-ink-muted">
                <span>Date & Time</span>
                <span>{new Date(selectedOrder.created_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>Table / Guest</span>
                <span className="font-semibold text-ink">{selectedOrder.table_number ? `Table ${selectedOrder.table_number}` : selectedOrder.customer_name || 'Guest'}</span>
              </div>
              <div className="py-2 border-y border-line space-y-1.5">
                {selectedOrder.items.map((it: any) => (
                  <div key={it.id} className="flex justify-between text-ink-2">
                    <span>{it.quantity}x {it.item_name}</span>
                    <span>₹{it.subtotal.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>Subtotal</span>
                <span>₹{selectedOrder.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>Discount</span>
                <span>-₹{selectedOrder.discount_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>GST (5%)</span>
                <span>₹{selectedOrder.tax_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>Service Charge</span>
                <span>₹{selectedOrder.service_charge.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-sm text-accent-brand pt-2 border-t border-line">
                <span>Total Amount Paid</span>
                <span>₹{selectedOrder.total_amount.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={() => window.print()}
              className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition flex items-center justify-center gap-1.5"
            >
              <Printer className="w-4 h-4" /> Print Tax Receipt
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
