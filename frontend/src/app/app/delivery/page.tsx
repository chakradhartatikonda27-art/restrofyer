"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function DeliveryManagementPage() {
  const [deliveryOrders, setDeliveryOrders] = useState<any[]>([]);
  const [executives, setExecutives] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [selectedRiderId, setSelectedRiderId] = useState("");

  useEffect(() => {
    loadDeliveryData();
  }, []);

  const loadDeliveryData = async () => {
    setLoading(true);
    try {
      const [orders, execs] = await Promise.all([
        apiRequest("/delivery/orders"),
        apiRequest("/delivery/executives")
      ]);
      setDeliveryOrders(orders);
      setExecutives(execs);
      if (execs.length > 0 && !selectedRiderId) {
        setSelectedRiderId(execs[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRider = async (orderId: string) => {
    const rider = executives.find(e => e.id === selectedRiderId);
    if (!rider) return;
    try {
      await apiRequest(`/delivery/orders/${orderId}/assign`, {
        method: "POST",
        body: JSON.stringify({ rider_id: rider.id, rider_name: rider.name })
      });
      setSelectedOrder(null);
      await loadDeliveryData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleStatusUpdate = async (orderId: string, nextStatus: string) => {
    try {
      await apiRequest(`/delivery/orders/${orderId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      await loadDeliveryData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-ink tracking-tight">Delivery Dispatch & Rider Management</h1>
        <p className="text-xs text-ink-muted mt-1">Live dispatch pipeline for takeaway and home delivery orders.</p>
      </div>

      {/* Delivery Orders Board */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-line flex items-center justify-between">
          <h2 className="text-base font-bold text-ink">Active Delivery Orders</h2>
          <span className="text-xs text-ink-muted">{deliveryOrders.length} orders in pipeline</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Customer & Phone</th>
                <th className="py-3 px-4">Delivery Address</th>
                <th className="py-3 px-4">Assigned Rider</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Delivery Fee</th>
                <th className="py-3 px-4 text-right">Dispatch Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {deliveryOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-subtle">
                    No active delivery orders pending dispatch.
                  </td>
                </tr>
              ) : (
                deliveryOrders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-row-hover transition">
                    <td className="py-3 px-4">
                      <div className="font-bold text-ink">{ord.customer_name}</div>
                      <div className="text-[10px] text-ink-muted">{ord.customer_phone}</div>
                    </td>
                    <td className="py-3 px-4 text-ink-3 max-w-xs truncate">
                      {ord.delivery_address}
                    </td>
                    <td className="py-3 px-4 text-ink-3">
                      {ord.rider_name || (
                        <button
                          onClick={() => setSelectedOrder(ord)}
                          className="text-[11px] font-bold text-accent-brand hover:underline"
                        >
                          + Assign Rider
                        </button>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        ord.status === "Delivered" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                        ord.status === "OutForDelivery" ? "bg-tint-amber text-accent-amber border border-tint-amber-border" :
                        "bg-control text-ink-3"
                      }`}>
                        {ord.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-ink">₹{ord.delivery_fee.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right space-x-1.5">
                      {ord.status === "Assigned" && (
                        <button
                          onClick={() => handleStatusUpdate(ord.id, "PickedUp")}
                          className="px-2.5 py-1 rounded bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold"
                        >
                          Picked Up
                        </button>
                      )}
                      {ord.status === "PickedUp" && (
                        <button
                          onClick={() => handleStatusUpdate(ord.id, "OutForDelivery")}
                          className="px-2.5 py-1 rounded bg-amber-500 text-slate-950 font-bold text-xs"
                        >
                          Out for Delivery
                        </button>
                      )}
                      {ord.status === "OutForDelivery" && (
                        <button
                          onClick={() => handleStatusUpdate(ord.id, "Delivered")}
                          className="px-2.5 py-1 rounded bg-emerald-600 text-white font-bold text-xs"
                        >
                          Mark Delivered
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assign Rider Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Assign Delivery Rider</h3>
              <button onClick={() => setSelectedOrder(null)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Select Active Executive</label>
              <select
                value={selectedRiderId}
                onChange={(e) => setSelectedRiderId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                {executives.map(e => <option key={e.id} value={e.id}>{e.name} ({e.phone})</option>)}
              </select>
            </div>

            <button
              onClick={() => handleAssignRider(selectedOrder.id)}
              className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
            >
              Confirm Rider Assignment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
