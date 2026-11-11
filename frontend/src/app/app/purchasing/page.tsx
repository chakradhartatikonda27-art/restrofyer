"use client";

import { useEffect, useState } from "react";
import {
  Plus, CheckCircle2, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function PurchasingPage() {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [inventoryItems, setInventoryItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [supName, setSupName] = useState("");
  const [supContact, setSupContact] = useState("");
  const [supPhone, setSupPhone] = useState("");
  const [supEmail] = useState("");
  const [supTerms] = useState("Net 30 Days");

  const [showPOModal, setShowPOModal] = useState(false);
  const [poSupplierId, setPoSupplierId] = useState("");
  const [poItems, setPoItems] = useState<any[]>([]);

  useEffect(() => {
    loadProcurement();
  }, []);

  const loadProcurement = async () => {
    setLoading(true);
    try {
      const [sups, pos, inv] = await Promise.all([
        apiRequest("/procurement/suppliers"),
        apiRequest("/procurement/purchase-orders"),
        apiRequest("/inventory/items")
      ]);
      setSuppliers(sups);
      setPurchaseOrders(pos);
      setInventoryItems(inv);
      if (sups.length > 0 && !poSupplierId) {
        setPoSupplierId(sups[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/procurement/suppliers", {
        method: "POST",
        body: JSON.stringify({
          name: supName,
          contact_name: supContact,
          phone: supPhone,
          email: supEmail || null,
          payment_terms: supTerms
        })
      });
      setShowSupplierModal(false);
      setSupName("");
      setSupPhone("");
      await loadProcurement();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const addPOItemRow = () => {
    if (inventoryItems.length === 0) return;
    const first = inventoryItems[0];
    setPoItems([...poItems, {
      inventory_item_id: first.id,
      item_name: first.name,
      quantity: 10,
      unit_price: first.cost_per_unit
    }]);
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/procurement/purchase-orders", {
        method: "POST",
        body: JSON.stringify({
          supplier_id: poSupplierId,
          items: poItems
        })
      });
      setShowPOModal(false);
      setPoItems([]);
      await loadProcurement();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReceiveGoods = async (poId: string) => {
    if (!confirm("Confirm Goods Receipt Note (GRN)? This will immediately increment raw material inventory balances.")) return;
    try {
      const res = await apiRequest("/procurement/goods-receipts", {
        method: "POST",
        body: JSON.stringify({ po_id: poId, notes: "Verified delivery against PO invoice" })
      });
      alert(`Success! ${res.message} (GRN: ${res.grn_number})`);
      await loadProcurement();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Procurement, Suppliers & Goods Receiving (GRN)</h1>
          <p className="text-xs text-ink-muted mt-1">Vendor catalogs, automated stock receipts, and purchase orders.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSupplierModal(true)}
            className="px-3.5 py-2 bg-control hover:bg-control-hover text-ink-2 border border-line-strong rounded-xl text-xs font-bold transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Vendor
          </button>
          <button
            onClick={() => { setShowPOModal(true); if (poItems.length === 0) addPOItemRow(); }}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Create Purchase Order
          </button>
        </div>
      </div>

      {/* Purchase Orders Table */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-line flex items-center justify-between">
          <h2 className="text-base font-bold text-ink">Purchase Orders & Deliveries</h2>
          <span className="text-xs text-ink-muted">{purchaseOrders.length} total POs</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">PO Number</th>
                <th className="py-3 px-4">Supplier</th>
                <th className="py-3 px-4">Items Ordered</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {purchaseOrders.map((po) => {
                const sup = suppliers.find(s => s.id === po.supplier_id);
                return (
                  <tr key={po.id} className="hover:bg-row-hover transition">
                    <td className="py-3 px-4 font-bold text-ink">{po.po_number}</td>
                    <td className="py-3 px-4 text-ink-3">{sup?.name || "Vendor"}</td>
                    <td className="py-3 px-4 text-ink-muted">
                      {po.items.map((i: any) => `${i.quantity} ${i.item_name}`).join(", ")}
                    </td>
                    <td className="py-3 px-4 font-black text-ink">
                      ₹{po.total_amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        po.status === "Received" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                        "bg-tint-amber text-accent-amber border border-tint-amber-border"
                      }`}>
                        {po.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-ink-subtle text-[11px]">
                      {new Date(po.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {po.status !== "Received" ? (
                        <button
                          onClick={() => handleReceiveGoods(po.id)}
                          className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition shadow-sm"
                        >
                          Receive Goods (GRN)
                        </button>
                      ) : (
                        <span className="text-[11px] text-accent-emerald font-bold flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Stock Updated
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Suppliers Grid */}
      <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm">
        <h2 className="text-base font-bold text-ink mb-4">Approved Vendor Directory</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suppliers.map((s) => (
            <div key={s.id} className="p-4 rounded-xl bg-well border border-line space-y-1.5 text-xs">
              <div className="font-bold text-sm text-ink">{s.name}</div>
              <div className="text-ink-muted">Contact: {s.contact_name || "Sales Rep"}</div>
              <div className="text-ink-muted">Phone: {s.phone}</div>
              <div className="text-[10px] text-accent-brand font-semibold">{s.payment_terms}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Supplier Modal */}
      {showSupplierModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateSupplier} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Add Vendor Profile</h3>
              <button type="button" onClick={() => setShowSupplierModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Company / Supplier Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Royal Fresh Farm Supplies"
                value={supName}
                onChange={(e) => setSupName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Contact Person</label>
              <input
                type="text"
                placeholder="e.g. Rahul Sharma"
                value={supContact}
                onChange={(e) => setSupContact(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Phone Number</label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={supPhone}
                onChange={(e) => setSupPhone(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Save Supplier
            </button>
          </form>
        </div>
      )}

      {/* Create PO Modal */}
      {showPOModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreatePO} className="bg-panel border border-line rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Create Purchase Order (PO)</h3>
              <button type="button" onClick={() => setShowPOModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Select Supplier</label>
              <select
                value={poSupplierId}
                onChange={(e) => setPoSupplierId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                {suppliers.map(s => <option key={s.id} value={s.id}>{s.name} ({s.payment_terms})</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-bold text-ink-3">
                <span>Items to Purchase</span>
                <button type="button" onClick={addPOItemRow} className="text-accent-brand hover:underline">
                  + Add Item
                </button>
              </div>

              {poItems.map((row, idx) => (
                <div key={idx} className="flex gap-2">
                  <select
                    value={row.inventory_item_id}
                    onChange={(e) => {
                      const inv = inventoryItems.find(i => i.id === e.target.value);
                      const copy = [...poItems];
                      copy[idx] = { ...copy[idx], inventory_item_id: inv.id, item_name: inv.name, unit_price: inv.cost_per_unit };
                      setPoItems(copy);
                    }}
                    className="flex-1 px-2.5 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink"
                  >
                    {inventoryItems.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                  </select>

                  <input
                    type="number"
                    step="0.1"
                    placeholder="Qty"
                    value={row.quantity}
                    onChange={(e) => {
                      const copy = [...poItems];
                      copy[idx].quantity = parseFloat(e.target.value) || 0;
                      setPoItems(copy);
                    }}
                    className="w-20 px-2 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink text-right font-mono"
                  />

                  <input
                    type="number"
                    step="0.01"
                    placeholder="Rate"
                    value={row.unit_price}
                    onChange={(e) => {
                      const copy = [...poItems];
                      copy[idx].unit_price = parseFloat(e.target.value) || 0;
                      setPoItems(copy);
                    }}
                    className="w-24 px-2 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink text-right font-mono"
                  />
                </div>
              ))}
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Issue Purchase Order
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
