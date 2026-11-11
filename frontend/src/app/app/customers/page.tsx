"use client";

import { useEffect, useState } from "react";
import {
  Plus, Search, Award, X
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function CustomerCRMPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [segmentFilter, setSegmentFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const [showAddModal, setShowAddModal] = useState(false);
  const [custName, setCustName] = useState("");
  const [custPhone, setCustPhone] = useState("");
  const [custEmail, setCustEmail] = useState("");
  const [custNotes, setCustNotes] = useState("");
  const [custAddress] = useState("");

  const [activeCustomer, setActiveCustomer] = useState<any | null>(null);
  const [loyaltyHistory, setLoyaltyHistory] = useState<any | null>(null);

  useEffect(() => {
    loadCustomers();
  }, [segmentFilter]);

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const query = `/crm${segmentFilter ? `?segment=${segmentFilter}` : ''}`;
      const data = await apiRequest(query);
      setCustomers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/crm", {
        method: "POST",
        body: JSON.stringify({
          name: custName,
          phone: custPhone,
          email: custEmail || null,
          notes: custNotes || null,
          address: custAddress || null
        })
      });
      setShowAddModal(false);
      setCustName("");
      setCustPhone("");
      await loadCustomers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openLoyaltyHistory = async (customer: any) => {
    setActiveCustomer(customer);
    try {
      const history = await apiRequest(`/loyalty/customers/${customer.id}/transactions`);
      setLoyaltyHistory(history);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredCustomers = customers.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.phone.includes(search)
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Customer CRM & Loyalty Ledgers</h1>
          <p className="text-xs text-ink-muted mt-1">Guest profiles, lifetime spend analytics, and ledger-verified loyalty points.</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add Customer
        </button>
      </div>

      {/* Filter Strip */}
      <div className="p-4 rounded-2xl bg-panel border border-line flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search customer name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={segmentFilter}
            onChange={(e) => setSegmentFilter(e.target.value)}
            className="px-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink-3"
          >
            <option value="">All Segments</option>
            <option value="VIP">VIP Diners</option>
            <option value="Returning">Returning Customers</option>
            <option value="New">New Guests</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Customer Name</th>
                <th className="py-3 px-4">Contact Phone</th>
                <th className="py-3 px-4">Segment</th>
                <th className="py-3 px-4">Total Visits</th>
                <th className="py-3 px-4">Lifetime Spend</th>
                <th className="py-3 px-4">Loyalty Balance</th>
                <th className="py-3 px-4 text-right">Loyalty Ledger</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filteredCustomers.map((cust) => (
                <tr key={cust.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-4">
                    <div className="font-bold text-ink">{cust.name}</div>
                    {cust.notes && <div className="text-[10px] text-accent-amber truncate max-w-xs">{cust.notes}</div>}
                  </td>
                  <td className="py-3 px-4 text-ink-3 font-mono text-[11px]">{cust.phone}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      cust.segment === "VIP" ? "bg-tint-amber text-accent-amber border border-tint-amber-border" :
                      cust.segment === "Returning" ? "bg-tint-brand text-accent-brand border border-tint-brand-border" :
                      "bg-control text-ink-muted"
                    }`}>
                      {cust.segment}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-ink-3">{cust.total_visits} visits</td>
                  <td className="py-3 px-4 font-black text-ink">
                    ₹{cust.total_spend.toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1 font-bold text-accent-amber bg-tint-amber px-2 py-0.5 rounded-md border border-tint-amber-border">
                      <Award className="w-3.5 h-3.5" />
                      {cust.loyalty_points} pts ({cust.loyalty_tier})
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => openLoyaltyHistory(cust)}
                      className="px-2.5 py-1 rounded-lg bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold transition"
                    >
                      Audit Ledger
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Loyalty Ledger Drawer Modal */}
      {activeCustomer && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-panel border border-line rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Loyalty Points Ledger</h3>
                <p className="text-xs text-ink-muted">{activeCustomer.name} • {loyaltyHistory?.tier} Tier</p>
              </div>
              <button onClick={() => setActiveCustomer(null)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-well border border-line text-center">
              <span className="text-[10px] uppercase font-bold text-ink-subtle">Verified Ledger Balance</span>
              <div className="text-3xl font-black text-accent-amber mt-1">
                {loyaltyHistory?.points_balance || activeCustomer.loyalty_points} Points
              </div>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              <h4 className="text-xs font-bold text-ink-3">Transaction History (Double-Entry)</h4>
              {loyaltyHistory?.transactions?.map((tx: any) => (
                <div key={tx.id} className="p-2.5 rounded-lg bg-well border border-line text-xs flex items-center justify-between">
                  <div>
                    <span className={`font-bold ${tx.points >= 0 ? "text-accent-emerald" : "text-accent-rose"}`}>
                      {tx.points >= 0 ? `+${tx.points}` : tx.points} pts
                    </span>
                    <span className="text-ink-muted ml-2">{tx.reason}</span>
                  </div>
                  <span className="text-[10px] text-ink-subtle font-mono">
                    Bal: {tx.running_balance}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={() => setActiveCustomer(null)}
              className="w-full py-2.5 rounded-xl text-xs font-bold text-ink-3 bg-control hover:bg-control-hover transition"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Add Customer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateCustomer} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Create Customer Profile</h3>
              <button type="button" onClick={() => setShowAddModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Rahul Sen"
                value={custName}
                onChange={(e) => setCustName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Mobile Phone</label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={custPhone}
                onChange={(e) => setCustPhone(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Email (Optional)</label>
              <input
                type="email"
                placeholder="guest@gmail.com"
                value={custEmail}
                onChange={(e) => setCustEmail(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Preferences & Notes</label>
              <textarea
                rows={2}
                placeholder="Allergies, table preferences, favorite drinks..."
                value={custNotes}
                onChange={(e) => setCustNotes(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Save Customer & Create Loyalty Account
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
