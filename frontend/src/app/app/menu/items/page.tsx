"use client";

import { useEffect, useState } from "react";
import {
  ArrowDownUp,
  ChevronDown,
  Copy,
  Download,
  LayoutGrid,
  List,
  MoreHorizontal,
  Plus,
  Search,
  Upload,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { getActiveBranch } from "@/lib/auth";
import {
  BranchRecord,
  CuisineRecord,
  FOOD_TYPE_OPTIONS,
  KitchenStationRecord,
  MenuCategory,
  MenuItemRecord,
  MenuSummary,
} from "@/components/menu/MenuTypes";
import { DietaryBadge, resolveFoodType } from "@/components/menu/VegBadge";
import { DishPhotoGrid } from "@/components/menu/DishPhotoGrid";
import { MenuItemTable } from "@/components/menu/MenuItemTable";
import { MenuItemDialog } from "@/components/menu/MenuItemDialog";
import {
  BulkUploadDialog,
  CopyBetweenBranchesDialog,
  OrganizeItemsDialog,
} from "@/components/menu/MenuModals";
import {
  deleteMenuItemRecord,
  exportMenuItemsCsv,
  saveMenuItemRecord,
  toggleItemAvailabilityRecord,
  toggleItemCustomerSiteRecord,
} from "@/components/menu/menuActions";

export default function AllMenuItemsPage() {
  const [items, setItems] = useState<MenuItemRecord[]>([]);
  const [cuisines, setCuisines] = useState<CuisineRecord[]>([]);
  const [menus, setMenus] = useState<MenuSummary[]>([]);
  const [categories, setCategories] = useState<MenuCategory[]>([]);
  const [branches, setBranches] = useState<BranchRecord[]>([]);
  const [stations, setStations] = useState<KitchenStationRecord[]>([]);
  const [activeBranchId, setActiveBranchId] = useState("");
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("all");
  const [foodTypeFilter, setFoodTypeFilter] = useState("all");
  const [menuFilter, setMenuFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [viewMode, setViewMode] = useState<"cards" | "list">("cards");
  const [toolsOpen, setToolsOpen] = useState(false);

  const [itemDialogOpen, setItemDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItemRecord | null>(null);
  const [copyOpen, setCopyOpen] = useState(false);
  const [organizeOpen, setOrganizeOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);

  useEffect(() => {
    setActiveBranchId(getActiveBranch() || "");
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [itemsRes, cuisinesRes, menusRes, catsRes, branchesRes, stationsRes] = await Promise.all([
        apiRequest("/menus/items"),
        apiRequest("/menus/cuisines"),
        apiRequest("/menus"),
        apiRequest("/menus/categories"),
        apiRequest("/branches"),
        apiRequest("/kitchens/stations").catch(() => []),
      ]);
      setItems(itemsRes);
      setCuisines(cuisinesRes);
      setMenus(menusRes);
      setCategories(catsRes);
      setBranches(branchesRes);
      setStations(Array.isArray(stationsRes) ? stationsRes : []);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredItems = items.filter((item) => {
    if (search && !item.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (cuisineFilter !== "all" && item.cuisine_id !== cuisineFilter) return false;
    if (foodTypeFilter !== "all" && resolveFoodType(item.food_type, item.is_veg) !== foodTypeFilter) {
      return false;
    }
    if (menuFilter !== "all" && item.menu_id !== menuFilter) return false;
    if (categoryFilter !== "all") {
      if (item.category_id !== categoryFilter && item.parent_category_id !== categoryFilter) {
        return false;
      }
    }
    return true;
  });

  const handleToggleAvailability = async (id: string) => {
    await toggleItemAvailabilityRecord(id);
    setItems((prev) => prev.map((i) => (i.id === id ? { ...i, is_available: !i.is_available } : i)));
  };

  const handleToggleCustomerSite = async (id: string) => {
    await toggleItemCustomerSiteRecord(id);
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, show_on_customer_site: !i.show_on_customer_site } : i))
    );
  };

  const handleDelete = async (item: MenuItemRecord) => {
    if (!confirm(`Delete "${item.name}"?`)) return;
    await deleteMenuItemRecord(item.id);
    await loadData();
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Clean Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Indian Dish Catalog</h1>
          <p className="text-xs text-ink-muted mt-0.5">
            Browse, photograph, and manage every Indian dish across cuisines, food types, and categories.
          </p>
        </div>

        <div className="flex items-center gap-2 relative">
          <div className="relative">
            <button
              type="button"
              onClick={() => setToolsOpen((p) => !p)}
              className="px-3.5 py-2 rounded-xl border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
            >
              <MoreHorizontal className="w-4 h-4" />
              <span>More Tools</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {toolsOpen && (
              <>
                <div className="fixed inset-0 z-20" onClick={() => setToolsOpen(false)} />
                <div className="absolute right-0 mt-1.5 w-52 rounded-xl bg-panel border border-line shadow-xl z-30 py-1.5 text-xs">
                  <button
                    type="button"
                    onClick={() => { setToolsOpen(false); setCopyOpen(true); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Copy className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Copy to Branch</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setToolsOpen(false); setOrganizeOpen(true); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <ArrowDownUp className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Organize Order</span>
                  </button>
                  <div className="my-1 border-t border-line" />
                  <button
                    type="button"
                    onClick={() => {
                      setToolsOpen(false);
                      exportMenuItemsCsv({
                        menuId: menuFilter !== "all" ? menuFilter : undefined,
                        cuisineId: cuisineFilter !== "all" ? cuisineFilter : undefined,
                        foodType: foodTypeFilter !== "all" ? foodTypeFilter : undefined,
                        categoryId: categoryFilter !== "all" ? categoryFilter : undefined,
                      });
                    }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Download className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Export Dishes (CSV)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setToolsOpen(false); setBulkOpen(true); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Upload className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Bulk Upload CSV</span>
                  </button>
                </div>
              </>
            )}
          </div>

          <button
            type="button"
            onClick={() => {
              setEditingItem(null);
              setItemDialogOpen(true);
            }}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Dish
          </button>
        </div>
      </div>

      {/* Unified Filter Bar with Veg/Non-Veg Pills & View Switch */}
      <div className="p-3 rounded-2xl bg-panel border border-line flex flex-wrap items-center gap-2.5 shadow-sm">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="w-3.5 h-3.5 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search dishes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-well border border-input-border rounded-xl text-xs text-ink placeholder:text-ink-subtle"
          />
        </div>

        <select
          value={cuisineFilter}
          onChange={(e) => setCuisineFilter(e.target.value)}
          className="px-3 py-1.5 bg-well border border-input-border rounded-xl text-xs font-medium text-ink"
        >
          <option value="all">All Cuisines</option>
          {cuisines.map((cu) => (
            <option key={cu.id} value={cu.id}>{cu.name}</option>
          ))}
        </select>

        <div className="flex flex-wrap items-center gap-1">
          <button
            type="button"
            onClick={() => setFoodTypeFilter("all")}
            className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
              foodTypeFilter === "all"
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-well text-ink-3 border-line hover:bg-control"
            }`}
          >
            All
          </button>
          {FOOD_TYPE_OPTIONS.map((ft) => {
            const active = foodTypeFilter === ft.value;
            return (
              <button
                key={ft.value}
                type="button"
                onClick={() => setFoodTypeFilter(active ? "all" : ft.value)}
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
                  active
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-well text-ink-2 border-line hover:bg-control"
                }`}
              >
                <DietaryBadge foodType={ft.value} />
                <span>{ft.shortLabel}</span>
              </button>
            );
          })}
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-1.5 bg-well border border-input-border rounded-xl text-xs font-medium text-ink"
        >
          <option value="all">All Categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.parent_name ? `${c.parent_name} › ${c.name}` : c.name}
            </option>
          ))}
        </select>

        <select
          value={menuFilter}
          onChange={(e) => setMenuFilter(e.target.value)}
          className="px-3 py-1.5 bg-well border border-input-border rounded-xl text-xs font-medium text-ink"
        >
          <option value="all">All Menus</option>
          {menus.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>

        <div className="ml-auto flex items-center gap-2.5">
          <span className="text-[11px] font-semibold text-ink-muted">
            {filteredItems.length} dish(es)
          </span>
          <div className="inline-flex rounded-xl bg-well border border-line p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("cards")}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                viewMode === "cards"
                  ? "bg-panel text-ink shadow-sm"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Cards</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                viewMode === "list"
                  ? "bg-panel text-ink shadow-sm"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>List</span>
            </button>
          </div>
        </div>
      </div>

      {viewMode === "cards" ? (
        <DishPhotoGrid
          items={filteredItems}
          onToggleAvailability={handleToggleAvailability}
          onToggleCustomerSite={handleToggleCustomerSite}
          onEdit={(item) => {
            setEditingItem(item);
            setItemDialogOpen(true);
          }}
          onDelete={handleDelete}
        />
      ) : (
        <MenuItemTable
          items={filteredItems}
          onToggleAvailability={handleToggleAvailability}
          onToggleCustomerSite={handleToggleCustomerSite}
          onEdit={(item) => {
            setEditingItem(item);
            setItemDialogOpen(true);
          }}
          onDelete={handleDelete}
        />
      )}

      <MenuItemDialog
        open={itemDialogOpen}
        onClose={() => setItemDialogOpen(false)}
        editingItem={editingItem}
        menus={menus}
        cuisines={cuisines}
        categories={categories}
        branches={branches}
        stations={stations}
        allItems={items}
        onSave={async (payload, id) => {
          await saveMenuItemRecord(payload, id);
          await loadData();
        }}
      />

      <CopyBetweenBranchesDialog
        open={copyOpen}
        onClose={() => setCopyOpen(false)}
        mode="items"
        branches={branches}
        activeBranchId={activeBranchId}
        menus={menus}
        items={filteredItems}
        onCopy={async (targetBranchId, ids) => {
          await apiRequest("/menus/items/copy-between-branches", {
            method: "POST",
            body: JSON.stringify({ target_branch_id: targetBranchId, item_ids: ids }),
          });
        }}
      />

      <OrganizeItemsDialog
        open={organizeOpen}
        onClose={() => setOrganizeOpen(false)}
        items={filteredItems}
        onSaveOrder={async (ordered) => {
          await apiRequest("/menus/items/reorder", {
            method: "PUT",
            body: JSON.stringify({ items: ordered }),
          });
          await loadData();
        }}
      />

      <BulkUploadDialog
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        onUpload={async (rows) => {
          await apiRequest("/menus/items/bulk-upload", {
            method: "POST",
            body: JSON.stringify({ items: rows }),
          });
          await loadData();
        }}
      />
    </div>
  );
}
