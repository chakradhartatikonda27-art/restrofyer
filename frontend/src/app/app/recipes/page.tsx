"use client";

import { useEffect, useState } from "react";
import {
  Plus, Trash2, ChevronRight
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function RecipeCostingPage() {
  const [menuItems, setMenuItems] = useState<any[]>([]);
  const [inventoryItems, setInventoryItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [recipe, setRecipe] = useState<any | null>(null);
  const [recipeItems, setRecipeItems] = useState<any[]>([]);
  const [yieldPortions, setYieldPortions] = useState<number>(1);
  const [instructions, setInstructions] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [itemsData, invData] = await Promise.all([
        apiRequest("/menus/items"),
        apiRequest("/inventory/items")
      ]);
      setMenuItems(itemsData);
      setInventoryItems(invData);
      if (itemsData.length > 0) {
        selectMenuItem(itemsData[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectMenuItem = async (item: any) => {
    setSelectedItem(item);
    try {
      const rec = await apiRequest(`/recipes/${item.id}`);
      setRecipe(rec);
      setYieldPortions(rec.yield_portions);
      setInstructions(rec.instructions || "");
      setRecipeItems(rec.items.map((it: any) => ({
        inventory_item_id: it.inventory_item_id,
        item_name: it.item_name,
        quantity: it.quantity,
        uom: it.uom
      })));
    } catch {
      setRecipe(null);
      setYieldPortions(1);
      setInstructions("");
      setRecipeItems([]);
    }
  };

  const addIngredientRow = () => {
    if (inventoryItems.length === 0) return;
    const first = inventoryItems[0];
    setRecipeItems([...recipeItems, {
      inventory_item_id: first.id,
      item_name: first.name,
      quantity: 0.1,
      uom: first.uom
    }]);
  };

  const updateIngredientRow = (idx: number, field: string, val: any) => {
    setRecipeItems(prev => prev.map((row, i) => {
      if (i === idx) {
        if (field === "inventory_item_id") {
          const inv = inventoryItems.find(it => it.id === val);
          return { ...row, inventory_item_id: val, item_name: inv?.name || "Unknown", uom: inv?.uom || "kg" };
        }
        return { ...row, [field]: val };
      }
      return row;
    }));
  };

  const removeIngredientRow = (idx: number) => {
    setRecipeItems(prev => prev.filter((_, i) => i !== idx));
  };

  const handleSaveRecipe = async () => {
    if (!selectedItem) return;
    setSaving(true);
    try {
      const saved = await apiRequest("/recipes", {
        method: "POST",
        body: JSON.stringify({
          menu_item_id: selectedItem.id,
          yield_portions: yieldPortions,
          instructions,
          items: recipeItems.map(it => ({
            inventory_item_id: it.inventory_item_id,
            quantity: parseFloat(it.quantity) || 0,
            uom: it.uom
          }))
        })
      });
      setRecipe(saved);
      alert("Recipe Bill of Materials and Food Costing saved successfully!");
      const updatedItems = await apiRequest("/menus/items");
      setMenuItems(updatedItems);
      setSelectedItem(updatedItems.find((i: any) => i.id === selectedItem.id) || selectedItem);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const totalBatchCost = recipeItems.reduce((acc, row) => {
    const inv = inventoryItems.find(i => i.id === row.inventory_item_id);
    const unitCost = inv ? inv.cost_per_unit : 0;
    return acc + (parseFloat(row.quantity) || 0) * unitCost;
  }, 0);

  const costPerPortion = yieldPortions > 0 ? totalBatchCost / yieldPortions : 0;
  const sellingPrice = selectedItem ? selectedItem.base_price : 0;
  const grossProfit = sellingPrice - costPerPortion;
  const grossMarginPct = sellingPrice > 0 ? (grossProfit / sellingPrice) * 100 : 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-black text-ink tracking-tight">Recipe Bill of Materials (BOM) & Food Costing</h1>
        <p className="text-xs text-ink-muted mt-1">Engineer dish ingredients, calculate exact portion costs, and automate real-time stock consumption.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Menu Item Selector */}
        <div className="bg-panel border border-line rounded-2xl p-4 shadow-sm flex flex-col h-[650px]">
          <h2 className="text-xs uppercase tracking-wider font-bold text-ink-muted px-2 mb-3">Select Menu Item</h2>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {menuItems.map((item) => (
              <div
                key={item.id}
                onClick={() => selectMenuItem(item)}
                className={`p-3 rounded-xl border text-left cursor-pointer transition select-none flex items-center justify-between ${
                  selectedItem?.id === item.id
                    ? "bg-tint-brand border-brand-500 text-accent-brand shadow-sm"
                    : "bg-well border-line text-ink-3 hover:bg-control"
                }`}
              >
                <div>
                  <div className="text-xs font-bold">{item.name}</div>
                  <div className="text-[10px] text-ink-subtle mt-0.5">Price: ₹{item.base_price.toFixed(2)}</div>
                </div>
                <ChevronRight className="w-4 h-4 text-ink-subtle" />
              </div>
            ))}
          </div>
        </div>

        {/* Right 2 Columns: Recipe BOM Builder & Cost Card */}
        {selectedItem && (
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
                <span className="text-[10px] uppercase font-bold text-ink-subtle">Menu Price</span>
                <div className="text-xl font-black text-ink mt-1">₹{sellingPrice.toFixed(2)}</div>
              </div>
              <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
                <span className="text-[10px] uppercase font-bold text-ink-subtle">Raw Ingredient Cost</span>
                <div className="text-xl font-black text-accent-amber mt-1">₹{costPerPortion.toFixed(2)}</div>
              </div>
              <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
                <span className="text-[10px] uppercase font-bold text-ink-subtle">Gross Margin %</span>
                <div className={`text-xl font-black mt-1 ${grossMarginPct >= 65 ? "text-accent-emerald" : "text-accent-amber"}`}>
                  {grossMarginPct.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Recipe Ingredients Builder */}
            <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-ink">Bill of Materials for: {selectedItem.name}</h3>
                  <p className="text-xs text-ink-muted">Specify raw ingredients consumed each time this dish is ordered</p>
                </div>
                <button
                  type="button"
                  onClick={addIngredientRow}
                  className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 transition"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Ingredient
                </button>
              </div>

              <div className="space-y-2">
                {recipeItems.map((row, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2.5 rounded-xl bg-well border border-line">
                    <select
                      value={row.inventory_item_id}
                      onChange={(e) => updateIngredientRow(idx, "inventory_item_id", e.target.value)}
                      className="flex-1 px-3 py-1.5 bg-panel border border-input-border rounded-lg text-xs text-ink"
                    >
                      {inventoryItems.map(inv => (
                        <option key={inv.id} value={inv.id}>
                          {inv.name} (₹{inv.cost_per_unit}/{inv.uom})
                        </option>
                      ))}
                    </select>

                    <div className="flex items-center gap-1.5 w-36">
                      <input
                        type="number"
                        step="0.001"
                        value={row.quantity}
                        onChange={(e) => updateIngredientRow(idx, "quantity", e.target.value)}
                        className="w-20 px-2 py-1.5 bg-panel border border-input-border rounded-lg text-xs text-ink text-right font-mono"
                      />
                      <span className="text-xs text-ink-muted font-bold">{row.uom}</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => removeIngredientRow(idx)}
                      className="p-1.5 text-ink-subtle hover:text-accent-rose"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}

                {recipeItems.length === 0 && (
                  <div className="p-8 text-center text-xs text-ink-subtle border border-dashed border-line-strong rounded-xl">
                    No ingredients added yet. Click &quot;Add Ingredient&quot; above to link raw materials to this dish.
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-ink-muted mb-1">Chef Prep & Cooking Instructions</label>
                <textarea
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Roll 250g dough ball to 12 inches, bake in woodfire oven at 450°C for 90 seconds..."
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>

              <button
                type="button"
                disabled={saving || recipeItems.length === 0}
                onClick={handleSaveRecipe}
                className="w-full py-3 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition disabled:opacity-50"
              >
                {saving ? "Saving BOM..." : "Save Recipe & Update Food Costing"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
