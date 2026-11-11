"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ShoppingBag, CheckCircle2, Plus, Minus, ArrowRight, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";
import { FOOD_TYPE_OPTIONS } from "@/components/menu/MenuTypes";
import { DietaryBadge, DishThumbnail, resolveFoodType } from "@/components/menu/VegBadge";

export default function PublicStorefrontPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [menuData, setMenuData] = useState<any | null>(null);
  const [selectedCuisineId, setSelectedCuisineId] = useState<string>("all");
  const [selectedFoodType, setSelectedFoodType] = useState<string>("all");
  const [selectedCatId, setSelectedCatId] = useState<string>("all");
  const [cart, setCart] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCheckout, setShowCheckout] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [orderType, setOrderType] = useState("Takeaway");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [placedOrder, setPlacedOrder] = useState<any | null>(null);

  useEffect(() => {
    if (slug) {
      loadStorefront();
    }
  }, [slug]);

  const loadStorefront = async () => {
    setLoading(true);
    try {
      const data = await apiRequest(`/public/${slug}/menu`);
      setMenuData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (item: any) => {
    setCart(prev => {
      const existing = prev.find(i => i.id === item.id);
      if (existing) {
        return prev.map(i => i.id === item.id ? { ...i, quantity: i.quantity + 1, total: (i.quantity + 1) * i.base_price } : i);
      } else {
        return [...prev, { ...item, quantity: 1, total: item.base_price }];
      }
    });
  };

  const updateQuantity = (itemId: string, delta: number) => {
    setCart(prev => prev.map(item => {
      if (item.id === itemId) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty, total: newQty * item.base_price } : null;
      }
      return item;
    }).filter(Boolean));
  };

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await apiRequest(`/public/${slug}/orders`, {
        method: "POST",
        body: JSON.stringify({
          order_type: orderType,
          customer_name: customerName,
          customer_phone: customerPhone,
          notes: notes || null,
          items: cart.map(i => ({
            menu_item_id: i.id,
            quantity: i.quantity,
            modifiers: []
          }))
        })
      });
      setPlacedOrder(res);
      setShowCheckout(false);
      setCart([]);
    } catch (err: any) {
      alert(`Order submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const cartTotal = cart.reduce((a, b) => a + b.total, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas text-ink flex items-center justify-center text-sm font-semibold">
        Loading restaurant menu...
      </div>
    );
  }

  if (!menuData) {
    return (
      <div className="min-h-screen bg-canvas text-ink flex items-center justify-center text-sm">
        Restaurant storefront not found.
      </div>
    );
  }

  const allCuisines = menuData.cuisines || [];
  const allCategories = menuData.categories || [];
  const allItems = allCategories.flatMap((c: any) =>
    (c.items || []).map((it: any) => ({
      ...it,
      _catId: c.id,
      _parentCatId: c.parent_id,
      _catName: c.name,
    }))
  );
  const displayedItems = allItems.filter((item: any) => {
    if (selectedCuisineId !== "all" && item.cuisine_id !== selectedCuisineId) return false;
    if (selectedFoodType !== "all") {
      if (resolveFoodType(item.food_type, item.is_veg) !== selectedFoodType) return false;
    }
    if (selectedCatId !== "all") {
      if (item._catId !== selectedCatId && item._parentCatId !== selectedCatId) return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col">
      {/* Branded Banner */}
      <header
        style={{ backgroundImage: "linear-gradient(to right, var(--storefront-start), var(--color-panel), var(--color-canvas))" }}
        className="border-b border-line py-10 px-6"
      >
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-accent-brand">Online Ordering</span>
            <h1 className="text-3xl font-black text-ink mt-1">{menuData.restaurant_name}</h1>
            <p className="text-xs text-ink-muted mt-1">Freshly prepared artisanal dishes • Fast takeaway and pickup</p>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            {cart.length > 0 && (
              <button
                onClick={() => setShowCheckout(true)}
                className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-extrabold text-xs rounded-xl shadow-lg shadow-brand-500/25 flex items-center gap-2 transition"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>View Cart ({cart.reduce((a, b) => a + b.quantity, 0)} items • ₹{cartTotal.toFixed(2)})</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Storefront Area */}
      <main className="max-w-5xl mx-auto w-full p-6 space-y-5 flex-1">
        {/* Independent 3D Filters: Cuisine & Food Type */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-panel border border-line shadow-sm">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => setSelectedFoodType("all")}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                selectedFoodType === "all"
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-well text-ink-3 border-line hover:bg-control"
              }`}
            >
              All Food Types
            </button>
            {FOOD_TYPE_OPTIONS.map((ft) => {
              const active = selectedFoodType === ft.value;
              return (
                <button
                  key={ft.value}
                  type="button"
                  onClick={() => setSelectedFoodType(active ? "all" : ft.value)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                    active
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-well text-ink-2 border-line hover:bg-control"
                  }`}
                >
                  <DietaryBadge foodType={ft.value} />
                  <span>{ft.shortLabel}</span>
                </button>
              );
            })}
          </div>

          {allCuisines.length > 0 && (
            <select
              value={selectedCuisineId}
              onChange={(e) => setSelectedCuisineId(e.target.value)}
              aria-label="Filter by Cuisine"
              className="px-3 py-1.5 bg-well border border-input-border rounded-xl text-xs font-medium text-ink"
            >
              <option value="all">All Cuisines ({allCuisines.length})</option>
              {allCuisines.map((cu: any) => (
                <option key={cu.id} value={cu.id}>{cu.name}</option>
              ))}
            </select>
          )}
        </div>

        {/* Dish Categories Strip */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-line">
          <button
            onClick={() => setSelectedCatId("all")}
            className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${
              selectedCatId === "all" ? "bg-brand-600 text-white" : "bg-control text-ink-muted hover:text-ink"
            }`}
          >
            All Categories ({allItems.length})
          </button>
          {allCategories.map((c: any) => (
            <button
              key={c.id}
              onClick={() => setSelectedCatId(c.id)}
              className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${
                selectedCatId === c.id ? "bg-brand-600 text-white" : "bg-control text-ink-muted hover:text-ink"
              }`}
            >
              {c.name} ({c.items.length})
            </button>
          ))}
        </div>

        {/* Dishes Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {displayedItems.map((item: any) => (
            <div
              key={item.id}
              className="rounded-2xl bg-panel border border-line overflow-hidden flex flex-col justify-between hover:border-brand-500/50 transition shadow-sm group"
            >
              <div>
                <div className="relative h-40 w-full bg-well overflow-hidden">
                  <DishThumbnail
                    imageUrl={item.image_url}
                    name={item.name}
                    className="w-full h-full rounded-none border-0 group-hover:scale-[1.02] transition-transform duration-300"
                  />
                  <div className="absolute top-2.5 left-2.5">
                    <DietaryBadge foodType={item.food_type} isVeg={item.is_veg} showLabel />
                  </div>
                </div>
                <div className="p-4 pb-0">
                  <h3 className="text-sm font-bold text-ink">{item.name}</h3>
                  <p className="text-[11px] font-medium text-accent-brand mt-0.5">
                    {item.cuisine_name || "Indian Special"} · {item._catName}
                  </p>
                  {item.description && (
                    <p className="text-xs text-ink-muted line-clamp-2 mt-1.5 leading-relaxed">
                      {item.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="p-4 pt-3 mt-3 border-t border-line flex items-center justify-between">
                <div>
                  <span className="text-sm font-black text-ink">₹{item.base_price.toFixed(2)}</span>
                  <span className="text-[10px] text-ink-subtle ml-1.5">+{item.tax_rate ?? 5}% GST</span>
                </div>
                <button
                  onClick={() => addToCart(item)}
                  className="px-3 py-1.5 rounded-lg bg-tint-brand border border-tint-brand-border text-accent-brand hover:bg-brand-600 hover:text-white font-bold text-xs transition flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" /> Add
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Floating Sticky Cart Footer on Mobile */}
      {cart.length > 0 && !showCheckout && (
        <div className="fixed bottom-0 inset-x-0 p-4 bg-panel-glass backdrop-blur border-t border-line flex items-center justify-between z-40">
          <div className="text-xs">
            <span className="font-bold text-ink">{cart.reduce((a, b) => a + b.quantity, 0)} Items</span>
            <span className="text-ink-muted ml-2">Total: <strong className="text-accent-brand">₹{cartTotal.toFixed(2)}</strong></span>
          </div>
          <button
            onClick={() => setShowCheckout(true)}
            className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-extrabold text-xs rounded-xl shadow-lg transition flex items-center gap-2"
          >
            <span>Proceed to Checkout</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Checkout Drawer / Modal */}
      {showCheckout && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handlePlaceOrder} className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Review & Complete Order</h3>
                <p className="text-xs text-ink-muted">Directly routed to restaurant kitchen</p>
              </div>
              <button type="button" onClick={() => setShowCheckout(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {cart.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-lg bg-well border border-line text-xs">
                  <span className="font-bold text-ink">{item.quantity}x {item.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-black text-ink-2">₹{item.total.toFixed(2)}</span>
                    <button type="button" onClick={() => updateQuantity(item.id, -1)} className="text-ink-muted hover:text-accent-rose">
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <button type="button" onClick={() => updateQuantity(item.id, 1)} className="text-ink-muted hover:text-accent-emerald">
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2 p-1 bg-well rounded-lg border border-line text-xs font-bold">
              <button
                type="button"
                onClick={() => setOrderType("Takeaway")}
                className={`py-1.5 rounded-md ${orderType === "Takeaway" ? "bg-brand-600 text-white" : "text-ink-muted"}`}
              >
                Takeaway / Pickup
              </button>
              <button
                type="button"
                onClick={() => setOrderType("Delivery")}
                className={`py-1.5 rounded-md ${orderType === "Delivery" ? "bg-brand-600 text-white" : "text-ink-muted"}`}
              >
                Home Delivery
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Your Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Maya Patel"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Mobile Phone for Tracking</label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Special Cooking Requests</label>
              <input
                type="text"
                placeholder="Less spicy, no cutlery, extra napkins..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div className="pt-2 border-t border-line flex justify-between font-bold text-sm">
              <span>Total Payable</span>
              <span className="text-accent-brand">₹{cartTotal.toFixed(2)}</span>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {submitting ? "Transmitting to Kitchen..." : "Place Order Now"}
            </button>
          </form>
        </div>
      )}

      {/* Order Success Confirmation Modal */}
      {placedOrder && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 text-center space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-tint-emerald text-accent-emerald border border-tint-emerald-border flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-black text-ink">Order Placed Successfully!</h3>
              <p className="text-xs text-ink-muted mt-1">Sent straight to the restaurant kitchen display</p>
            </div>
            <div className="p-3 bg-well rounded-xl border border-line text-xs">
              <span className="text-ink-subtle text-[10px] uppercase font-bold block">Order Reference #</span>
              <span className="font-mono text-base font-bold text-accent-brand">{placedOrder.order_number}</span>
            </div>
            <button
              onClick={() => setPlacedOrder(null)}
              className="w-full py-2.5 rounded-xl text-xs font-bold text-ink-2 bg-control hover:bg-control-hover transition"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
