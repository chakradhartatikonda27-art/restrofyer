"use client";

import { useEffect, useState } from "react";
import {
  Coins, ArrowUpRight, ArrowDownLeft, Lock, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function CashRegisterPage() {
  const [registers, setRegisters] = useState<any[]>([]);
  const [activeSession, setActiveSession] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const [showOpenModal, setShowOpenModal] = useState(false);
  const [openRegisterId, setOpenRegisterId] = useState("");
  const [openingFloat, setOpeningFloat] = useState<number>(2000);

  const [showTxModal, setShowTxModal] = useState(false);
  const [txType, setTxType] = useState<string>("CASH_IN");
  const [txAmount, setTxAmount] = useState<number>(200);
  const [txReason, setTxReason] = useState<string>("");

  const [showCloseModal, setShowCloseModal] = useState(false);
  const [countedCash, setCountedCash] = useState<number>(0);
  const [closeNotes, setCloseNotes] = useState("");

  useEffect(() => {
    loadRegisterData();
  }, []);

  const loadRegisterData = async () => {
    setLoading(true);
    try {
      const regs = await apiRequest("/cash-registers");
      setRegisters(regs);
      if (regs.length > 0 && !openRegisterId) {
        setOpenRegisterId(regs[0].id);
      }

      try {
        const session = await apiRequest("/cash-registers/active-session");
        setActiveSession(session);
        setCountedCash(session.expected_closing_cash);
      } catch {
        setActiveSession(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenShift = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/cash-registers/open", {
        method: "POST",
        body: JSON.stringify({ register_id: openRegisterId, opening_float: openingFloat })
      });
      setShowOpenModal(false);
      await loadRegisterData();
    } catch (err: any) {
      alert(`Open failed: ${err.message}`);
    }
  };

  const handleCashInOut = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession) return;
    try {
      await apiRequest(`/cash-registers/sessions/${activeSession.id}/transactions`, {
        method: "POST",
        body: JSON.stringify({ transaction_type: txType, amount: txAmount, reason: txReason })
      });
      setShowTxModal(false);
      setTxReason("");
      await loadRegisterData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCloseShift = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession) return;
    try {
      const res = await apiRequest(`/cash-registers/sessions/${activeSession.id}/close`, {
        method: "POST",
        body: JSON.stringify({ actual_closing_cash: countedCash, notes: closeNotes || null })
      });
      alert(`Shift closed! Expected: ₹${res.expected_closing_cash.toFixed(2)}, Actual: ₹${res.actual_closing_cash.toFixed(2)}, Variance: ₹${res.variance.toFixed(2)}`);
      setShowCloseModal(false);
      await loadRegisterData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Cash Register Shifts & Drawer Reconciliation</h1>
          <p className="text-xs text-ink-muted mt-1">Cash drawer tracking, shift opening floats, in/out payouts, and variance formula auditing.</p>
        </div>

        {!activeSession ? (
          <button
            onClick={() => setShowOpenModal(true)}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Coins className="w-4 h-4" /> Open Shift Drawer
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTxModal(true)}
              className="px-3.5 py-2 bg-control hover:bg-control-hover text-ink-2 border border-line-strong rounded-xl text-xs font-bold transition flex items-center gap-1.5"
            >
              Cash In / Out
            </button>
            <button
              onClick={() => setShowCloseModal(true)}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-md shadow-rose-600/20 transition flex items-center gap-1.5"
            >
              <Lock className="w-4 h-4" /> Close Shift & Reconcile
            </button>
          </div>
        )}
      </div>

      {/* Active Shift Details or Closed Drawer Banner */}
      {!activeSession ? (
        <div className="p-16 text-center rounded-2xl bg-panel border border-line shadow-sm">
          <Coins className="w-12 h-12 text-ink-subtle mx-auto mb-3 stroke-[1.5]" />
          <h3 className="text-base font-bold text-ink">Cash Register is Currently Closed</h3>
          <p className="text-xs text-ink-muted mt-1">Open a new shift session by counting your opening cash float.</p>
          <button
            onClick={() => setShowOpenModal(true)}
            className="mt-4 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold transition"
          >
            Start Shift
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Opening Float</span>
              <div className="text-base font-black text-ink mt-1">₹{activeSession.opening_float.toFixed(2)}</div>
            </div>
            <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">+ Cash Sales</span>
              <div className="text-base font-black text-accent-emerald mt-1">₹{activeSession.cash_sales.toFixed(2)}</div>
            </div>
            <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">+ Cash In</span>
              <div className="text-base font-black text-accent-sky mt-1">₹{activeSession.cash_in.toFixed(2)}</div>
            </div>
            <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">- Cash Out</span>
              <div className="text-base font-black text-accent-amber mt-1">₹{activeSession.cash_out.toFixed(2)}</div>
            </div>
            <div className="p-4 rounded-xl bg-panel border border-line shadow-sm">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">- Cash Refunds</span>
              <div className="text-base font-black text-accent-rose mt-1">₹{activeSession.cash_refunds.toFixed(2)}</div>
            </div>
            <div className="p-4 rounded-xl bg-tint-brand border border-tint-brand-border shadow-sm">
              <span className="text-[10px] uppercase font-bold text-accent-brand">= Expected Cash</span>
              <div className="text-base font-black text-accent-brand mt-1">₹{activeSession.expected_closing_cash.toFixed(2)}</div>
            </div>
          </div>

          <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Active Shift Transactions & Auditing</h3>
                <p className="text-xs text-ink-muted">
                  Cashier: <span className="text-ink font-semibold">{activeSession.cashier_name}</span> • Started: {new Date(activeSession.opened_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <button
                onClick={() => setShowTxModal(true)}
                className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs transition"
              >
                + Record Cash In/Out
              </button>
            </div>

            <div className="space-y-2">
              {activeSession.transactions?.length === 0 ? (
                <div className="p-6 text-center text-xs text-ink-subtle">
                  No manual cash drawer adjustments in this shift session yet.
                </div>
              ) : (
                activeSession.transactions?.map((tx: any) => (
                  <div key={tx.id} className="p-3 rounded-xl bg-well border border-line flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <span className={`p-1.5 rounded-lg ${
                        tx.transaction_type === "CASH_IN" ? "bg-tint-emerald text-accent-emerald" : "bg-tint-amber text-accent-amber"
                      }`}>
                        {tx.transaction_type === "CASH_IN" ? <ArrowDownLeft className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                      </span>
                      <div>
                        <div className="font-bold text-ink">{tx.reason}</div>
                        <div className="text-[10px] text-ink-subtle">Authorized by: {tx.authorized_by}</div>
                      </div>
                    </div>
                    <div className={`font-mono font-bold ${tx.transaction_type === "CASH_IN" ? "text-accent-emerald" : "text-accent-amber"}`}>
                      {tx.transaction_type === "CASH_IN" ? "+" : "-"}₹{tx.amount.toFixed(2)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Open Shift Modal */}
      {showOpenModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleOpenShift} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Open Cash Register Shift</h3>
              <button type="button" onClick={() => setShowOpenModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Select Terminal</label>
              <select
                value={openRegisterId}
                onChange={(e) => setOpenRegisterId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                {registers.map(r => <option key={r.id} value={r.id}>{r.name} ({r.status})</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Opening Cash Float (₹)</label>
              <input
                type="number"
                step="0.01"
                required
                value={openingFloat}
                onChange={(e) => setOpeningFloat(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Verify Float & Open Register
            </button>
          </form>
        </div>
      )}

      {/* Cash In / Out Modal */}
      {showTxModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCashInOut} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Drawer Cash In / Cash Out</h3>
              <button type="button" onClick={() => setShowTxModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setTxType("CASH_IN")}
                className={`py-2 rounded-lg text-xs font-bold border transition ${
                  txType === "CASH_IN" ? "bg-tint-emerald border-emerald-500 text-accent-emerald" : "bg-well border-line text-ink-muted"
                }`}
              >
                + Cash In (Float)
              </button>
              <button
                type="button"
                onClick={() => setTxType("CASH_OUT")}
                className={`py-2 rounded-lg text-xs font-bold border transition ${
                  txType === "CASH_OUT" ? "bg-tint-amber border-amber-500 text-accent-amber" : "bg-well border-line text-ink-muted"
                }`}
              >
                - Cash Out (Payout)
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                required
                value={txAmount}
                onChange={(e) => setTxAmount(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Justification Reason</label>
              <input
                type="text"
                required
                placeholder="e.g. Additional change float, Ice payout..."
                value={txReason}
                onChange={(e) => setTxReason(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Record Drawer Movement
            </button>
          </form>
        </div>
      )}

      {/* Close Shift & Reconcile Modal */}
      {showCloseModal && activeSession && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCloseShift} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Reconcile & Close Register</h3>
              <button type="button" onClick={() => setShowCloseModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-well border border-line text-xs space-y-1">
              <div className="flex justify-between text-ink-muted">
                <span>System Expected Cash:</span>
                <span className="font-mono font-bold text-ink">₹{activeSession.expected_closing_cash.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-ink-muted">
                <span>Actual Counted Cash:</span>
                <span className="font-mono font-bold text-accent-amber">₹{countedCash.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold pt-1 border-t border-line">
                <span>Variance (Actual - Expected):</span>
                <span className={`font-mono ${countedCash - activeSession.expected_closing_cash === 0 ? "text-accent-emerald" : "text-accent-rose"}`}>
                  ₹{(countedCash - activeSession.expected_closing_cash).toFixed(2)}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Physical Cash Counted in Drawer (₹)</label>
              <input
                type="number"
                step="0.01"
                required
                value={countedCash}
                onChange={(e) => setCountedCash(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Closing Notes / Discrepancy Reason</label>
              <input
                type="text"
                placeholder="End of night shift reconciliation..."
                value={closeNotes}
                onChange={(e) => setCloseNotes(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 transition">
              Confirm Variance & Close Shift
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
