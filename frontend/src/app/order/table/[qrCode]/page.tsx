"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  QrCode, CheckCircle2, Plus, Minus, ArrowRight
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function QRTableOrderPage() {
  const params = useParams();
  const qrCode = params?.qrCode as string;

  const [tableInfo, setTableInfo] = useState<any | null>(null);
  const [menuData, setMenuData] = useState<any | null>(null);
  const [cart, setCart] = useState<any[]>([]);
  const [guestName] = useState("");
  const [notes] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [placedOrder, setPlacedOrder] = useState<any | null>(null);

  useEffect(() => {
    if (qrCode) {
      loadTableAndMenu();
    }
  }, [qrCode]);

  const loadTableAndMenu = async () => {
    setLoading(true);
    try {
      const tbl = await apiRequest(`/public/table/${qrCode}`);
      setTableInfo(tbl);
      const menuQuery = tbl.assigned_menu_id ? `?menu_id=${tbl.assigned_menu_id}` : "";
      const menu = await apiRequest(`/public/${tbl.tenant_slug}/menu${menuQuery}`);
      setMenuData(menu);
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

  const handleSendOrderToKitchen = async () => {
    if (cart.length === 0 || !tableInfo) return;
    setSubmitting(true);
    try {
      const res = await apiRequest(`/public/${tableInfo.tenant_slug}/orders`, {
        method: "POST",
        body: JSON.stringify({
          order_type: "QR",
          table_id: tableInfo.table_id,
          customer_name: guestName || `Guest at Table ${tableInfo.table_number}`,
          notes: notes || "Order placed via Table QR code",
          items: cart.map(i => ({
            menu_item_id: i.id,
            quantity: i.quantity,
            modifiers: []
          }))
        })
      });
      setPlacedOrder(res);
      setCart([]);
    } catch (err: any) {
      alert(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const cartTotal = cart.reduce((a, b) => a + b.total, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas text-ink flex items-center justify-center text-sm font-semibold">
        Connecting to table ordering terminal...
      </div>
    );
  }

  if (!tableInfo) {
    return (
      <div className="min-h-screen bg-canvas text-ink flex items-center justify-center text-sm">
        Invalid QR code. Please scan the QR code printed on your dining table.
      </div>
    );
  }

  const allItems = menuData?.categories?.flatMap((c: any) => c.items) || [];

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col max-w-md mx-auto border-x border-line shadow-2xl">
      {/* Table Greeting Header */}
      <header className="p-4 bg-panel border-b border-line flex items-center justify-between sticky top-0 z-30">
        <div>
          <span className="text-[10px] uppercase font-black text-accent-brand tracking-wider">Contactless Ordering</span>
          <h1 className="text-lg font-black text-ink">{tableInfo.tenant_name}</h1>
          <div className="text-xs text-accent-emerald font-bold flex items-center gap-1 mt-0.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Table {tableInfo.table_number} Connected</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <div className="w-10 h-10 rounded-xl bg-well border border-line flex items-center justify-center text-ink-3">
            <QrCode className="w-5 h-5" />
          </div>
        </div>
      </header>

      {/* Food Items List */}
      <main className="p-4 space-y-3 flex-1 overflow-y-auto pb-24">
        <div className="text-xs font-bold text-ink-muted">Available Menu Dishes</div>
        {allItems.map((item: any) => (
          <div key={item.id} className="p-3.5 rounded-xl bg-panel border border-line flex items-center justify-between gap-3 shadow-sm">
            <div className="flex-1">
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${item.is_veg ? "bg-emerald-500" : "bg-rose-500"}`} />
                <span className="font-bold text-xs text-ink">{item.name}</span>
              </div>
              <div className="text-xs font-black text-accent-brand mt-1">₹{item.base_price.toFixed(2)}</div>
            </div>

            <button
              onClick={() => addToCart(item)}
              className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold transition flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        ))}
      </main>

      {/* Floating Cart Drawer on Table Screen */}
      {cart.length > 0 && (
        <div className="fixed bottom-0 inset-x-0 max-w-md mx-auto p-4 bg-panel-glass backdrop-blur border-t border-line z-40 space-y-3">
          <div className="space-y-1.5 max-h-32 overflow-y-auto">
            {cart.map((item) => (
              <div key={item.id} className="flex justify-between items-center text-xs">
                <span className="text-ink-2">{item.quantity}x {item.name}</span>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-ink">₹{item.total.toFixed(2)}</span>
                  <button onClick={() => updateQuantity(item.id, -1)} className="p-0.5 text-ink-muted hover:text-ink">
                    <Minus className="w-3 h-3" />
                  </button>
                  <button onClick={() => updateQuantity(item.id, 1)} className="p-0.5 text-ink-muted hover:text-ink">
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-baseline pt-2 border-t border-line">
            <span className="text-xs text-ink-muted">Total Bill</span>
            <span className="text-base font-black text-accent-brand">₹{cartTotal.toFixed(2)}</span>
          </div>

          <button
            onClick={handleSendOrderToKitchen}
            disabled={submitting}
            className="w-full py-3 rounded-xl text-xs font-extrabold text-white bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-600/25 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {submitting ? "Sending to Kitchen..." : `Send to Kitchen Display (Table ${tableInfo.table_number})`}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Placed Order Success Modal */}
      {placedOrder && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-xs w-full p-6 text-center space-y-3 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-tint-emerald text-accent-emerald border border-tint-emerald-border flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-black text-ink">Order Sent to Chefs!</h3>
            <p className="text-xs text-ink-muted">Your dishes are now showing on the kitchen display board for preparation.</p>
            <div className="p-2.5 rounded-lg bg-well border border-line font-mono text-xs text-accent-brand font-bold">
              {placedOrder.order_number}
            </div>
            <button
              onClick={() => setPlacedOrder(null)}
              className="w-full py-2 rounded-lg bg-control hover:bg-control-hover text-xs font-bold text-ink-2 transition"
            >
              Order More Items
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
