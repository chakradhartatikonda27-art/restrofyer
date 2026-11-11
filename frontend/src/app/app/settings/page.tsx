"use client";

import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ThemePreferenceSelector } from "@/components/ThemeToggle";

export default function SettingsAndStaffPage() {
  const [branches, setBranches] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showBranchModal, setShowBranchModal] = useState(false);
  const [branchName, setBranchName] = useState("");
  const [branchCode, setBranchCode] = useState("");
  const [branchAddress, setBranchAddress] = useState("");
  const [taxRate, setTaxRate] = useState(5.0);

  const [showUserModal, setShowUserModal] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [staffPassword, setStaffPassword] = useState("Staff@123");
  const [staffRole, setStaffRole] = useState("CASHIER");
  const [staffPhone] = useState("");
  const [staffBranchId, setStaffBranchId] = useState("");

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const [branchData, userData] = await Promise.all([
        apiRequest("/branches"),
        apiRequest("/users")
      ]);
      setBranches(branchData);
      setUsers(userData);
      if (branchData.length > 0 && !staffBranchId) {
        setStaffBranchId(branchData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/branches", {
        method: "POST",
        body: JSON.stringify({
          name: branchName,
          code: branchCode,
          address: branchAddress,
          tax_rate: taxRate
        })
      });
      setShowBranchModal(false);
      setBranchName("");
      setBranchCode("");
      setBranchAddress("");
      await loadSettings();
    } catch (err: any) {
      alert(`Branch creation failed: ${err.message}`);
    }
  };

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/users", {
        method: "POST",
        body: JSON.stringify({
          full_name: staffName,
          email: staffEmail,
          password: staffPassword,
          role: staffRole,
          phone: staffPhone || null,
          branch_id: staffBranchId || null
        })
      });
      setShowUserModal(false);
      setStaffName("");
      setStaffEmail("");
      await loadSettings();
    } catch (err: any) {
      alert(`Staff invitation failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-ink tracking-tight">Organization Settings & Staff RBAC</h1>
        <p className="text-xs text-ink-muted mt-1">Configure display appearance, multi-branch locations, tax regulations, and granular employee permissions.</p>
      </div>

      {/* Display Appearance Theme Section */}
      <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
        <div className="border-b border-line pb-3">
          <h2 className="text-base font-bold text-ink">Display & Interface Appearance</h2>
          <p className="text-xs text-ink-muted">Choose crisp white daylight canvas, dark mode, or follow your operating system setting.</p>
        </div>
        <ThemePreferenceSelector />
      </div>

      {/* Multi-Branch Management Section */}
      <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div>
            <h2 className="text-base font-bold text-ink">Restaurant Branches & Locations</h2>
            <p className="text-xs text-ink-muted">Independent kitchens, dining floors, and localized tax profiles</p>
          </div>
          <button
            onClick={() => setShowBranchModal(true)}
            className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Branch
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {branches.map((b) => (
            <div key={b.id} className="p-4 rounded-xl bg-well border border-line text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-ink">{b.name}</span>
                <span className="px-2 py-0.5 rounded bg-control text-ink-3 font-mono text-[10px]">{b.code}</span>
              </div>
              <div className="text-ink-muted">{b.address}, {b.city}</div>
              <div className="text-ink-subtle text-[11px] pt-1 border-t border-line flex justify-between">
                <span>Tax Rate: {b.tax_rate}%</span>
                <span className="text-accent-emerald font-bold">Active Branch</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Staff & Workforce RBAC Section */}
      <div className="bg-panel border border-line rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div>
            <h2 className="text-base font-bold text-ink">Staff Workforce & Role-Based Access (RBAC)</h2>
            <p className="text-xs text-ink-muted">Manage employee accounts across kitchen, cashier, and manager positions</p>
          </div>
          <button
            onClick={() => setShowUserModal(true)}
            className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Staff Member
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Full Name</th>
                <th className="py-2.5 px-3">Work Email</th>
                <th className="py-2.5 px-3">System Role</th>
                <th className="py-2.5 px-3">Phone</th>
                <th className="py-2.5 px-3">Assigned Branch</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {users.map((u) => {
                const b = branches.find(br => br.id === u.branch_id);
                return (
                  <tr key={u.id} className="hover:bg-row-hover transition">
                    <td className="py-3 px-3 font-bold text-ink">{u.full_name}</td>
                    <td className="py-3 px-3 text-ink-3 font-mono text-[11px]">{u.email}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-tint-brand border border-tint-brand-border text-accent-brand text-[10px] font-bold">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-ink-muted">{u.phone || "N/A"}</td>
                    <td className="py-3 px-3 text-ink-3">{b?.name || "All Branches"}</td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[10px] text-accent-emerald font-bold bg-tint-emerald px-2 py-0.5 rounded border border-tint-emerald-border">
                        Active
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Branch Modal */}
      {showBranchModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateBranch} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Deploy New Branch</h3>
              <button type="button" onClick={() => setShowBranchModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Branch Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Bella Napoli - Gachibowli"
                value={branchName}
                onChange={(e) => setBranchName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Branch Internal Code</label>
              <input
                type="text"
                required
                placeholder="e.g. BN-GC-03"
                value={branchCode}
                onChange={(e) => setBranchCode(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Physical Address</label>
              <input
                type="text"
                required
                placeholder="e.g. Financial District"
                value={branchAddress}
                onChange={(e) => setBranchAddress(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">GST / Tax Rate (%)</label>
              <input
                type="number"
                step="0.1"
                required
                value={taxRate}
                onChange={(e) => setTaxRate(parseFloat(e.target.value) || 5.0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Create Branch (Plan Entitlement Enforced)
            </button>
          </form>
        </div>
      )}

      {/* Add Staff Modal */}
      {showUserModal && (
        <div className="fixed inset-0 z-50 bg-backdrop backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateStaff} className="bg-panel border border-line rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-bold text-ink">Add Staff Member</h3>
              <button type="button" onClick={() => setShowUserModal(false)} className="text-ink-muted hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Alex Fernandes"
                value={staffName}
                onChange={(e) => setStaffName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Work Email</label>
              <input
                type="email"
                required
                placeholder="alex@restaurant.com"
                value={staffEmail}
                onChange={(e) => setStaffEmail(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">System Role</label>
                <select
                  value={staffRole}
                  onChange={(e) => setStaffRole(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                >
                  <option value="BRANCH_MANAGER">Branch Manager</option>
                  <option value="CASHIER">Cashier (POS)</option>
                  <option value="WAITER">Waiter</option>
                  <option value="KITCHEN_STAFF">Chef / Cook</option>
                  <option value="INVENTORY_MANAGER">Inventory Mgr</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Assign Branch</label>
                <select
                  value={staffBranchId}
                  onChange={(e) => setStaffBranchId(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
                >
                  {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Temporary Password</label>
              <input
                type="text"
                required
                value={staffPassword}
                onChange={(e) => setStaffPassword(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <button type="submit" className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition">
              Create Employee Profile
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
