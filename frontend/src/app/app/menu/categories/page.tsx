"use client";

import { useEffect, useState } from "react";
import { Pencil, Plus, Search, Sparkles, Trash2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ModalDialog } from "@/components/ModalDialog";
import { MenuCategory, MenuSummary } from "@/components/menu/MenuTypes";

export default function DishCategoriesPage() {
  const [categories, setCategories] = useState<MenuCategory[]>([]);
  const [menus, setMenus] = useState<MenuSummary[]>([]);
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MenuCategory | null>(null);

  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [menuId, setMenuId] = useState("");
  const [displayOrder, setDisplayOrder] = useState<number>(1);
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    loadData();
  }, [showInactive]);

  const loadData = async () => {
    try {
      const [catsRes, menusRes] = await Promise.all([
        apiRequest(`/menus/categories?include_inactive=${showInactive ? "true" : "false"}`),
        apiRequest("/menus"),
      ]);
      setCategories(catsRes);
      setMenus(menusRes);
    } catch (err) {
      console.error(err);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setName("");
    setParentId("");
    setMenuId("");
    setDisplayOrder(categories.length + 1);
    setIsActive(true);
    setDialogOpen(true);
  };

  const openEdit = (cat: MenuCategory) => {
    setEditing(cat);
    setName(cat.name);
    setParentId(cat.parent_id || "");
    setMenuId(cat.menu_id || "");
    setDisplayOrder(cat.display_order || 1);
    setIsActive(cat.is_active);
    setDialogOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        parent_id: parentId || null,
        menu_id: menuId || null,
        display_order: displayOrder,
        is_active: isActive,
      };
      if (editing) {
        await apiRequest(`/menus/categories/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest("/menus/categories", {
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

  const toggleActive = async (cat: MenuCategory) => {
    try {
      await apiRequest(`/menus/categories/${cat.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !cat.is_active }),
      });
      await loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (cat: MenuCategory) => {
    if (!confirm(`Delete dish category "${cat.name}"?`)) return;
    try {
      await apiRequest(`/menus/categories/${cat.id}`, { method: "DELETE" });
      await loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleLoadIndianCategories = async () => {
    setApplying(true);
    try {
      const res = await apiRequest("/menus/templates/apply-indian-default", {
        method: "POST",
        body: JSON.stringify({
          include_sample_dishes: false,
          create_scheduled_menus: false,
        }),
      });
      await loadData();
      alert(`Loaded +${res.created_categories} default dish categories & +${res.created_cuisines} cuisines.`);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setApplying(false);
    }
  };

  const topLevelCategories = categories.filter((c) => !c.parent_id && (!editing || c.id !== editing.id));

  const filtered = categories.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.parent_name || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Dish Categories & Subcategories</h1>
          <p className="text-xs text-ink-muted mt-1">
            Dimension 3 of Menu Hierarchy — organize Starters, Tiffins, Curries, Biryani, Breads & custom subcategories.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={applying}
            onClick={handleLoadIndianCategories}
            className="px-3.5 py-2 rounded-xl border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-accent-brand" />
            <span>{applying ? "Loading..." : "Load Indian Default Categories"}</span>
          </button>
          <button
            type="button"
            onClick={openCreate}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Dish Category
          </button>
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-panel border border-line flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search categories or subcategories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle"
          />
        </div>
        <div className="flex items-center gap-4">
          <label className="inline-flex items-center gap-2 text-xs text-ink-3 cursor-pointer">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4 rounded accent-brand-600"
            />
            <span>Show deactivated</span>
          </label>
          <span className="text-xs text-ink-muted font-semibold">{filtered.length} category(s)</span>
        </div>
      </div>

      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Order</th>
                <th className="py-3 px-4">Category / Subcategory</th>
                <th className="py-3 px-4">Parent Category</th>
                <th className="py-3 px-4">Default Menu</th>
                <th className="py-3 px-4">Total Items</th>
                <th className="py-3 px-4 text-center">Active</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filtered.map((cat) => {
                const parentMenu = menus.find((m) => m.id === cat.menu_id);
                return (
                  <tr key={cat.id} className="hover:bg-row-hover transition">
                    <td className="py-3 px-4 font-mono text-ink-muted">#{cat.display_order}</td>
                    <td className="py-3 px-4 font-bold text-ink">
                      {cat.parent_id ? (
                        <span className="inline-flex items-center gap-1.5">
                          <span className="text-ink-subtle">↳</span>
                          <span>{cat.name}</span>
                          <span className="px-1.5 py-0.5 rounded bg-well border border-line text-[10px] text-ink-muted">
                            Subcategory
                          </span>
                        </span>
                      ) : (
                        cat.name
                      )}
                    </td>
                    <td className="py-3 px-4 text-ink-3">{cat.parent_name || "Top Level"}</td>
                    <td className="py-3 px-4 text-ink-3">{parentMenu?.name || "Global / Shared"}</td>
                    <td className="py-3 px-4">
                      <span className="px-2.5 py-0.5 rounded-full bg-control text-ink-2 font-semibold text-[11px]">
                        {cat.item_count} Item(s)
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <input
                        type="checkbox"
                        checked={cat.is_active}
                        onChange={() => toggleActive(cat)}
                        aria-label={`Toggle active status for ${cat.name}`}
                        className="w-4 h-4 rounded accent-brand-600 cursor-pointer"
                      />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => openEdit(cat)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold"
                        >
                          <Pencil className="w-3.5 h-3.5" /> Update
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(cat)}
                          aria-label={`Delete ${cat.name}`}
                          className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <ModalDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? `Update Category — ${editing.name}` : "Add Dish Category"}
        subtitle="Create top-level categories (Starters, Curries) or nested subcategories."
        maxWidthClass="max-w-md"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Category Name</label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g. Curries & Gravies"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Parent Category (Optional Subcategory)</label>
            <select
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            >
              <option value="">None (Top-Level Category)</option>
              {topLevelCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Default Menu</label>
              <select
                value={menuId}
                onChange={(e) => setMenuId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                <option value="">Global / Shared</option>
                {menus.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
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
          </div>
          <label className="inline-flex items-center gap-2 text-xs text-ink-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 rounded accent-brand-600"
            />
            <span>Active category</span>
          </label>
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
              {saving ? "Saving..." : "Save Category"}
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
}
