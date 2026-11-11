"use client";

import { useEffect, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ModalDialog } from "@/components/ModalDialog";
import { ItemModifier, ModifierGroup } from "@/components/menu/MenuTypes";

export default function ItemModifiersPage() {
  const [modifiers, setModifiers] = useState<ItemModifier[]>([]);
  const [groups, setGroups] = useState<ModifierGroup[]>([]);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ItemModifier | null>(null);

  const [name, setName] = useState("");
  const [groupId, setGroupId] = useState("");
  const [price, setPrice] = useState<number>(20);
  const [isAvailable, setIsAvailable] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [modsRes, groupsRes] = await Promise.all([
        apiRequest("/menus/modifiers"),
        apiRequest("/menus/modifier-groups"),
      ]);
      setModifiers(modsRes);
      setGroups(groupsRes);
    } catch (err) {
      console.error(err);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setName("");
    setGroupId(groups[0]?.id || "");
    setPrice(20);
    setIsAvailable(true);
    setDialogOpen(true);
  };

  const openEdit = (mod: ItemModifier) => {
    setEditing(mod);
    setName(mod.name);
    setGroupId(mod.group_id || groups[0]?.id || "");
    setPrice(mod.price);
    setIsAvailable(mod.is_available);
    setDialogOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await apiRequest(`/menus/modifiers/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify({
            group_id: groupId,
            name: name.trim(),
            price,
            is_available: isAvailable,
          }),
        });
      } else {
        await apiRequest("/menus/modifiers", {
          method: "POST",
          body: JSON.stringify({
            group_id: groupId,
            name: name.trim(),
            price,
            is_available: isAvailable,
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

  const handleToggle = async (modId: string) => {
    await apiRequest(`/menus/modifiers/${modId}/toggle-availability`, { method: "PATCH" });
    setModifiers((prev) =>
      prev.map((m) => (m.id === modId ? { ...m, is_available: !m.is_available } : m))
    );
  };

  const handleDelete = async (mod: ItemModifier) => {
    if (!confirm(`Delete item modifier "${mod.name}"?`)) return;
    await apiRequest(`/menus/modifiers/${mod.id}`, { method: "DELETE" });
    await loadData();
  };

  const filtered = modifiers.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      (m.group_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (m.item_name || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Item Modifiers</h1>
          <p className="text-xs text-ink-muted mt-1">
            Individual add-on options, spice selections, and extra portion pricing across dishes.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add Item Modifier
        </button>
      </div>

      <div className="p-4 rounded-2xl bg-panel border border-line flex items-center justify-between gap-3 shadow-sm">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search modifiers, groups, or items..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink placeholder:text-ink-subtle"
          />
        </div>
        <div className="text-xs text-ink-muted font-semibold">{filtered.length} modifier(s)</div>
      </div>

      <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Modifier Name</th>
                <th className="py-3 px-4">Modifier Group</th>
                <th className="py-3 px-4">Menu Item</th>
                <th className="py-3 px-4">Add-on Price</th>
                <th className="py-3 px-4 text-center">Is Available</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-medium">
              {filtered.map((mod) => (
                <tr key={mod.id} className="hover:bg-row-hover transition">
                  <td className="py-3 px-4 font-bold text-ink">{mod.name}</td>
                  <td className="py-3 px-4 text-ink-3">{mod.group_name || "Group"}</td>
                  <td className="py-3 px-4 text-ink-muted">{mod.item_name || "Item"}</td>
                  <td className="py-3 px-4 font-mono font-bold text-ink">+₹{mod.price.toFixed(2)}</td>
                  <td className="py-3 px-4 text-center">
                    <input
                      type="checkbox"
                      aria-label={`Toggle availability for ${mod.name}`}
                      checked={mod.is_available}
                      onChange={() => handleToggle(mod.id)}
                      className="w-4 h-4 rounded accent-brand-600 cursor-pointer"
                    />
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <div className="inline-flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(mod)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold"
                      >
                        <Pencil className="w-3.5 h-3.5" /> Update
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(mod)}
                        aria-label={`Delete ${mod.name}`}
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
        title={editing ? `Update Modifier — ${editing.name}` : "Add Item Modifier"}
        maxWidthClass="max-w-md"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Modifier Name</label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g. Pure Cow Ghee Drizzle"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Modifier Group</label>
            <select
              required
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            >
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.item_name || "Item"})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3 items-end">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Add-on Price (₹)</label>
              <input
                type="number"
                step="0.01"
                min={0}
                required
                value={price}
                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>

            <label className="flex items-center gap-2 text-xs text-ink-3 pb-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isAvailable}
                onChange={(e) => setIsAvailable(e.target.checked)}
                className="w-4 h-4 rounded accent-brand-600"
              />
              <span>Is Available</span>
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
              {saving ? "Saving..." : "Save Modifier"}
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
}
