"use client";

import { useEffect, useState } from "react";
import {
  Clock, CheckCircle2, ChefHat
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function KitchenDisplayPage() {
  const [kots, setKots] = useState<any[]>([]);
  const [stations, setStations] = useState<any[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    loadKds();
    const interval = setInterval(loadKds, 5000);
    return () => clearInterval(interval);
  }, [selectedStationId]);

  const loadKds = async () => {
    try {
      const [kotData, stationData] = await Promise.all([
        apiRequest(`/kitchens/kots${selectedStationId !== 'all' ? `?station_id=${selectedStationId}` : ''}`),
        apiRequest("/kitchens/stations")
      ]);
      setKots(kotData);
      setStations(stationData);
    } catch (err) {
      console.error("Error loading KDS:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (kotId: string, nextStatus: string) => {
    setUpdatingId(kotId);
    try {
      await apiRequest(`/kitchens/kots/${kotId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      await loadKds();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const getElapsedMinutes = (createdAt: string) => {
    const diff = Math.floor((new Date().getTime() - new Date(createdAt).getTime()) / 60000);
    return Math.max(0, diff);
  };

  return (
    <div className="space-y-6 max-w-[1700px] mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h1 className="text-2xl font-black text-ink tracking-tight">Kitchen Display System (KDS)</h1>
          </div>
          <p className="text-xs text-ink-muted mt-1">Real-time order routing, line cooking timers, and ticket dispatch.</p>
        </div>

        {/* Station Filter Tabs */}
        <div className="flex items-center gap-2 bg-panel border border-line p-1 rounded-xl shadow-sm overflow-x-auto">
          <button
            onClick={() => setSelectedStationId("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition ${
              selectedStationId === "all"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            All Stations ({kots.length})
          </button>
          {stations.map((s) => {
            const count = kots.filter(k => k.kitchen_station_id === s.id).length;
            return (
              <button
                key={s.id}
                onClick={() => setSelectedStationId(s.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition ${
                  selectedStationId === s.id
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-ink-muted hover:text-ink"
                }`}
              >
                {s.name} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* KOT Cards Board Grid */}
      {kots.length === 0 ? (
        <div className="p-16 text-center rounded-2xl bg-panel border border-line shadow-sm">
          <ChefHat className="w-12 h-12 text-ink-subtle mx-auto mb-3 stroke-[1.5]" />
          <h3 className="text-base font-bold text-ink">All Kitchen Orders Cleared!</h3>
          <p className="text-xs text-ink-subtle mt-1">Waiting for new orders from the POS terminal or online store.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {kots.map((kot) => {
            const elapsed = getElapsedMinutes(kot.created_at);
            const isUrgent = elapsed >= 15;
            const isPreparing = kot.status === "Preparing";
            const isReady = kot.status === "Ready";

            return (
              <div
                key={kot.id}
                className={`rounded-2xl border flex flex-col justify-between overflow-hidden shadow-md transition ${
                  isReady ? "bg-panel border-tint-emerald-border" :
                  isUrgent ? "bg-panel border-tint-rose-border" :
                  isPreparing ? "bg-panel border-tint-amber-border" :
                  "bg-panel border-line"
                }`}
              >
                {/* KOT Header */}
                <div className={`p-3.5 border-b flex items-center justify-between ${
                  isReady ? "bg-tint-emerald border-tint-emerald-border" :
                  isUrgent ? "bg-tint-rose border-tint-rose-border" :
                  "bg-well border-line"
                }`}>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-black text-ink">{kot.kot_number}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-control text-ink-3 font-bold border border-line-strong">
                        {kot.station_name}
                      </span>
                    </div>
                    <div className="text-[11px] text-ink-muted mt-0.5">
                      Waiter: {kot.waiter_name || "Self-Order"}
                    </div>
                  </div>

                  {/* Elapsed Timer */}
                  <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold ${
                    isUrgent ? "bg-rose-600 text-white animate-pulse" :
                    isPreparing ? "bg-tint-amber text-accent-amber" :
                    "bg-control text-ink-3"
                  }`}>
                    <Clock className="w-3.5 h-3.5" />
                    <span>{elapsed}m</span>
                  </div>
                </div>

                {/* Items List */}
                <div className="p-4 flex-1 space-y-3">
                  {kot.items.map((item: any) => (
                    <div key={item.id} className="flex items-start justify-between gap-2 border-b border-line pb-2.5 last:border-none last:pb-0">
                      <div>
                        <div className="text-sm font-extrabold text-ink flex items-center gap-1.5">
                          <span className="text-accent-brand">{item.quantity}x</span>
                          <span>{item.item_name}</span>
                        </div>
                        {item.variant_name && (
                          <div className="text-xs text-accent-amber font-medium ml-5">
                            Size: {item.variant_name}
                          </div>
                        )}
                        {item.modifiers_summary && (
                          <div className="text-xs text-ink-muted ml-5">
                            +{item.modifiers_summary}
                          </div>
                        )}
                        {item.notes && (
                          <div className="text-xs text-accent-amber bg-tint-amber px-2 py-0.5 rounded mt-1 ml-5 font-semibold">
                            Note: {item.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {kot.notes && (
                    <div className="p-2 rounded-lg bg-well border border-line text-xs text-ink-muted">
                      <span className="font-bold text-accent-amber">Ticket Instructions:</span> {kot.notes}
                    </div>
                  )}
                </div>

                {/* Status Action Buttons */}
                <div className="p-3 border-t border-line bg-well-soft flex items-center gap-2">
                  {kot.status === "New" && (
                    <button
                      type="button"
                      disabled={updatingId === kot.id}
                      onClick={() => handleStatusChange(kot.id, "Preparing")}
                      className="w-full py-2.5 px-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-xs transition shadow-md shadow-amber-500/20"
                    >
                      Start Preparing
                    </button>
                  )}

                  {kot.status === "Preparing" && (
                    <button
                      type="button"
                      disabled={updatingId === kot.id}
                      onClick={() => handleStatusChange(kot.id, "Ready")}
                      className="w-full py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs transition shadow-md shadow-emerald-500/20 flex items-center justify-center gap-1.5"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Mark Ready (Notify Waiter)</span>
                    </button>
                  )}

                  {kot.status === "Ready" && (
                    <button
                      type="button"
                      disabled={updatingId === kot.id}
                      onClick={() => handleStatusChange(kot.id, "Served")}
                      className="w-full py-2.5 px-3 rounded-xl bg-control hover:bg-control-hover text-ink-2 font-bold text-xs transition border border-line-strong"
                    >
                      Mark Dispatched / Served
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
