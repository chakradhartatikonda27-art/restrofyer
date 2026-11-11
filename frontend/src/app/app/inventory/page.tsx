"use client";

import { useEffect, useState } from "react";
import {
  Plus, AlertTriangle, Search, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function InventoryManagementPage() {
  const [items, setItems] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [lowStockFilter, setLowStockFilter] = useState(false);
  const [loading, setLoading] = useState(true);

  const [showAddModal, setShowAddModal] = useState(false);
  const [itemName, setItemName] = useState("");
  const [sku, setSku] = useState("");
  const [uom, setUom] = useState("kg");
  const [currentStock, setCurrentStock] = useState<number>(10);
  const [minStock, setMinStock] = useState<number>(5);
  const [costPerUnit, setCostPerUnit] = useState<number>(100);
  const [location, setLocation] = useState("Walk-in Cooler");

  const [adjustItem, setAdjustItem] = useState<any | null>(null);
  const [adjustQty, setAdjustQty] = useState<number>(0);
  const [adjustType, setAdjustType] = useState<string>("ADJUSTMENT");
  const [adjustNotes, setAdjustNotes] = useState<string>("");

  useEffect(() => {
    loadInventory();
  }, [lowStockFilter]);

  const loadInventory = async () => {
    setLoading(true);
    try {
      const query = `/inventory/items${lowStockFilter ? '?low_stock_only=true' : ''}`;
      const data = await apiRequest(query);
      setItems(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/inventory/items", {
        method: "POST",
        body: JSON.stringify({
          name: itemName,
          sku: sku || null,
          uom,
          current_stock: currentStock,
          minimum_stock: minStock,
          cost_per_unit: costPerUnit,
          storage_location: location
        })
      });
      setShowAddModal(false);
      setItemName("");
      setSku("");
      await loadInventory();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleStockAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem) return;
    try {
      await apiRequest("/inventory/movements", {
        method: "POST",
        body: JSON.stringify({
          inventory_item_id: adjustItem.id,
          movement_type: adjustType,
          quantity: adjustQty,
          notes: adjustNotes || "Manual stock reconciliation"
        })
      });
      setAdjustItem(null);
      setAdjustQty(0);
      setAdjustNotes("");
      await loadInventory();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const filteredItems = items.filter(i =>
    i.name.toLowerCase().includes(search.toLowerCase()) ||
    (i.sku && i.sku.toLowerCase().includes(search.toLowerCase()))
  );

  const lowStockCount = items.filter(i => i.is_low_stock).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Raw Materials & Inventory Control</h1>
          <p className="text-xs text-ink-muted mt-1">Real-time ingredient stock, automated order consumption, and wastage reconciliation.</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add Raw Ingredient
        </button>
      </div>

      {/* Filter and KPI Strip */}
      <div className="p-4 rounded-2xl bg-panel border border-line flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search ingredient or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <button
            onClick={() => setLowStockFilter(!lowStockFilter)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition flex items-center gap-1.5 ${
              lowStockFilter
                ? "bg-tint-amber border-amber-500 text-accent-amber"
                : "bg-well border-line text-ink-muted hover:text-ink"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-accent-amber" />
            <span>Low Stock Only ({lowStockCount})</span>
          </button>
        </div>

        <div className="text-xs text-ink-muted font-semibold">
          Total Ingredients: <span className="text-ink">{items.length}</span>
        </div>
      </div>

      {/* Inventory Items Table */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Ingredient Name</th>
                <th className="py-3 px-4">SKU</th>
                <th className="py-3 px-4">Storage Location</th>
                <th className="py-3 px-4">Current Stock</th>
                <th className="py-3 px-4">Min. Threshold</th>
                <th className="py-3 px-4">Unit Cost</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-4 font-bold text-ink">{item.name}</td>
                  <td className="py-3 px-4 font-mono text-ink-muted text-[11px]">{item.sku || "N/A"}</td>
                  <td className="py-3 px-4 text-ink-3">{item.storage_location}</td>
                  <td className="py-3 px-4 font-black text-ink">
                    {item.current_stock.toFixed(2)} {item.uom}
                  </td>
                  <td className="py-3 px-4 text-ink-muted">
                    {item.minimum_stock.toFixed(2)} {item.uom}
                  </td>
                  <td className="py-3 px-4 text-ink-3">
                    ₹{item.cost_per_unit.toFixed(2)} / {item.uom}
                  </td>
                  <td className="py-3 px-4">
                    {item.is_low_stock ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-tint-amber border border-tint-amber-border text-accent-amber">
                        <AlertTriangle className="w-3 h-3" /> Reorder Needed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-tint-emerald border border-tint-emerald-border text-accent-emerald">
                        Optimal Stock
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setAdjustItem(item)}
                      className="px-2.5 py-1 rounded-lg bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold transition"
                    >
                      Adjust Stock
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Stock Adjustment Modal */}
      {adjustItem && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleStockAdjustment} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Adjust Stock Balance</h3>
                <p className="text-xs text-ink-muted">{adjustItem.name} (Current: {adjustItem.current_stock} {adjustItem.uom})</p>
              </div>
              <button type="button" onClick={() => setAdjustItem(null)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Reason / Movement Type</label>
              <select
                value={adjustType}
                onChange={(e) => setAdjustType(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                <option value="PURCHASE_RECEIPT">Purchase Receipt (Stock In)</option>
                <option value="ADJUSTMENT">Manual Count Adjustment</option>
                <option value="WASTAGE">Wastage / Spoilage (Stock Out)</option>
                <option value="SALES_CONSUMPTION">Kitchen Tasting / Internal Meal</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">
                Quantity to Add (+) or Deduct (-) in {adjustItem.uom}
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={adjustQty}
                onChange={(e) => setAdjustQty(parseFloat(e.target.value) || 0)}
                placeholder="e.g. +5.0 or -2.5"
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Notes / Audit Justification</label>
              <input
                type="text"
                required
                placeholder="Reason for variance..."
                value={adjustNotes}
                onChange={(e) => setAdjustNotes(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Confirm Stock Movement
            </button>
          </form>
        </div>
      )}

      {/* Add New Ingredient Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateItem} className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Add Raw Ingredient</h3>
              <button type="button" onClick={() => setShowAddModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Ingredient Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Extra Virgin Olive Oil"
                value={itemName}
                onChange={(e) => setItemName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">SKU / Code</label>
                <input
                  type="text"
                  placeholder="e.g. RAW-OIL-01"
                  value={sku}
                  onChange={(e) => setSku(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Unit of Measure (UOM)</label>
                <select
                  value={uom}
                  onChange={(e) => setUom(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                >
                  <option value="kg">Kilograms (kg)</option>
                  <option value="g">Grams (g)</option>
                  <option value="l">Liters (l)</option>
                  <option value="ml">Milliliters (ml)</option>
                  <option value="pcs">Pieces (pcs)</option>
                  <option value="box">Box</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Opening Stock</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={currentStock}
                  onChange={(e) => setCurrentStock(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Min. Alert</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={minStock}
                  onChange={(e) => setMinStock(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Cost / Unit (₹)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={costPerUnit}
                  onChange={(e) => setCostPerUnit(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Storage Location</label>
              <input
                type="text"
                placeholder="e.g. Dry Pantry Shelf 3"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Save Ingredient
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
