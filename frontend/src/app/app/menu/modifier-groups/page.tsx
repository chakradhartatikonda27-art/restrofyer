"use client";

import { useEffect, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ModalDialog } from "@/components/ModalDialog";
import { MenuItemRecord, ModifierGroup } from "@/components/menu/MenuTypes";

export default function ModifierGroupsPage() {
  const [groups, setGroups] = useState<ModifierGroup[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItemRecord[]>([]);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ModifierGroup | null>(null);

  const [name, setName] = useState("");
  const [itemId, setItemId] = useState("");
  const [minSel, setMinSel] = useState<number>(0);
  const [maxSel, setMaxSel] = useState<number>(3);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [groupsRes, itemsRes] = await Promise.all([
        apiRequest("/menus/modifier-groups"),
        apiRequest("/menus/items"),
      ]);
      setGroups(groupsRes);
      setMenuItems(itemsRes);
    } catch (err) {
      console.error(err);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setName("");
    setItemId(menuItems[0]?.id || "");
    setMinSel(0);
    setMaxSel(3);
    setDialogOpen(true);
  };

  const openEdit = (g: ModifierGroup) => {
    setEditing(g);
    setName(g.name);
    setItemId(g.item_id || menuItems[0]?.id || "");
    setMinSel(g.min_selection);
    setMaxSel(g.max_selection);
    setDialogOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await apiRequest(`/menus/modifier-groups/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify({
            item_id: itemId,
            name: name.trim(),
            min_selection: minSel,
            max_selection: maxSel,
          }),
        });
      } else {
        await apiRequest("/menus/modifier-groups", {
          method: "POST",
          body: JSON.stringify({
            item_id: itemId,
            name: name.trim(),
            min_selection: minSel,
            max_selection: maxSel,
            modifiers: [],
          }),
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

  const handleDelete = async (g: ModifierGroup) => {
    if (!confirm(`Delete modifier group "${g.name}" and its options?`)) return;
    await apiRequest(`/menus/modifier-groups/${g.id}`, { method: "DELETE" });
    await loadData();
  };

  const filtered = groups.filter(
    (g) =>
      g.name.toLowerCase().includes(search.toLowerCase()) ||
      (g.item_name || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Modifier Groups</h1>
          <p className="text-xs text-ink-muted mt-1">
            Define required and optional customization groups such as Spice Level or Extra Toppings.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add Modifier Group
        </button>
      </div>

      <div className="p-4 rounded-2xl bg-panel border border-line flex items-center justify-between gap-3 shadow-sm">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search modifier groups or dishes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle"
          />
        </div>
        <div className="text-xs text-ink-muted font-semibold">{filtered.length} group(s)</div>
      </div>

      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Group Name</th>
                <th className="py-3 px-4">Linked Menu Item</th>
                <th className="py-3 px-4">Selection Rules</th>
                <th className="py-3 px-4">Included Options</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filtered.map((g) => (
                <tr key={g.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-4 font-bold text-ink">{g.name}</td>
                  <td className="py-3 px-4 text-ink-3">{g.item_name || "Menu Item"}</td>
                  <td className="py-3 px-4 text-ink-muted">
                    Min {g.min_selection} • Max {g.max_selection}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1.5">
                      {g.modifiers.length === 0 ? (
                        <span className="text-ink-subtle text-[11px]">No options yet</span>
                      ) : (
                        g.modifiers.map((m) => (
                          <span
                            key={m.id}
                            className="px-2 py-0.5 rounded bg-well border border-line text-[11px] text-ink-3"
                          >
                            {m.name} (+₹{m.price.toFixed(0)})
                          </span>
                        ))
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <div className="inline-flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(g)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold"
                      >
                        <Pencil className="w-3.5 h-3.5" /> Update
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(g)}
                        aria-label={`Delete ${g.name}`}
                        className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <ModalDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? `Update Modifier Group — ${editing.name}` : "Add Modifier Group"}
        maxWidthClass="max-w-md"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Group Name</label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g. Spice Level"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Menu Item</label>
            <select
              required
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            >
              {menuItems.map((it) => (
                <option key={it.id} value={it.id}>{it.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Min Selection</label>
              <input
                type="number"
                min={0}
                value={minSel}
                onChange={(e) => setMinSel(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Max Selection</label>
              <input
                type="number"
                min={1}
                value={maxSel}
                onChange={(e) => setMaxSel(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>
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
              {saving ? "Saving..." : "Save Group"}
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
}
