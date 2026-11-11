"use client";

import { useEffect, useState } from "react";
import {
  Plus, Users, QrCode, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function TableManagementPage() {
  const [areas, setAreas] = useState<any[]>([]);
  const [selectedAreaId, setSelectedAreaId] = useState<string>("all");
  const [tables, setTables] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [activeTable, setActiveTable] = useState<any | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTableNum, setNewTableNum] = useState("");
  const [newTableName, setNewTableName] = useState("");
  const [newCapacity, setNewCapacity] = useState(4);
  const [newAreaId, setNewAreaId] = useState("");

  useEffect(() => {
    loadTables();
  }, []);

  const loadTables = async () => {
    setLoading(true);
    try {
      const [areasData, tablesData] = await Promise.all([
        apiRequest("/tables/areas"),
        apiRequest("/tables")
      ]);
      setAreas(areasData);
      setTables(tablesData);
      if (areasData.length > 0 && !newAreaId) {
        setNewAreaId(areasData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (tableId: string, newStatus: string) => {
    setUpdatingStatus(true);
    try {
      await apiRequest(`/tables/${tableId}`, {
        method: "PUT",
        body: JSON.stringify({ status: newStatus })
      });
      await loadTables();
      setActiveTable(null);
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleRelease = async (tableId: string) => {
    try {
      await apiRequest(`/tables/${tableId}/release`, { method: "POST" });
      await loadTables();
      setActiveTable(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCreateTable = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/tables", {
        method: "POST",
        body: JSON.stringify({
          area_id: newAreaId,
          table_number: newTableNum,
          name: newTableName || null,
          capacity: newCapacity
        })
      });
      setShowCreateModal(false);
      setNewTableNum("");
      setNewTableName("");
      await loadTables();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const filteredTables = selectedAreaId === "all"
    ? tables
    : tables.filter(t => t.area_id === selectedAreaId);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Dining Tables & Visual Floor Plan</h1>
          <p className="text-xs text-ink-muted mt-1">Manage dining sections, table seating occupancy, and contactless QR ordering tokens.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Table
          </button>
        </div>
      </div>

      {/* Area Tabs */}
      <div className="flex items-center justify-between border-b border-line pb-3">
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setSelectedAreaId("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              selectedAreaId === "all" ? "bg-control text-ink border border-line-strong" : "text-ink-muted hover:text-ink"
            }`}
          >
            All Dining Rooms ({tables.length})
          </button>
          {areas.map((a) => (
            <button
              key={a.id}
              onClick={() => setSelectedAreaId(a.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                selectedAreaId === a.id ? "bg-control text-ink border border-line-strong" : "text-ink-muted hover:text-ink"
              }`}
            >
              {a.name} ({tables.filter(t => t.area_id === a.id).length})
            </button>
          ))}
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-3 text-[11px] font-semibold text-ink-muted">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Available</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Occupied</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Reserved</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Cleaning</span>
        </div>
      </div>

      {/* Interactive Table Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {filteredTables.map((table) => {
          const isOccupied = table.status === "Occupied";
          const isReserved = table.status === "Reserved";
          const isCleaning = table.status === "Cleaning";

          return (
            <div
              key={table.id}
              onClick={() => setActiveTable(table)}
              className={`p-4 rounded-2xl border text-left cursor-pointer transition select-none flex flex-col justify-between hover:scale-[1.02] shadow-sm ${
                isOccupied ? "bg-tint-amber border-tint-amber-border text-accent-amber" :
                isReserved ? "bg-tint-blue border-tint-blue-border text-accent-blue" :
                isCleaning ? "bg-tint-purple border-tint-purple-border text-accent-purple" :
                "bg-panel border-line text-ink hover:border-tint-emerald-border"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base font-black tracking-tight">{table.table_number}</span>
                  <span className={`w-2.5 h-2.5 rounded-full ${
                    isOccupied ? "bg-amber-500 animate-pulse" :
                    isReserved ? "bg-blue-500" :
                    isCleaning ? "bg-purple-500" :
                    "bg-emerald-500"
                  }`} />
                </div>
                <div className="text-xs font-semibold text-ink-3 truncate">
                  {table.name || "Dining Table"}
                </div>
                <div className="text-[11px] text-ink-muted mt-1 flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" />
                  <span>{table.capacity} Guests</span>
                </div>
              </div>

              <div className="mt-4 pt-2.5 border-t border-line flex items-center justify-between text-[11px]">
                <span className="uppercase font-bold tracking-wider">{table.status}</span>
                <QrCode className="w-4 h-4 text-ink-muted hover:text-ink" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Table Detail & Actions Modal */}
      {activeTable && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-lg font-black text-ink">{activeTable.table_number}</h3>
                <p className="text-xs text-ink-muted">{activeTable.name || `${activeTable.capacity} Seats Dining Table`}</p>
              </div>
              <button onClick={() => setActiveTable(null)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-ink-3">Set Table State</label>
              <div className="grid grid-cols-2 gap-2">
                {["Available", "Occupied", "Reserved", "Cleaning"].map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => handleStatusUpdate(activeTable.id, st)}
                    className={`py-2 px-3 rounded-xl border text-xs font-bold transition ${
                      activeTable.status === st
                        ? "bg-brand-600 text-white border-brand-500"
                        : "bg-well border-line text-ink-3 hover:bg-control"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-well border border-line text-xs space-y-1.5">
              <div className="font-bold text-ink-3 flex items-center gap-1.5">
                <QrCode className="w-4 h-4 text-accent-brand" />
                <span>Contactless Table QR Order Token:</span>
              </div>
              <div className="font-mono text-[11px] text-accent-amber bg-panel p-2 rounded border border-line break-all select-all">
                {activeTable.qr_code_token || "QR-TOKEN-PENDING"}
              </div>
              <div className="text-[10px] text-ink-subtle">
                Customers scanning this table QR code order directly without calling a waiter.
              </div>
            </div>

            {activeTable.status !== "Available" && (
              <button
                type="button"
                onClick={() => handleRelease(activeTable.id)}
                className="w-full py-2.5 rounded-xl text-xs font-bold text-accent-emerald bg-tint-emerald border border-tint-emerald-border hover:opacity-80 transition"
              >
                Release Table (Set to Available)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Create Table Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateTable} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Add Dining Table</h3>
              <button type="button" onClick={() => setShowCreateModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Dining Area</label>
              <select
                value={newAreaId}
                onChange={(e) => setNewAreaId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                {areas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Table Number</label>
              <input
                type="text"
                required
                placeholder="e.g. T-09"
                value={newTableNum}
                onChange={(e) => setNewTableNum(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Name / Label (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Window Booth"
                value={newTableName}
                onChange={(e) => setNewTableName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Seating Capacity</label>
              <input
                type="number"
                min={1}
                max={20}
                value={newCapacity}
                onChange={(e) => setNewCapacity(parseInt(e.target.value) || 4)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
            >
              Save Table
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
