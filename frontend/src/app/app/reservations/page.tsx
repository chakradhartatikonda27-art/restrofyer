"use client";

import { useEffect, useState } from "react";
import {
  Plus, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [custName, setCustName] = useState("");
  const [custPhone, setCustPhone] = useState("");
  const [partySize, setPartySize] = useState(2);
  const [tableId, setTableId] = useState("");
  const [resTime, setResTime] = useState("");
  const [requests, setRequests] = useState("");

  useEffect(() => {
    loadReservations();
  }, []);

  const loadReservations = async () => {
    setLoading(true);
    try {
      const [resData, tblsData] = await Promise.all([
        apiRequest("/reservations"),
        apiRequest("/tables")
      ]);
      setReservations(resData);
      setTables(tblsData);
      if (tblsData.length > 0 && !tableId) {
        setTableId(tblsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReservation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/reservations", {
        method: "POST",
        body: JSON.stringify({
          customer_name: custName,
          customer_phone: custPhone,
          party_size: partySize,
          table_id: tableId || null,
          reservation_time: new Date(resTime).toISOString(),
          special_requests: requests || null
        })
      });
      setShowModal(false);
      setCustName("");
      setCustPhone("");
      await loadReservations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleStatusChange = async (resId: string, status: string) => {
    try {
      await apiRequest(`/reservations/${resId}/status?status_val=${status}`, {
        method: "PATCH"
      });
      await loadReservations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Table Reservations & Walk-ins</h1>
          <p className="text-xs text-ink-muted mt-1">Guest booking calendar, table assignment, and seamless dining check-ins.</p>
        </div>

        <button
          onClick={() => {
            const d = new Date();
            d.setHours(d.getHours() + 2);
            setResTime(d.toISOString().slice(0, 16));
            setShowModal(true);
          }}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Book Reservation
        </button>
      </div>

      {/* Reservations Table */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Guest Name</th>
                <th className="py-3 px-4">Contact Phone</th>
                <th className="py-3 px-4">Party Size</th>
                <th className="py-3 px-4">Table</th>
                <th className="py-3 px-4">Date & Time</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {reservations.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ink-subtle">
                    No reservations recorded. Click &quot;Book Reservation&quot; to schedule a table.
                  </td>
                </tr>
              ) : (
                reservations.map((res) => {
                  const tbl = tables.find(t => t.id === res.table_id);
                  return (
                    <tr key={res.id} className="hover:bg-row-hover transition">
                      <td className="py-3 px-4 font-bold text-ink">{res.customer_name}</td>
                      <td className="py-3 px-4 text-ink-3 font-mono text-[11px]">{res.customer_phone}</td>
                      <td className="py-3 px-4 text-ink-3">{res.party_size} Guests</td>
                      <td className="py-3 px-4 text-accent-brand font-semibold">{tbl?.table_number || "Unassigned"}</td>
                      <td className="py-3 px-4 text-ink-3">
                        {new Date(res.reservation_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          res.status === "CheckedIn" ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                          res.status === "Confirmed" ? "bg-tint-blue text-accent-blue border border-tint-blue-border" :
                          "bg-control text-ink-muted"
                        }`}>
                          {res.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1.5">
                        {res.status === "Confirmed" && (
                          <button
                            onClick={() => handleStatusChange(res.id, "CheckedIn")}
                            className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm"
                          >
                            Check-in Guest
                          </button>
                        )}
                        {res.status === "CheckedIn" && (
                          <button
                            onClick={() => handleStatusChange(res.id, "Completed")}
                            className="px-2.5 py-1 rounded bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold"
                          >
                            Complete
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Book Reservation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateReservation} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">New Table Reservation</h3>
              <button type="button" onClick={() => setShowModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Guest Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Priya Sharma"
                value={custName}
                onChange={(e) => setCustName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Phone Number</label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={custPhone}
                onChange={(e) => setCustPhone(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Party Size</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={partySize}
                  onChange={(e) => setPartySize(parseInt(e.target.value) || 2)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Assign Table</label>
                <select
                  value={tableId}
                  onChange={(e) => setTableId(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                >
                  {tables.map(t => <option key={t.id} value={t.id}>{t.table_number} ({t.capacity} seats)</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Date & Time</label>
              <input
                type="datetime-local"
                required
                value={resTime}
                onChange={(e) => setResTime(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Special Notes</label>
              <input
                type="text"
                placeholder="Window seat, high chair, birthday..."
                value={requests}
                onChange={(e) => setRequests(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Confirm Reservation
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
