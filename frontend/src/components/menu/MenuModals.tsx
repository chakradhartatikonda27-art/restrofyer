"use client";

import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp, Download, Upload } from "lucide-react";
import { ModalDialog } from "@/components/ModalDialog";
import {
  BranchRecord,
  MenuItemRecord,
  MenuSummary,
  TableRecord,
} from "./MenuTypes";

/* -------------------------------------------------------------------------
 * 1. Add / Update Menu Dialog (with Breakfast / Lunch / Dinner / AllDay scheduling)
 * ---------------------------------------------------------------------- */
const SCHEDULE_OPTIONS = ["AllDay", "Breakfast", "Lunch", "Dinner", "Custom"] as const;
const DAY_OPTIONS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const;

export function MenuFormDialog({
  open,
  onClose,
  editingMenu,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  editingMenu: MenuSummary | null;
  onSave: (
    payload: {
      name: string;
      description: string;
      schedule_type: string;
      available_from: string | null;
      available_to: string | null;
      active_days: string[];
    },
    editingId: string | null
  ) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scheduleType, setScheduleType] = useState("AllDay");
  const [availableFrom, setAvailableFrom] = useState("");
  const [availableTo, setAvailableTo] = useState("");
  const [activeDays, setActiveDays] = useState<string[]>([...DAY_OPTIONS]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName(editingMenu?.name || "");
    setDescription(editingMenu?.description || "");
    setScheduleType(editingMenu?.schedule_type || "AllDay");
    setAvailableFrom(editingMenu?.available_from || "");
    setAvailableTo(editingMenu?.available_to || "");
    setActiveDays(
      editingMenu?.active_days && editingMenu.active_days.length > 0
        ? editingMenu.active_days
        : [...DAY_OPTIONS]
    );
  }, [open, editingMenu]);

  const toggleDay = (d: string) => {
    setActiveDays((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(
        {
          name: name.trim(),
          description: description.trim(),
          schedule_type: scheduleType,
          available_from: scheduleType === "AllDay" ? null : availableFrom || null,
          available_to: scheduleType === "AllDay" ? null : availableTo || null,
          active_days: activeDays.length > 0 ? activeDays : [...DAY_OPTIONS],
        },
        editingMenu?.id || null
      );
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalDialog
      open={open}
      onClose={onClose}
      title={editingMenu ? `Update Menu — ${editingMenu.name}` : "Add Menu"}
      subtitle="Configure meal service schedule such as Breakfast, Lunch, Dinner, or All-Day."
      maxWidthClass="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-ink-3 mb-1">Menu Name</label>
          <input
            type="text"
            required
            autoFocus
            placeholder="e.g. Breakfast Menu"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Schedule Type</label>
            <select
              value={scheduleType}
              onChange={(e) => {
                const v = e.target.value;
                setScheduleType(v);
                if (v === "Breakfast") {
                  setAvailableFrom("07:00");
                  setAvailableTo("11:30");
                } else if (v === "Lunch") {
                  setAvailableFrom("12:00");
                  setAvailableTo("15:30");
                } else if (v === "Dinner") {
                  setAvailableFrom("18:30");
                  setAvailableTo("23:30");
                }
              }}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            >
              {SCHEDULE_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">From (HH:MM)</label>
            <input
              type="time"
              disabled={scheduleType === "AllDay"}
              value={availableFrom}
              onChange={(e) => setAvailableFrom(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink disabled:opacity-40"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">To (HH:MM)</label>
            <input
              type="time"
              disabled={scheduleType === "AllDay"}
              value={availableTo}
              onChange={(e) => setAvailableTo(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink disabled:opacity-40"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-ink-3 mb-1.5">Active Days</label>
          <div className="flex flex-wrap gap-1.5">
            {DAY_OPTIONS.map((d) => {
              const active = activeDays.includes(d);
              return (
                <button
                  key={d}
                  type="button"
                  onClick={() => toggleDay(d)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                    active
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-well text-ink-3 border-line"
                  }`}
                >
                  {d}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-ink-3 mb-1">Description (Optional)</label>
          <textarea
            rows={2}
            placeholder="Short summary shown to staff and QR diners..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
          />
        </div>
        <div className="flex justify-end gap-2 pt-2 border-t border-line">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition disabled:opacity-50"
          >
            {saving ? "Saving..." : editingMenu ? "Update Menu" : "Create Menu"}
          </button>
        </div>
      </form>
    </ModalDialog>
  );
}

/* -------------------------------------------------------------------------
 * 2. Copy Between Branches Dialog (supports copying Menus or Items)
 * ---------------------------------------------------------------------- */
export function CopyBetweenBranchesDialog({
  open,
  onClose,
  mode,
  branches,
  activeBranchId,
  menus,
  items,
  onCopy,
}: {
  open: boolean;
  onClose: () => void;
  mode: "menus" | "items";
  branches: BranchRecord[];
  activeBranchId: string;
  menus: MenuSummary[];
  items: MenuItemRecord[];
  onCopy: (targetBranchId: string, selectedIds: string[]) => Promise<void>;
}) {
  const otherBranches = branches.filter((b) => b.id !== activeBranchId);
  const [targetBranchId, setTargetBranchId] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTargetBranchId(otherBranches[0]?.id || "");
    if (mode === "menus") {
      setSelectedIds(menus.map((m) => m.id));
    } else {
      setSelectedIds(items.map((i) => i.id));
    }
  }, [open, mode, activeBranchId, menus, items]);

  const toggleId = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetBranchId || selectedIds.length === 0) return;
    setSubmitting(true);
    try {
      await onCopy(targetBranchId, selectedIds);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalDialog
      open={open}
      onClose={onClose}
      title={mode === "menus" ? "Copy Menus Between Branches" : "Copy Menu Items Between Branches"}
      subtitle="Duplicate pricing, categories, variants, and modifiers to another branch location."
      maxWidthClass="max-w-md"
    >
      {otherBranches.length === 0 ? (
        <div className="p-4 rounded-xl bg-tint-amber border border-tint-amber-border text-xs text-accent-amber">
          Add a second branch under <strong>Settings &amp; Staff</strong> to copy menus between locations.
        </div>
      ) : (
        <form onSubmit={handleConfirm} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ink-3 mb-1">Destination Branch</label>
            <select
              value={targetBranchId}
              onChange={(e) => setTargetBranchId(e.target.value)}
              className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
            >
              {otherBranches.map((b) => (
                <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5 max-h-56 overflow-y-auto p-2 rounded-xl bg-well border border-line">
            <div className="flex items-center justify-between text-[11px] font-bold text-ink-muted px-1 pb-1 border-b border-line">
              <span>{mode === "menus" ? "Select Menus" : "Select Items"} ({selectedIds.length})</span>
              <button
                type="button"
                onClick={() =>
                  setSelectedIds(
                    selectedIds.length === (mode === "menus" ? menus.length : items.length)
                      ? []
                      : (mode === "menus" ? menus.map((m) => m.id) : items.map((i) => i.id))
                  )
                }
                className="text-accent-brand hover:underline"
              >
                Toggle All
              </button>
            </div>
            {mode === "menus"
              ? menus.map((m) => (
                  <label key={m.id} className="flex items-center justify-between p-1.5 rounded-lg hover:bg-control cursor-pointer text-xs">
                    <span className="flex items-center gap-2 font-medium text-ink">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(m.id)}
                        onChange={() => toggleId(m.id)}
                        className="w-4 h-4 rounded accent-brand-600"
                      />
                      {m.name}
                    </span>
                    <span className="text-[11px] text-ink-muted">{m.item_count} item(s)</span>
                  </label>
                ))
              : items.map((i) => (
                  <label key={i.id} className="flex items-center justify-between p-1.5 rounded-lg hover:bg-control cursor-pointer text-xs">
                    <span className="flex items-center gap-2 font-medium text-ink">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(i.id)}
                        onChange={() => toggleId(i.id)}
                        className="w-4 h-4 rounded accent-brand-600"
                      />
                      {i.name}
                    </span>
                    <span className="text-[11px] text-ink-muted font-mono">₹{i.base_price.toFixed(2)}</span>
                  </label>
                ))}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || selectedIds.length === 0}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? "Copying..." : `Copy to Branch (${selectedIds.length})`}
            </button>
          </div>
        </form>
      )}
    </ModalDialog>
  );
}

/* -------------------------------------------------------------------------
 * 3. Assign Menu to Table Dialog
 * ---------------------------------------------------------------------- */
export function AssignMenuTableDialog({
  open,
  onClose,
  menus,
  tables,
  defaultMenuId,
  onAssign,
}: {
  open: boolean;
  onClose: () => void;
  menus: MenuSummary[];
  tables: TableRecord[];
  defaultMenuId?: string;
  onAssign: (menuId: string, tableIds: string[]) => Promise<void>;
}) {
  const [menuId, setMenuId] = useState("");
  const [selectedTableIds, setSelectedTableIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    const initialMenuId = defaultMenuId || menus[0]?.id || "";
    setMenuId(initialMenuId);
    const matching = menus.find((m) => m.id === initialMenuId);
    setSelectedTableIds(matching?.assigned_table_ids || []);
  }, [open, defaultMenuId, menus]);

  const handleMenuChange = (nextMenuId: string) => {
    setMenuId(nextMenuId);
    const matching = menus.find((m) => m.id === nextMenuId);
    setSelectedTableIds(matching?.assigned_table_ids || []);
  };

  const toggleTable = (tableId: string) => {
    setSelectedTableIds((prev) =>
      prev.includes(tableId) ? prev.filter((id) => id !== tableId) : [...prev, tableId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!menuId) return;
    setSaving(true);
    try {
      await onAssign(menuId, selectedTableIds);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalDialog
      open={open}
      onClose={onClose}
      title="Assign Menu to Table"
      subtitle="Bind a menu so QR table ordering automatically opens that menu for guests seated there."
      maxWidthClass="max-w-md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-ink-3 mb-1">Select Menu</label>
          <select
            value={menuId}
            onChange={(e) => handleMenuChange(e.target.value)}
            className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
          >
            {menus.map((m) => (
              <option key={m.id} value={m.id}>{m.name} ({m.item_count} items)</option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5 max-h-56 overflow-y-auto p-2 rounded-xl bg-well border border-line">
          {tables.length === 0 ? (
            <div className="p-4 text-center text-xs text-ink-subtle">
              No dining tables configured in this branch yet.
            </div>
          ) : (
            tables.map((t) => {
              const checked = selectedTableIds.includes(t.id);
              return (
                <label
                  key={t.id}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-control cursor-pointer text-xs"
                >
                  <span className="flex items-center gap-2.5 font-semibold text-ink">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleTable(t.id)}
                      className="w-4 h-4 rounded accent-brand-600"
                    />
                    <span>{t.table_number} {t.name ? `— ${t.name}` : ""}</span>
                  </span>
                  <span className="text-[11px] text-ink-muted">{t.capacity} seats</span>
                </label>
              );
            })
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-line">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || !menuId}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Table Assignment"}
          </button>
        </div>
      </form>
    </ModalDialog>
  );
}

/* -------------------------------------------------------------------------
 * 4. Organize Items Dialog (Reorder display_order cleanly)
 * ---------------------------------------------------------------------- */
export function OrganizeItemsDialog({
  open,
  onClose,
  items,
  onSaveOrder,
}: {
  open: boolean;
  onClose: () => void;
  items: MenuItemRecord[];
  onSaveOrder: (ordered: { id: string; display_order: number }[]) => Promise<void>;
}) {
  const [ordered, setOrdered] = useState<MenuItemRecord[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) setOrdered([...items]);
  }, [open, items]);

  const move = (idx: number, dir: -1 | 1) => {
    const target = idx + dir;
    if (target < 0 || target >= ordered.length) return;
    const copy = [...ordered];
    const [removed] = copy.splice(idx, 1);
    copy.splice(target, 0, removed);
    setOrdered(copy);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSaveOrder(ordered.map((it, idx) => ({ id: it.id, display_order: idx + 1 })));
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalDialog
      open={open}
      onClose={onClose}
      title="Organize Menu Items Order"
      subtitle="Move dishes up or down to control display order across POS and online storefronts."
      maxWidthClass="max-w-lg"
    >
      <div className="space-y-1.5 max-h-72 overflow-y-auto p-2 rounded-xl bg-well border border-line">
        {ordered.length === 0 ? (
          <div className="p-6 text-center text-xs text-ink-subtle">No items to organize in this view.</div>
        ) : (
          ordered.map((it, idx) => (
            <div
              key={it.id}
              className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-panel border border-line text-xs"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="w-6 h-6 rounded-md bg-control text-ink-muted font-mono font-bold flex items-center justify-center text-[11px] shrink-0">
                  {idx + 1}
                </span>
                <div className="truncate">
                  <div className="font-bold text-ink truncate">{it.name}</div>
                  <div className="text-[10px] text-ink-muted">₹{it.base_price.toFixed(2)} • {it.category_name || "General"}</div>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  disabled={idx === 0}
                  onClick={() => move(idx, -1)}
                  aria-label={`Move ${it.name} up`}
                  className="p-1.5 rounded-lg bg-control hover:bg-control-hover text-ink-3 disabled:opacity-30"
                >
                  <ArrowUp className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={idx === ordered.length - 1}
                  onClick={() => move(idx, 1)}
                  aria-label={`Move ${it.name} down`}
                  className="p-1.5 rounded-lg bg-control hover:bg-control-hover text-ink-3 disabled:opacity-30"
                >
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="flex justify-end gap-2 pt-2 border-t border-line">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={saving || ordered.length === 0}
          onClick={handleSave}
          className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
        >
          {saving ? "Saving Order..." : "Save Display Order"}
        </button>
      </div>
    </ModalDialog>
  );
}

/* -------------------------------------------------------------------------
 * 5. Bulk Upload CSV Dialog
 * ---------------------------------------------------------------------- */
const SAMPLE_CSV = `name,description,base_price,cuisine_name,food_type,category_name,menu_name,tax_rate,is_available,show_on_customer_site
Chicken 65,Spicy boneless fried chicken tempered with curry leaves,220,South Indian,NON_VEG,Starters,Dinner Menu,5,true,true
Paneer Butter Masala,Cottage cheese cubes in rich makhani gravy,240,North Indian,VEG,Curries & Gravies,Dinner Menu,5,true,true
Egg Pakoda,Crispy besan-crusted spiced egg fritters,140,Other Regional,EGG,Starters,All-Day Menu,5,true,true`;

interface ParsedCsvRow {
  name: string;
  description: string;
  base_price: number;
  cuisine_name?: string;
  food_type: string;
  category_name: string;
  menu_name: string;
  tax_rate: number;
  is_veg: boolean;
  is_available: boolean;
  show_on_customer_site: boolean;
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  result.push(current.trim());
  return result;
}

export function BulkUploadDialog({
  open,
  onClose,
  defaultMenuId,
  onUpload,
}: {
  open: boolean;
  onClose: () => void;
  defaultMenuId?: string;
  onUpload: (rows: ParsedCsvRow[], menuId?: string) => Promise<void>;
}) {
  const [csvText, setCsvText] = useState(SAMPLE_CSV);
  const [submitting, setSubmitting] = useState(false);

  const lines = csvText
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  const headerCols = (lines[0] ? parseCsvLine(lines[0]) : []).map((h) => h.toLowerCase());
  const hasCuisineCol = headerCols.includes("cuisine_name");

  const parsedRows: ParsedCsvRow[] = lines
    .slice(1)
    .map((line) => {
      const cols = parseCsvLine(line);
      if (hasCuisineCol) {
        const ftype = (cols[4] || "VEG").toUpperCase();
        return {
          name: cols[0] || "",
          description: cols[1] || "",
          base_price: parseFloat(cols[2]) || 0,
          cuisine_name: cols[3] || undefined,
          food_type: ["VEG", "NON_VEG", "EGG", "VEGAN"].includes(ftype) ? ftype : "VEG",
          category_name: cols[5] || "Main Course",
          menu_name: cols[6] || "",
          tax_rate: parseFloat(cols[7]) || 5,
          is_veg: ftype === "VEG" || ftype === "VEGAN",
          is_available: (cols[8] || "true").toLowerCase() !== "false",
          show_on_customer_site: (cols[9] || "true").toLowerCase() !== "false",
        };
      }
      const isVegFlag = (cols[5] || "true").toLowerCase() !== "false";
      return {
        name: cols[0] || "",
        description: cols[1] || "",
        base_price: parseFloat(cols[2]) || 0,
        food_type: isVegFlag ? "VEG" : "NON_VEG",
        category_name: cols[3] || "Main Course",
        menu_name: cols[4] || "",
        tax_rate: 5,
        is_veg: isVegFlag,
        is_available: (cols[6] || "true").toLowerCase() !== "false",
        show_on_customer_site: (cols[7] || "true").toLowerCase() !== "false",
      };
    })
    .filter((r) => r.name.length > 0);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setCsvText(text);
  };

  const handleDownloadSample = () => {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "menu_items_sample_template.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleConfirm = async () => {
    if (parsedRows.length === 0) return;
    setSubmitting(true);
    try {
      await onUpload(parsedRows, defaultMenuId);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalDialog
      open={open}
      onClose={onClose}
      title="Bulk Upload Menu Items (CSV)"
      subtitle="Upload a CSV spreadsheet or edit rows directly. Missing menus and categories are created automatically."
      maxWidthClass="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-well border border-input-border text-xs font-semibold text-ink cursor-pointer hover:bg-control">
            <Upload className="w-3.5 h-3.5 text-accent-brand" />
            <span>Choose .csv File</span>
            <input type="file" accept=".csv,text/csv" onChange={handleFileChange} className="sr-only" />
          </label>
          <button
            type="button"
            onClick={handleDownloadSample}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-control hover:bg-control-hover text-xs font-semibold text-ink-2"
          >
            <Download className="w-3.5 h-3.5" /> Download Sample CSV Template
          </button>
        </div>

        <textarea
          rows={5}
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
          className="w-full p-3 bg-well border border-input-border rounded-xl text-[11px] font-mono text-ink"
        />

        <div className="max-h-40 overflow-y-auto rounded-xl border border-line bg-well">
          <table className="w-full text-left text-[11px]">
            <thead className="bg-control text-ink-muted uppercase border-b border-line">
              <tr>
                <th className="py-2 px-3">Item Name</th>
                <th className="py-2 px-3">Cuisine</th>
                <th className="py-2 px-3">Food Type</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3">Price</th>
                <th className="py-2 px-3">Menu</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {parsedRows.map((row, idx) => (
                <tr key={idx}>
                  <td className="py-1.5 px-3 font-bold text-ink">{row.name}</td>
                  <td className="py-1.5 px-3 text-ink-3">{row.cuisine_name || "—"}</td>
                  <td className="py-1.5 px-3 text-ink-3">{row.food_type}</td>
                  <td className="py-1.5 px-3 text-ink-3">{row.category_name}</td>
                  <td className="py-1.5 px-3 font-mono text-ink-3">₹{row.base_price.toFixed(2)}</td>
                  <td className="py-1.5 px-3 text-ink-3">{row.menu_name || "Active Menu"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-line">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-control hover:bg-control-hover text-ink-3"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={submitting || parsedRows.length === 0}
            onClick={handleConfirm}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Uploading..." : `Import ${parsedRows.length} Item(s)`}
          </button>
        </div>
      </div>
    </ModalDialog>
  );
}
