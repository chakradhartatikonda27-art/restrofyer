"use client";

import { useEffect, useState } from "react";
import {
  ArrowDownUp,
  ChevronDown,
  Clock,
  Copy,
  Download,
  LayoutGrid,
  List,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Table2,
  Trash2,
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
  TableRecord,
} from "@/components/menu/MenuTypes";
import { DietaryBadge, resolveFoodType } from "@/components/menu/VegBadge";
import { DishPhotoGrid } from "@/components/menu/DishPhotoGrid";
import { MenuItemTable } from "@/components/menu/MenuItemTable";
import { MenuItemDialog } from "@/components/menu/MenuItemDialog";
import {
  AssignMenuTableDialog,
  BulkUploadDialog,
  CopyBetweenBranchesDialog,
  MenuFormDialog,
  OrganizeItemsDialog,
} from "@/components/menu/MenuModals";
import {
  deleteMenuItemRecord,
  exportMenuItemsCsv,
  saveMenuItemRecord,
  toggleItemAvailabilityRecord,
  toggleItemCustomerSiteRecord,
} from "@/components/menu/menuActions";

export default function MenusDashboardPage() {
  const [menus, setMenus] = useState<MenuSummary[]>([]);
  const [selectedMenuId, setSelectedMenuId] = useState<string>("ALL");
  const [items, setItems] = useState<MenuItemRecord[]>([]);
  const [cuisines, setCuisines] = useState<CuisineRecord[]>([]);
  const [categories, setCategories] = useState<MenuCategory[]>([]);
  const [branches, setBranches] = useState<BranchRecord[]>([]);
  const [stations, setStations] = useState<KitchenStationRecord[]>([]);
  const [tables, setTables] = useState<TableRecord[]>([]);
  const [activeBranchId, setActiveBranchId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [applyingTemplate, setApplyingTemplate] = useState(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [actionsMenuOpen, setActionsMenuOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"cards" | "list">("cards");

  // Unified 3D Filters
  const [itemSearch, setItemSearch] = useState("");
  const [filterCuisineId, setFilterCuisineId] = useState("all");
  const [filterFoodType, setFilterFoodType] = useState<string>("all");
  const [filterCategoryId, setFilterCategoryId] = useState("all");
  const [filterAvailable, setFilterAvailable] = useState<"all" | "yes" | "no">("all");

  // Modals
  const [menuDialogOpen, setMenuDialogOpen] = useState(false);
  const [editingMenu, setEditingMenu] = useState<MenuSummary | null>(null);

  const [itemDialogOpen, setItemDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItemRecord | null>(null);

  const [copyMode, setCopyMode] = useState<"menus" | "items" | null>(null);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [organizeModalOpen, setOrganizeModalOpen] = useState(false);
  const [bulkModalOpen, setBulkModalOpen] = useState(false);

  useEffect(() => {
    setActiveBranchId(getActiveBranch() || "");
    loadAll();
  }, []);

  const flashBanner = (msg: string) => {
    setBannerMessage(msg);
    setTimeout(() => setBannerMessage(null), 4000);
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      const [menusRes, cuisinesRes, catsRes, itemsRes, branchesRes, tablesRes, stationsRes] = await Promise.all([
        apiRequest("/menus"),
        apiRequest("/menus/cuisines"),
        apiRequest("/menus/categories"),
        apiRequest("/menus/items"),
        apiRequest("/branches"),
        apiRequest("/tables"),
        apiRequest("/kitchens/stations").catch(() => []),
      ]);
      setMenus(menusRes);
      setCuisines(cuisinesRes);
      setCategories(catsRes);
      setItems(itemsRes);
      setBranches(branchesRes);
      setTables(tablesRes);
      setStations(Array.isArray(stationsRes) ? stationsRes : []);

      setSelectedMenuId((prev) =>
        prev === "ALL" || (prev && menusRes.some((m: MenuSummary) => m.id === prev))
          ? prev
          : "ALL"
      );
    } catch (err) {
      console.error("Failed loading menus workspace:", err);
    } finally {
      setLoading(false);
    }
  };

  const selectedMenu = selectedMenuId === "ALL" ? null : menus.find((m) => m.id === selectedMenuId) || null;
  const menuScopedItems = selectedMenu ? items.filter((i) => i.menu_id === selectedMenu.id) : items;

  const filteredItems = menuScopedItems.filter((item) => {
    if (
      itemSearch &&
      !item.name.toLowerCase().includes(itemSearch.toLowerCase()) &&
      !(item.description || "").toLowerCase().includes(itemSearch.toLowerCase())
    ) {
      return false;
    }
    if (filterCuisineId !== "all" && item.cuisine_id !== filterCuisineId) return false;
    if (filterFoodType !== "all" && resolveFoodType(item.food_type, item.is_veg) !== filterFoodType) {
      return false;
    }
    if (filterCategoryId !== "all") {
      if (item.category_id !== filterCategoryId && item.parent_category_id !== filterCategoryId) {
        return false;
      }
    }
    if (filterAvailable === "yes" && !item.is_available) return false;
    if (filterAvailable === "no" && item.is_available) return false;
    return true;
  });

  const handleSaveMenu = async (
    payload: {
      name: string;
      description: string;
      schedule_type: string;
      available_from: string | null;
      available_to: string | null;
      active_days: string[];
    },
    editingId: string | null
  ) => {
    if (editingId) {
      await apiRequest(`/menus/${editingId}`, {
        method: "PUT",
        body: JSON.stringify({
          name: payload.name,
          description: payload.description || null,
          schedule_type: payload.schedule_type,
          available_from: payload.available_from,
          available_to: payload.available_to,
          active_days: payload.active_days,
        }),
      });
      flashBanner(`Updated menu "${payload.name}".`);
    } else {
      const created = await apiRequest("/menus", {
        method: "POST",
        body: JSON.stringify({
          name: payload.name,
          description: payload.description || null,
          schedule_type: payload.schedule_type,
          available_from: payload.available_from,
          available_to: payload.available_to,
          active_days: payload.active_days,
          display_order: menus.length + 1,
        }),
      });
      setSelectedMenuId(created.id);
      flashBanner(`Created menu "${payload.name}".`);
    }
    await loadAll();
  };

  const handleDeleteMenu = async (menu: MenuSummary) => {
    if (!confirm(`Delete menu "${menu.name}"? Dishes inside it will stay in your catalog.`)) {
      return;
    }
    try {
      await apiRequest(`/menus/${menu.id}`, { method: "DELETE" });
      setSelectedMenuId("ALL");
      flashBanner(`Deleted menu "${menu.name}".`);
      await loadAll();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleApplyDefaultTemplate = async () => {
    setActionsMenuOpen(false);
    setApplyingTemplate(true);
    try {
      const res = await apiRequest("/menus/templates/apply-indian-default", {
        method: "POST",
        body: JSON.stringify({
          include_sample_dishes: true,
          create_scheduled_menus: true,
        }),
      });
      await loadAll();
      flashBanner(
        `Applied Indian Catalog: +${res.created_cuisines} cuisines, +${res.created_categories} categories, +${res.created_items} dishes.`
      );
    } catch (err: any) {
      alert(err.message);
    } finally {
      setApplyingTemplate(false);
    }
  };

  const handleSaveItem = async (payload: Record<string, any>, editingId: string | null) => {
    await saveMenuItemRecord(payload, editingId);
    flashBanner(editingId ? `Updated "${payload.name}".` : `Added "${payload.name}".`);
    await loadAll();
  };

  const handleDeleteItem = async (item: MenuItemRecord) => {
    if (!confirm(`Delete "${item.name}"?`)) return;
    try {
      await deleteMenuItemRecord(item.id);
      flashBanner(`Deleted "${item.name}".`);
      await loadAll();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleAvailability = async (itemId: string) => {
    try {
      await toggleItemAvailabilityRecord(itemId);
      setItems((prev) =>
        prev.map((i) => (i.id === itemId ? { ...i, is_available: !i.is_available } : i))
      );
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleCustomerSite = async (itemId: string) => {
    try {
      await toggleItemCustomerSiteRecord(itemId);
      setItems((prev) =>
        prev.map((i) =>
          i.id === itemId ? { ...i, show_on_customer_site: !i.show_on_customer_site } : i
        )
      );
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCopyBetweenBranches = async (targetBranchId: string, selectedIds: string[]) => {
    if (copyMode === "menus") {
      const res = await apiRequest("/menus/copy-between-branches", {
        method: "POST",
        body: JSON.stringify({ target_branch_id: targetBranchId, menu_ids: selectedIds }),
      });
      flashBanner(res.message);
    } else if (copyMode === "items") {
      const res = await apiRequest("/menus/items/copy-between-branches", {
        method: "POST",
        body: JSON.stringify({ target_branch_id: targetBranchId, item_ids: selectedIds }),
      });
      flashBanner(res.message);
    }
  };

  const handleAssignMenuToTables = async (menuId: string, tableIds: string[]) => {
    const res = await apiRequest(`/menus/${menuId}/assign-tables`, {
      method: "POST",
      body: JSON.stringify({ table_ids: tableIds }),
    });
    flashBanner(res.message);
    await loadAll();
  };

  const handleSaveOrder = async (ordered: { id: string; display_order: number }[]) => {
    await apiRequest("/menus/items/reorder", {
      method: "PUT",
      body: JSON.stringify({ items: ordered }),
    });
    flashBanner("Saved display order.");
    await loadAll();
  };

  const handleBulkUpload = async (rows: any[], menuId?: string) => {
    const res = await apiRequest("/menus/items/bulk-upload", {
      method: "POST",
      body: JSON.stringify({ default_menu_id: menuId || null, items: rows }),
    });
    flashBanner(res.message);
    await loadAll();
  };

  const handleExportCsv = async () => {
    setActionsMenuOpen(false);
    try {
      await exportMenuItemsCsv({
        menuId: selectedMenu?.id,
        cuisineId: filterCuisineId !== "all" ? filterCuisineId : undefined,
        foodType: filterFoodType !== "all" ? filterFoodType : undefined,
        categoryId: filterCategoryId !== "all" ? filterCategoryId : undefined,
      });
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Clean Header with Primary CTAs & Compact Tools Menu */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-ink tracking-tight">Indian Menus & Dishes</h1>
          <p className="text-xs text-ink-muted mt-0.5">
            Filter independently by Cuisine, Food Type, and Dish Category across branches.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 relative">
          {bannerMessage && (
            <span className="px-3 py-1.5 rounded-xl bg-tint-emerald border border-tint-emerald-border text-accent-emerald text-xs font-bold">
              {bannerMessage}
            </span>
          )}

          {/* Overflow Actions Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActionsMenuOpen((p) => !p)}
              className="px-3.5 py-2 rounded-xl border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
            >
              <MoreHorizontal className="w-4 h-4" />
              <span>More Tools</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {actionsMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setActionsMenuOpen(false)}
                />
                <div className="absolute right-0 mt-1.5 w-56 rounded-xl bg-panel border border-line shadow-xl z-30 py-1.5 text-xs">
                  <button
                    type="button"
                    disabled={applyingTemplate}
                    onClick={handleApplyDefaultTemplate}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink font-medium"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-accent-brand" />
                    <span>{applyingTemplate ? "Applying Template..." : "Load Indian Template"}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActionsMenuOpen(false); setAssignModalOpen(true); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Table2 className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Assign Menu to Tables</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActionsMenuOpen(false); setCopyMode("items"); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Copy className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Copy Dishes to Branch</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActionsMenuOpen(false); setCopyMode("menus"); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Copy className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Copy Menus to Branch</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActionsMenuOpen(false); setOrganizeModalOpen(true); }}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <ArrowDownUp className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Organize Dish Order</span>
                  </button>
                  <div className="my-1 border-t border-line" />
                  <button
                    type="button"
                    onClick={handleExportCsv}
                    className="w-full px-3.5 py-2 text-left hover:bg-well flex items-center gap-2.5 text-ink"
                  >
                    <Download className="w-3.5 h-3.5 text-ink-muted" />
                    <span>Export Dishes (CSV)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActionsMenuOpen(false); setBulkModalOpen(true); }}
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
              setEditingMenu(null);
              setMenuDialogOpen(true);
            }}
            className="px-3.5 py-2 rounded-xl border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Menu</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEditingItem(null);
              setItemDialogOpen(true);
            }}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-md shadow-brand-500/20 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Add Dish</span>
          </button>
        </div>
      </div>

      {/* Compact Scheduled Menu Pill Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            type="button"
            onClick={() => setSelectedMenuId("ALL")}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition border ${
              selectedMenuId === "ALL"
                ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                : "bg-panel text-ink-2 border-line hover:bg-well"
            }`}
          >
            All Menus ({items.length})
          </button>
          {menus.map((menu) => {
            const isSelected = selectedMenu?.id === menu.id;
            const timeTag =
              menu.available_from && menu.available_to
                ? `${menu.available_from}–${menu.available_to}`
                : "";
            return (
              <button
                key={menu.id}
                type="button"
                onClick={() => setSelectedMenuId(menu.id)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition border ${
                  isSelected
                    ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                    : "bg-panel text-ink-2 border-line hover:bg-well"
                }`}
              >
                <span>{menu.name}</span>
                <span className={`text-[11px] ${isSelected ? "text-white/85" : "text-ink-muted"}`}>
                  ({menu.item_count})
                </span>
                {timeTag && (
                  <span className={`hidden sm:inline-flex items-center gap-0.5 text-[10px] ${isSelected ? "text-white/85" : "text-ink-subtle"}`}>
                    <Clock className="w-3 h-3" /> {timeTag}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {selectedMenu && (
          <div className="inline-flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => {
                setEditingMenu(selectedMenu);
                setMenuDialogOpen(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-line bg-panel hover:bg-control text-ink-2 text-[11px] font-semibold"
            >
              <Pencil className="w-3 h-3" /> Edit Menu
            </button>
            <button
              type="button"
              onClick={() => handleDeleteMenu(selectedMenu)}
              aria-label={`Delete ${selectedMenu.name}`}
              className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Single Unified 3-Dimensional Filter Bar */}
      <div className="p-3 rounded-2xl bg-panel border border-line flex flex-wrap items-center gap-2.5 shadow-sm">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="w-3.5 h-3.5 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search dishes..."
            value={itemSearch}
            onChange={(e) => setItemSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-well border border-input-border rounded-xl text-xs text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <select
          value={filterCuisineId}
          onChange={(e) => setFilterCuisineId(e.target.value)}
          aria-label="Filter by Cuisine"
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
            onClick={() => setFilterFoodType("all")}
            className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
              filterFoodType === "all"
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-well text-ink-3 border-line hover:bg-control"
            }`}
          >
            All
          </button>
          {FOOD_TYPE_OPTIONS.map((ft) => {
            const active = filterFoodType === ft.value;
            return (
              <button
                key={ft.value}
                type="button"
                onClick={() => setFilterFoodType(active ? "all" : ft.value)}
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
          value={filterCategoryId}
          onChange={(e) => setFilterCategoryId(e.target.value)}
          aria-label="Filter by Dish Category"
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
          value={filterAvailable}
          onChange={(e) => setFilterAvailable(e.target.value as any)}
          aria-label="Filter by Stock Availability"
          className="px-3 py-1.5 bg-well border border-input-border rounded-xl text-xs font-medium text-ink"
        >
          <option value="all">All Stock</option>
          <option value="yes">In Stock</option>
          <option value="no">Out of Stock</option>
        </select>

        <div className="ml-auto flex items-center gap-2.5">
          <span className="text-[11px] font-semibold text-ink-muted">
            {loading ? "Loading..." : `${filteredItems.length} dish(es)`}
          </span>
          <div className="inline-flex rounded-xl bg-well border border-line p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("cards")}
              title="Photo Grid View"
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
              title="Compact List View"
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

      {/* Photo Grid or Compact Table */}
      {viewMode === "cards" ? (
        <DishPhotoGrid
          items={filteredItems}
          onToggleAvailability={handleToggleAvailability}
          onToggleCustomerSite={handleToggleCustomerSite}
          onEdit={(item) => {
            setEditingItem(item);
            setItemDialogOpen(true);
          }}
          onDelete={handleDeleteItem}
          emptyMessage={
            selectedMenu
              ? `No dishes in "${selectedMenu.name}" match the active filters.`
              : "No dishes match the active filters."
          }
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
          onDelete={handleDeleteItem}
          emptyMessage={
            selectedMenu
              ? `No dishes in "${selectedMenu.name}" match the active filters.`
              : "No dishes match the active filters."
          }
        />
      )}

      {/* Dialogs */}
      <MenuFormDialog
        open={menuDialogOpen}
        onClose={() => setMenuDialogOpen(false)}
        editingMenu={editingMenu}
        onSave={handleSaveMenu}
      />

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
        defaultMenuId={selectedMenu?.id}
        onSave={handleSaveItem}
      />

      <CopyBetweenBranchesDialog
        open={copyMode !== null}
        onClose={() => setCopyMode(null)}
        mode={copyMode || "menus"}
        branches={branches}
        activeBranchId={activeBranchId}
        menus={menus}
        items={filteredItems}
        onCopy={handleCopyBetweenBranches}
      />

      <AssignMenuTableDialog
        open={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        menus={menus}
        tables={tables}
        defaultMenuId={selectedMenu?.id}
        onAssign={handleAssignMenuToTables}
      />

      <OrganizeItemsDialog
        open={organizeModalOpen}
        onClose={() => setOrganizeModalOpen(false)}
        items={menuScopedItems}
        onSaveOrder={handleSaveOrder}
      />

      <BulkUploadDialog
        open={bulkModalOpen}
        onClose={() => setBulkModalOpen(false)}
        defaultMenuId={selectedMenu?.id}
        onUpload={handleBulkUpload}
      />
    </div>
  );
}
