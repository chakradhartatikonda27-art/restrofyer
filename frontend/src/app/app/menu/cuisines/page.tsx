"use client";

import { useEffect, useState } from "react";
import { Pencil, Plus, Search, Sparkles, Trash2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ModalDialog } from "@/components/ModalDialog";
import { CuisineRecord } from "@/components/menu/MenuTypes";

export default function CuisinesPage() {
  const [cuisines, setCuisines] = useState<CuisineRecord[]>([]);
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<CuisineRecord | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [displayOrder, setDisplayOrder] = useState(1);
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [applyingTemplate, setApplyingTemplate] = useState(false);

  useEffect(() => {
    loadData();
  }, [showInactive]);

  const loadData = async () => {
    try {
      const data = await apiRequest(`/menus/cuisines?include_inactive=${showInactive ? "true" : "false"}`);
      setCuisines(data);
    } catch (err) {
      console.error(err);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setName("");
    setDescription("");
    setDisplayOrder(cuisines.length + 1);
    setIsActive(true);
    setDialogOpen(true);
  };

  const openEdit = (c: CuisineRecord) => {
    setEditing(c);
    setName(c.name);
    setDescription(c.description || "");
    setDisplayOrder(c.display_order || 1);
    setIsActive(c.is_active);
    setDialogOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        description: description.trim() || null,
        display_order: displayOrder,
        is_active: isActive,
      };
      if (editing) {
        await apiRequest(`/menus/cuisines/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest("/menus/cuisines", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      setDialogOpen(false);
      await loadData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (c: CuisineRecord) => {
    try {
      await apiRequest(`/menus/cuisines/${c.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !c.is_active }),
      });
      await loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (c: CuisineRecord) => {
    if (!confirm(`Delete cuisine "${c.name}"?`)) return;
    try {
      await apiRequest(`/menus/cuisines/${c.id}`, { method: "DELETE" });
      await loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleApplyIndianDefaults = async () => {
    setApplyingTemplate(true);
    try {
      const res = await apiRequest("/menus/templates/apply-indian-default", {
        method: "POST",
        body: JSON.stringify({
          include_sample_dishes: false,
          create_scheduled_menus: false,
        }),
      });
      await loadData();
      alert(
        `Applied template: +${res.created_cuisines} cuisines, +${res.created_categories} dish categories.`
      );
    } catch (err: any) {
      alert(err.message);
    } finally {
      setApplyingTemplate(false);
    }
  };

  const filtered = cuisines.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink">Cuisines & Regional Sections</h1>
          <p className="text-sm text-ink-muted mt-0.5">
            Dimension 1 of Menu Hierarchy — keep cuisines separate from Food Type and Dish Category.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={applyingTemplate}
            onClick={handleApplyIndianDefaults}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-accent-brand" />
            <span>{applyingTemplate ? "Applying..." : "Load Indian Default Cuisines"}</span>
          </button>
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add Cuisine</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 bg-panel border border-line rounded-2xl p-3">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search cuisines..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-xl text-xs text-ink"
          />
        </div>
        <label className="inline-flex items-center gap-2 text-xs text-ink-3 cursor-pointer px-2">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="w-4 h-4 rounded accent-brand-600"
          />
          <span>Show deactivated cuisines</span>
        </label>
      </div>

      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3.5 px-4 font-bold">Order</th>
                <th className="py-3.5 px-4 font-bold">Cuisine Name</th>
                <th className="py-3.5 px-4 font-bold">Description</th>
                <th className="py-3.5 px-4 font-bold text-center">Dishes</th>
                <th className="py-3.5 px-4 font-bold text-center">Active</th>
                <th className="py-3.5 px-4 font-bold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-xs text-ink-subtle">
                    No cuisines configured yet. Add custom cuisines or load the default Indian template.
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-row-hover transition">
                    <td className="py-3.5 px-4 font-mono text-ink-muted">#{c.display_order}</td>
                    <td className="py-3.5 px-4 font-bold text-sm text-ink">{c.name}</td>
                    <td className="py-3.5 px-4 text-ink-3 max-w-md">{c.description || "—"}</td>
                    <td className="py-3.5 px-4 text-center font-semibold text-ink">{c.item_count}</td>
                    <td className="py-3.5 px-4 text-center">
                      <input
                        type="checkbox"
                        checked={c.is_active}
                        onChange={() => toggleActive(c)}
                        aria-label={`Toggle active status for ${c.name}`}
                        className="w-4 h-4 rounded accent-brand-600 cursor-pointer"
                      />
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => openEdit(c)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(c)}
                          className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80 transition"
                          title={`Delete ${c.name}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <ModalDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? `Update Cuisine — ${editing.name}` : "Add Cuisine"}
        subtitle="Customize regional sections such as South Indian, North Indian, Chinese, or Continental."
        maxWidthClass="max-w-md"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Cuisine Name</label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g. South Indian"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Description</label>
            <textarea
              rows={2}
              placeholder="Dosa, Idli, Vada, Andhra & coastal rice staples..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            />
          </div>
          <div className="grid grid-cols-2 gap-3 items-center">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Display Order</label>
              <input
                type="number"
                min={0}
                value={displayOrder}
                onChange={(e) => setDisplayOrder(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>
            <label className="inline-flex items-center gap-2 text-xs text-ink-2 pt-4 cursor-pointer">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 rounded accent-brand-600"
              />
              <span>Active</span>
            </label>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={() => setDialogOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : editing ? "Update Cuisine" : "Create Cuisine"}
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
}
