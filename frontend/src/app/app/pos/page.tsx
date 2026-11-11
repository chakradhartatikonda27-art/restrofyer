"use client";

import { useEffect, useState } from "react";
import {
  Search, ShoppingCart, Trash2, Plus, Minus, CreditCard,
  Banknote, QrCode, Split, CheckCircle2, X, Tag, User, LayoutGrid,
  Printer
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { FOOD_TYPE_OPTIONS } from "@/components/menu/MenuTypes";
import { DietaryBadge, DishThumbnail, resolveFoodType } from "@/components/menu/VegBadge";

export default function POSTerminalPage() {
  const [cuisines, setCuisines] = useState<any[]>([]);
  const [selectedCuisineId, setSelectedCuisineId] = useState<string>("all");
  const [selectedFoodType, setSelectedFoodType] = useState<string>("all");
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCatId, setSelectedCatId] = useState<string>("all");
  const [items, setItems] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  // Cart State
  const [cart, setCart] = useState<any[]>([]);
  const [orderType, setOrderType] = useState<string>("DineIn");
  const [selectedTableId, setSelectedTableId] = useState<string>("");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [discountAmount, setDiscountAmount] = useState<number>(0);
  const [orderNotes, setOrderNotes] = useState<string>("");

  // Variant/Modifier Modal
  const [activeItemForCustomization, setActiveItemForCustomization] = useState<any | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<any | null>(null);
  const [selectedModifiers, setSelectedModifiers] = useState<any[]>([]);

  // Payment Checkout Modal
  const [showPaymentModal, setShowPaymentModal] = useState<boolean>(false);
  const [paymentMethod, setPaymentMethod] = useState<string>("Cash");
  const [paymentReference, setPaymentReference] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Success Receipt View
  const [completedInvoice, setCompletedInvoice] = useState<any | null>(null);

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    try {
      const [cats, cuisinesRes, menuItems, tbls, custs] = await Promise.all([
        apiRequest("/menus/categories"),
        apiRequest("/menus/cuisines"),
        apiRequest("/menus/items?available_only=true"),
        apiRequest("/tables"),
        apiRequest("/crm")
      ]);
      setCategories(cats);
      setCuisines(cuisinesRes);
      setItems(menuItems);
      setTables(tbls);
      setCustomers(custs);
    } catch (err) {
      console.error("Error loading POS catalog:", err);
    }
  };

  const handleItemClick = (item: any) => {
    if ((item.variants && item.variants.length > 0) || (item.modifier_groups && item.modifier_groups.length > 0)) {
      setActiveItemForCustomization(item);
      setSelectedVariant(item.variants && item.variants.length > 0 ? item.variants[0] : null);
      setSelectedModifiers([]);
    } else {
      addToCartDirect(item, null, []);
    }
  };

  const addToCartDirect = (item: any, variant: any, modifiers: any[]) => {
    const unitPrice = variant
      ? variant.price
      : (typeof item.effective_price === "number" ? item.effective_price : item.base_price);
    const modifiersTotal = modifiers.reduce((acc, m) => acc + m.price, 0);
    const finalPrice = unitPrice + modifiersTotal;

    const cartKey = `${item.id}-${variant?.id || 'base'}-${modifiers.map(m => m.id).sort().join('-')}`;

    setCart(prev => {
      const existing = prev.find(i => i.cartKey === cartKey);
      if (existing) {
        return prev.map(i => i.cartKey === cartKey ? { ...i, quantity: i.quantity + 1, subtotal: (i.quantity + 1) * finalPrice } : i);
      } else {
        return [...prev, {
          cartKey,
          menu_item_id: item.id,
          name: item.name,
          variant_id: variant?.id || null,
          variant_name: variant?.name || null,
          modifiers: modifiers.map(m => ({ name: m.name, price: m.price })),
          unit_price: finalPrice,
          tax_rate: typeof item.tax_rate === "number" ? item.tax_rate : 5.0,
          quantity: 1,
          subtotal: finalPrice
        }];
      }
    });

    setActiveItemForCustomization(null);
  };

  const updateQuantity = (cartKey: string, delta: number) => {
    setCart(prev => prev.map(item => {
      if (item.cartKey === cartKey) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty, subtotal: newQty * item.unit_price } : null;
      }
      return item;
    }).filter(Boolean));
  };

  const removeItem = (cartKey: string) => {
    setCart(prev => prev.filter(i => i.cartKey !== cartKey));
  };

  const clearCart = () => {
    setCart([]);
    setDiscountAmount(0);
    setSelectedTableId("");
    setSelectedCustomerId("");
    setOrderNotes("");
  };

  // Calculations (respecting per-item GST %)
  const subtotal = cart.reduce((acc, i) => acc + i.subtotal, 0);
  const taxableSubtotal = Math.max(0, subtotal - discountAmount);
  const weightedTax =
    subtotal > 0
      ? cart.reduce((acc, i) => {
          const itemRate = typeof i.tax_rate === "number" ? i.tax_rate : 5.0;
          return acc + (i.subtotal / subtotal) * taxableSubtotal * (itemRate / 100.0);
        }, 0)
      : 0;
  const taxAmount = Math.round(weightedTax * 100) / 100;
  const serviceCharge = orderType === "DineIn" ? (taxableSubtotal * 2.5) / 100.0 : 0.0;
  const grandTotal = taxableSubtotal + taxAmount + serviceCharge;

  const handleCheckoutAndPay = async () => {
    if (cart.length === 0) return;
    setIsProcessing(true);
    try {
      const orderPayload = {
        order_type: orderType,
        table_id: selectedTableId || null,
        customer_id: selectedCustomerId || null,
        customer_name: customers.find(c => c.id === selectedCustomerId)?.name || null,
        discount_amount: discountAmount,
        discount_reason: discountAmount > 0 ? "Staff POS Discount" : null,
        notes: orderNotes || null,
        items: cart.map(i => ({
          menu_item_id: i.menu_item_id,
          quantity: i.quantity,
          variant_id: i.variant_id,
          modifiers: i.modifiers,
          notes: i.variant_name || null
        }))
      };

      const createdOrder = await apiRequest("/orders", {
        method: "POST",
        body: JSON.stringify(orderPayload)
      });

      const paymentPayload = {
        amount: Number(createdOrder.total_amount ?? grandTotal),
        payment_method: paymentMethod,
        payment_reference: paymentReference || `POS-${Date.now().toString().slice(-6)}`
      };

      const invoice = await apiRequest(`/invoices/orders/${createdOrder.id}/payments`, {
        method: "POST",
        body: JSON.stringify(paymentPayload)
      });

      setCompletedInvoice({
        ...invoice,
        order_number: createdOrder.order_number,
        items: createdOrder.items,
        table_number: createdOrder.table_number,
        customer_name: createdOrder.customer_name
      });

      setShowPaymentModal(false);
      clearCart();
      loadCatalog();
    } catch (err: any) {
      alert(`Checkout failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredItems = items.filter(i => {
    const matchesCuisine = selectedCuisineId === "all" || i.cuisine_id === selectedCuisineId;
    const itemFtype = resolveFoodType(i.food_type, i.is_veg);
    const matchesFoodType = selectedFoodType === "all" || itemFtype === selectedFoodType;
    const matchesCat =
      selectedCatId === "all" ||
      i.category_id === selectedCatId ||
      i.parent_category_id === selectedCatId;
    const matchesChannel =
      !Array.isArray(i.order_channels) ||
      i.order_channels.length === 0 ||
      i.order_channels.includes(orderType);
    const matchesSearch = i.name.toLowerCase().includes(search.toLowerCase());
    return matchesCuisine && matchesFoodType && matchesCat && matchesChannel && matchesSearch;
  });

  return (
    <div className="h-[calc(100vh-5rem)] flex flex-col lg:flex-row gap-4 max-w-[1600px] mx-auto overflow-hidden">
      {/* Left Menu & Catalog Column */}
      <div className="flex-1 flex flex-col bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        {/* Top 3D Filter Bar */}
        <div className="p-3.5 border-b border-line space-y-2.5 bg-well-soft">
          <div className="flex flex-wrap items-center justify-between gap-2.5">
            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Quick search dishes or SKUs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-panel border border-input-border rounded-xl text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <select
              value={selectedCuisineId}
              onChange={(e) => setSelectedCuisineId(e.target.value)}
              aria-label="Filter POS by Cuisine"
              className="px-3 py-1.5 bg-panel border border-input-border rounded-xl text-xs font-medium text-ink"
            >
              <option value="all">All Cuisines</option>
              {cuisines.map((cu) => (
                <option key={cu.id} value={cu.id}>{cu.name}</option>
              ))}
            </select>

            <div className="flex flex-wrap items-center gap-1">
              <button
                type="button"
                onClick={() => setSelectedFoodType("all")}
                className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
                  selectedFoodType === "all"
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-panel text-ink-3 border-line"
                }`}
              >
                All
              </button>
              {FOOD_TYPE_OPTIONS.map((ft) => {
                const active = selectedFoodType === ft.value;
                return (
                  <button
                    key={ft.value}
                    type="button"
                    onClick={() => setSelectedFoodType(active ? "all" : ft.value)}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
                      active
                        ? "bg-brand-600 text-white border-brand-600"
                        : "bg-panel text-ink-2 border-line"
                    }`}
                  >
                    <DietaryBadge foodType={ft.value} />
                    <span>{ft.shortLabel}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
            <button
              onClick={() => setSelectedCatId("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                selectedCatId === "all"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-control text-ink-muted hover:text-ink"
              }`}
            >
              All Categories
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCatId(c.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                  selectedCatId === c.id
                    ? "bg-brand-600 text-white shadow-sm"
                    : "bg-control text-ink-muted hover:text-ink"
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>

        {/* Menu Items Touch Grid */}
        <div className="flex-1 p-4 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3 content-start">
          {filteredItems.map((item) => {
            const effPrice =
              typeof item.effective_price === "number" ? item.effective_price : item.base_price;
            return (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                className="p-2.5 rounded-xl bg-well border border-line hover:border-brand-500/60 hover:bg-panel hover:shadow-sm cursor-pointer transition select-none flex flex-col justify-between group pos-touch-card"
              >
                <div>
                  <div className="relative h-24 w-full mb-2 rounded-lg overflow-hidden bg-panel">
                    <DishThumbnail
                      imageUrl={item.image_url}
                      name={item.name}
                      className="w-full h-full rounded-lg border-0 group-hover:scale-[1.03] transition-transform"
                    />
                    <div className="absolute top-1.5 right-1.5">
                      <DietaryBadge foodType={item.food_type} isVeg={item.is_veg} />
                    </div>
                  </div>
                  <div className="flex items-start justify-between gap-1.5 mb-0.5">
                    <span className="text-xs font-bold text-ink group-hover:text-accent-brand transition leading-snug line-clamp-1">
                      {item.name}
                    </span>
                  </div>
                  <div className="text-[10px] text-ink-subtle font-medium mb-1 line-clamp-1">
                    {item.cuisine_name || "House"}{item.category_name ? ` · ${item.category_name}` : ""}
                  </div>
                  {item.description && (
                    <p className="text-[11px] text-ink-muted line-clamp-1 leading-relaxed">
                      {item.description}
                    </p>
                  )}
                </div>

                <div className="mt-3 pt-2 border-t border-line flex items-center justify-between">
                  <span className="text-xs font-black text-ink">
                    ₹{effPrice.toFixed(2)}
                  </span>
                  <span className="text-[10px] font-semibold text-accent-brand bg-tint-brand px-2 py-0.5 rounded-md border border-tint-brand-border">
                    + Add
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Cart & Checkout Column */}
      <div className="w-full lg:w-96 flex flex-col bg-panel border border-line rounded-2xl overflow-hidden shrink-0 shadow-lg">
        {/* Cart Header & Order Type Toggle */}
        <div className="p-3.5 border-b border-line bg-well-soft space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="w-4 h-4 text-accent-brand" />
              <span className="text-xs font-extrabold text-ink uppercase tracking-wider">Current Bill</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-tint-brand text-accent-brand font-bold">
                {cart.reduce((a, b) => a + b.quantity, 0)} items
              </span>
            </div>
            {cart.length > 0 && (
              <button
                onClick={clearCart}
                className="text-[10px] font-bold text-ink-subtle hover:text-accent-rose transition"
              >
                Clear Cart
              </button>
            )}
          </div>

          {/* Order Types */}
          <div className="grid grid-cols-4 gap-1 p-1 rounded-lg bg-well border border-line">
            {["DineIn", "Takeaway", "Delivery", "QR"].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setOrderType(type)}
                className={`py-1 text-[11px] font-bold rounded-md transition ${
                  orderType === type ? "bg-brand-600 text-white shadow" : "text-ink-muted hover:text-ink"
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Table Selector (If DineIn) */}
          {orderType === "DineIn" && (
            <div className="flex items-center gap-2">
              <LayoutGrid className="w-3.5 h-3.5 text-ink-subtle" />
              <select
                value={selectedTableId}
                onChange={(e) => setSelectedTableId(e.target.value)}
                className="flex-1 px-2.5 py-1 bg-panel border border-input-border rounded-lg text-xs text-ink focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">Select Dining Table...</option>
                {tables.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.table_number} — {t.name || `${t.capacity} seats`} ({t.status})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Customer Selector */}
          <div className="flex items-center gap-2">
            <User className="w-3.5 h-3.5 text-ink-subtle" />
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="flex-1 px-2.5 py-1 bg-panel border border-input-border rounded-lg text-xs text-ink focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">Walk-in Customer (Guest)</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.phone}) • {c.segment}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cart Items List */}
        <div className="flex-1 p-3 overflow-y-auto space-y-2 divide-y divide-line">
          {cart.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-ink-subtle">
              <ShoppingCart className="w-8 h-8 stroke-[1.5] mb-2 opacity-40" />
              <div className="text-xs font-semibold text-ink-muted">Cart is empty</div>
              <div className="text-[11px] text-ink-subtle mt-0.5">Select menu items from the left to start an order</div>
            </div>
          ) : (
            cart.map((item) => (
              <div key={item.cartKey} className="pt-2 first:pt-0 flex items-center justify-between gap-2 text-xs">
                <div className="flex-1 truncate">
                  <div className="font-bold text-ink truncate">{item.name}</div>
                  {item.variant_name && (
                    <div className="text-[10px] text-accent-brand font-medium">{item.variant_name}</div>
                  )}
                  {item.modifiers && item.modifiers.length > 0 && (
                    <div className="text-[10px] text-ink-muted">
                      +{item.modifiers.map((m: any) => m.name).join(", ")}
                    </div>
                  )}
                  <div className="text-[11px] text-ink-muted mt-0.5">₹{item.unit_price.toFixed(2)} ea</div>
                </div>

                {/* Qty +/- & Total */}
                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center rounded-lg bg-well border border-line p-0.5">
                    <button
                      onClick={() => updateQuantity(item.cartKey, -1)}
                      className="p-1 text-ink-muted hover:text-ink rounded"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="px-2 font-bold text-xs text-ink">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.cartKey, 1)}
                      className="p-1 text-ink-muted hover:text-ink rounded"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                  <div className="w-16 text-right font-black text-ink">
                    ₹{item.subtotal.toFixed(2)}
                  </div>
                  <button
                    onClick={() => removeItem(item.cartKey)}
                    className="p-1 text-ink-subtle hover:text-accent-rose transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Financial Summary & Checkout Action */}
        <div className="p-4 border-t border-line bg-well space-y-2 text-xs">
          <div className="flex items-center justify-between text-ink-muted">
            <span className="flex items-center gap-1.5 text-[11px]">
              <Tag className="w-3 h-3" /> Discount
            </span>
            <div className="flex items-center gap-1">
              <span className="text-ink-subtle">₹</span>
              <input
                type="number"
                min={0}
                value={discountAmount}
                onChange={(e) => setDiscountAmount(parseFloat(e.target.value) || 0)}
                className="w-16 px-1.5 py-0.5 bg-panel border border-input-border rounded text-right text-xs text-accent-brand font-bold focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-between text-ink-muted text-[11px]">
            <span>Subtotal</span>
            <span>₹{subtotal.toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-ink-muted text-[11px]">
            <span>GST (Per-Item Rate)</span>
            <span>₹{taxAmount.toFixed(2)}</span>
          </div>

          {serviceCharge > 0 && (
            <div className="flex justify-between text-ink-muted text-[11px]">
              <span>Service Charge (2.5%)</span>
              <span>₹{serviceCharge.toFixed(2)}</span>
            </div>
          )}

          <div className="pt-2 border-t border-line flex justify-between items-baseline">
            <span className="text-sm font-bold text-ink">Grand Total</span>
            <span className="text-xl font-black text-accent-brand">
              ₹{grandTotal.toFixed(2)}
            </span>
          </div>

          <button
            type="button"
            disabled={cart.length === 0}
            onClick={() => setShowPaymentModal(true)}
            className="w-full mt-2 py-3 px-4 rounded-xl text-sm font-extrabold text-white bg-gradient-to-r from-brand-600 to-amber-500 hover:from-brand-700 hover:to-amber-600 shadow-lg shadow-brand-500/25 transition disabled:opacity-40 flex items-center justify-center gap-2"
          >
            <CreditCard className="w-4 h-4" />
            <span>Pay & Send to Kitchen (₹{grandTotal.toFixed(2)})</span>
          </button>
        </div>
      </div>

      {/* Item Customization Modal (Variants & Modifiers) */}
      {activeItemForCustomization && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">{activeItemForCustomization.name}</h3>
                <p className="text-xs text-ink-muted">Select portion size and extra ingredients</p>
              </div>
              <button
                onClick={() => setActiveItemForCustomization(null)}
                className="text-ink-muted hover:text-ink"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {activeItemForCustomization.variants && activeItemForCustomization.variants.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-ink-3">Choose Size / Variant</label>
                <div className="grid grid-cols-2 gap-2">
                  {activeItemForCustomization.variants.map((v: any) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => setSelectedVariant(v)}
                      className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-between transition ${
                        selectedVariant?.id === v.id
                          ? "bg-tint-brand border-brand-500 text-accent-brand shadow"
                          : "bg-well border-line text-ink-3 hover:bg-control"
                      }`}
                    >
                      <span>{v.name}</span>
                      <span className="font-bold">₹{v.price.toFixed(2)}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeItemForCustomization.modifier_groups?.map((group: any) => (
              <div key={group.id} className="space-y-2">
                <label className="text-xs font-bold text-ink-3">{group.name}</label>
                <div className="space-y-1.5">
                  {group.modifiers.map((mod: any) => {
                    const isSelected = selectedModifiers.some(m => m.id === mod.id);
                    return (
                      <button
                        key={mod.id}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            setSelectedModifiers(selectedModifiers.filter(m => m.id !== mod.id));
                          } else {
                            setSelectedModifiers([...selectedModifiers, mod]);
                          }
                        }}
                        className={`w-full p-2.5 rounded-xl border text-xs flex items-center justify-between transition ${
                          isSelected
                            ? "bg-tint-brand border-brand-500 text-accent-brand"
                            : "bg-well border-line text-ink-3 hover:bg-control"
                        }`}
                      >
                        <span className="font-medium">{mod.name}</span>
                        <span className="font-bold">+₹{mod.price.toFixed(2)}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}

            <button
              type="button"
              onClick={() => addToCartDirect(activeItemForCustomization, selectedVariant, selectedModifiers)}
              className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition mt-4"
            >
              Add to Bill
            </button>
          </div>
        </div>
      )}

      {/* Payment Tender Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Complete Transaction & Tender</h3>
                <p className="text-xs text-ink-muted">Total Due: ₹{grandTotal.toFixed(2)}</p>
              </div>
              <button
                onClick={() => setShowPaymentModal(false)}
                className="text-ink-muted hover:text-ink"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "Cash", name: "Cash Tender", icon: Banknote },
                { id: "Card", name: "Credit/Debit Card", icon: CreditCard },
                { id: "UPI", name: "UPI / QR Code", icon: QrCode },
                { id: "Split", name: "Split Bill", icon: Split }
              ].map((m) => {
                const Icon = m.icon;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setPaymentMethod(m.id)}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition ${
                      paymentMethod === m.id
                        ? "bg-brand-600 text-white shadow-lg shadow-brand-500/25 border-brand-500"
                        : "bg-well border-line text-ink-3 hover:bg-control"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{m.name}</span>
                  </button>
                );
              })}
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-muted mb-1">
                Payment Reference / Transaction ID (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. CARD_AUTH_4920 or UPI_RR_9812"
                value={paymentReference}
                onChange={(e) => setPaymentReference(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink focus:outline-none"
              />
            </div>

            <button
              type="button"
              disabled={isProcessing}
              onClick={handleCheckoutAndPay}
              className="w-full py-3 rounded-xl text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-600/25 transition disabled:opacity-50"
            >
              {isProcessing ? "Processing & Printing KOT..." : `Confirm Payment (₹${grandTotal.toFixed(2)})`}
            </button>
          </div>
        </div>
      )}

      {/* Invoice Receipt Modal */}
      {completedInvoice && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl text-center">
            <div className="w-12 h-12 rounded-full bg-tint-emerald text-accent-emerald border border-tint-emerald-border flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-base font-bold text-ink">Payment Received!</h3>
              <p className="text-xs text-ink-muted">Order successfully routed to Kitchen Display (KDS)</p>
            </div>

            <div className="p-4 rounded-xl bg-well border border-line text-left text-xs space-y-2">
              <div className="flex justify-between font-mono text-[11px] text-ink-muted pb-2 border-b border-line">
                <span>{completedInvoice.invoice_number}</span>
                <span>{completedInvoice.order_number}</span>
              </div>
              <div className="text-ink-3">
                {completedInvoice.table_number ? `Table: ${completedInvoice.table_number}` : 'Takeaway / Walk-in'}
              </div>
              <div className="py-2 border-y border-line space-y-1">
                {completedInvoice.items?.map((it: any, idx: number) => (
                  <div key={idx} className="flex justify-between text-ink-2">
                    <span>{it.quantity}x {it.item_name}</span>
                    <span>₹{it.subtotal.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between font-bold text-sm text-ink pt-1">
                <span>Total Paid</span>
                <span className="text-accent-brand">₹{completedInvoice.total_amount.toFixed(2)}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setCompletedInvoice(null)}
                className="flex-1 py-2 rounded-xl text-xs font-bold text-ink-3 bg-control hover:bg-control-hover transition"
              >
                Close & Next Order
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition flex items-center gap-1.5"
              >
                <Printer className="w-4 h-4" /> Print
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
