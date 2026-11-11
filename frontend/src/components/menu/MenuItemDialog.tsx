"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, ChevronUp, Copy, Plus, Trash2, Upload } from "lucide-react";
import { ModalDialog } from "@/components/ModalDialog";
import {
  BranchConfigRecord,
  BranchRecord,
  ComboComponentRecord,
  CuisineRecord,
  FOOD_TYPE_OPTIONS,
  FoodType,
  ItemVariant,
  KitchenStationRecord,
  MenuCategory,
  MenuItemRecord,
  MenuSummary,
  ORDER_CHANNEL_OPTIONS,
  SPICE_LEVEL_OPTIONS,
} from "./MenuTypes";
import { DISH_PHOTO_PRESETS, DietaryBadge, DishThumbnail, resolveFoodType } from "./VegBadge";
import { uploadMenuImage } from "./menuActions";

interface MenuItemDialogProps {
  open: boolean;
  onClose: () => void;
  editingItem: MenuItemRecord | null;
  menus: MenuSummary[];
  categories: MenuCategory[];
  cuisines?: CuisineRecord[];
  branches?: BranchRecord[];
  stations?: KitchenStationRecord[];
  allItems?: MenuItemRecord[];
  defaultMenuId?: string;
  onSave: (payload: Record<string, any>, editingId: string | null) => Promise<void>;
}

const PRESET_VARIANT_NAMES = ["Half", "Full", "Regular", "Large"];

export function MenuItemDialog({
  open,
  onClose,
  editingItem,
  menus,
  categories,
  cuisines = [],
  branches = [],
  stations = [],
  allItems = [],
  defaultMenuId,
  onSave,
}: MenuItemDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cuisineId, setCuisineId] = useState("");
  const [foodType, setFoodType] = useState<FoodType>("VEG");
  const [categoryId, setCategoryId] = useState("");
  const [menuId, setMenuId] = useState("");
  const [kitchenStationId, setKitchenStationId] = useState("");
  const [basePrice, setBasePrice] = useState<number>(220);
  const [costPrice, setCostPrice] = useState<number>(75);
  const [taxRate, setTaxRate] = useState<number>(5);
  const [prepTime, setPrepTime] = useState<number>(15);
  const [sku, setSku] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [isAvailable, setIsAvailable] = useState(true);
  const [showOnSite, setShowOnSite] = useState(true);
  const [allBranches, setAllBranches] = useState(true);
  const [orderChannels, setOrderChannels] = useState<string[]>([...ORDER_CHANNEL_OPTIONS]);
  const [spiceLevels, setSpiceLevels] = useState<string[]>([]);
  const [variants, setVariants] = useState<ItemVariant[]>([]);
  const [branchConfigs, setBranchConfigs] = useState<Record<string, BranchConfigRecord>>({});
  const [isCombo, setIsCombo] = useState(false);
  const [comboComponents, setComboComponents] = useState<ComboComponentRecord[]>([]);
  const [comboPickId, setComboPickId] = useState("");
  const [comboPickQty, setComboPickQty] = useState(1);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [copiedPreview, setCopiedPreview] = useState(false);
  const [saving, setSaving] = useState(false);

  const activeCategories = useMemo(
    () => categories.filter((c) => c.is_active !== false),
    [categories]
  );

  useEffect(() => {
    if (!open) return;
    setCopiedPreview(false);
    setShowUrlInput(false);

    const initBranchMap = (existing?: BranchConfigRecord[]) => {
      const next: Record<string, BranchConfigRecord> = {};
      branches.forEach((b) => {
        const found = existing?.find((x) => x.branch_id === b.id);
        next[b.id] = found
          ? { ...found }
          : {
              branch_id: b.id,
              branch_name: b.name,
              branch_price: null,
              is_available: true,
              show_on_customer_site: true,
            };
      });
      return next;
    };

    if (editingItem) {
      setName(editingItem.name);
      setDescription(editingItem.description || "");
      setCuisineId(editingItem.cuisine_id || "");
      setFoodType(resolveFoodType(editingItem.food_type, editingItem.is_veg));
      setCategoryId(editingItem.category_id);
      setMenuId(editingItem.menu_id || "");
      setKitchenStationId(editingItem.kitchen_station_id || "");
      setBasePrice(editingItem.base_price);
      setCostPrice(editingItem.cost_price || 0);
      setTaxRate(typeof editingItem.tax_rate === "number" ? editingItem.tax_rate : 5);
      setPrepTime(editingItem.preparation_time || 15);
      setSku(editingItem.sku || "");
      setImageUrl(editingItem.image_url || "");
      setIsAvailable(editingItem.is_available);
      setShowOnSite(editingItem.show_on_customer_site);
      setAllBranches(!editingItem.branch_id);
      setOrderChannels(
        editingItem.order_channels && editingItem.order_channels.length > 0
          ? editingItem.order_channels
          : [...ORDER_CHANNEL_OPTIONS]
      );
      setSpiceLevels(editingItem.spice_levels || []);
      setVariants(editingItem.variants || []);
      setBranchConfigs(initBranchMap(editingItem.branch_configs));
      setIsCombo(Boolean(editingItem.is_combo));
      setComboComponents(editingItem.combo_components || []);
      setShowAdvanced(
        Boolean(
          editingItem.is_combo ||
            (editingItem.variants && editingItem.variants.length > 0) ||
            (editingItem.branch_configs && editingItem.branch_configs.length > 0)
        )
      );
    } else {
      setName("");
      setDescription("");
      setCuisineId(cuisines[0]?.id || "");
      setFoodType("VEG");
      setCategoryId(activeCategories[0]?.id || categories[0]?.id || "");
      setMenuId(defaultMenuId || menus[0]?.id || "");
      setKitchenStationId(stations[0]?.id || "");
      setBasePrice(180);
      setCostPrice(60);
      setTaxRate(5);
      setPrepTime(15);
      setSku("");
      setImageUrl(DISH_PHOTO_PRESETS[4].url);
      setIsAvailable(true);
      setShowOnSite(true);
      setAllBranches(true);
      setOrderChannels([...ORDER_CHANNEL_OPTIONS]);
      setSpiceLevels(["Mild", "Medium"]);
      setVariants([]);
      setBranchConfigs(initBranchMap([]));
      setIsCombo(false);
      setComboComponents([]);
      setShowAdvanced(false);
    }

    const firstEligible = allItems.find((i) => !editingItem || i.id !== editingItem.id);
    setComboPickId(firstEligible?.id || "");
    setComboPickQty(1);
  }, [open, editingItem, defaultMenuId, menus, categories, activeCategories, cuisines, branches, stations, allItems]);

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingPhoto(true);
    try {
      const uploadedUrl = await uploadMenuImage(file);
      setImageUrl(uploadedUrl);
    } catch (err: any) {
      alert(err.message || "Could not upload photo");
    } finally {
      setUploadingPhoto(false);
      e.target.value = "";
    }
  };

  const toggleChannel = (ch: string) => {
    setOrderChannels((prev) =>
      prev.includes(ch) ? prev.filter((x) => x !== ch) : [...prev, ch]
    );
  };

  const toggleSpice = (sp: string) => {
    setSpiceLevels((prev) =>
      prev.includes(sp) ? prev.filter((x) => x !== sp) : [...prev, sp]
    );
  };

  const addVariant = (presetName = "") => {
    setVariants((prev) => [
      ...prev,
      {
        name: presetName || "Regular",
        price: Number(basePrice || 0),
        sku: null,
        is_available: true,
      },
    ]);
  };

  const updateVariant = (idx: number, patch: Partial<ItemVariant>) => {
    setVariants((prev) => prev.map((v, i) => (i === idx ? { ...v, ...patch } : v)));
  };

  const removeVariant = (idx: number) => {
    setVariants((prev) => prev.filter((_, i) => i !== idx));
  };

  const addComboComponent = () => {
    if (!comboPickId) return;
    const picked = allItems.find((i) => i.id === comboPickId);
    setComboComponents((prev) => {
      const existingIdx = prev.findIndex((c) => c.component_item_id === comboPickId);
      if (existingIdx >= 0) {
        return prev.map((c, idx) =>
          idx === existingIdx ? { ...c, quantity: c.quantity + Math.max(1, comboPickQty) } : c
        );
      }
      return [
        ...prev,
        {
          component_item_id: comboPickId,
          component_item_name: picked?.name || "Item",
          quantity: Math.max(1, comboPickQty),
        },
      ];
    });
  };

  const updateBranchConfig = (branchId: string, patch: Partial<BranchConfigRecord>) => {
    setBranchConfigs((prev) => ({
      ...prev,
      [branchId]: {
        ...(prev[branchId] || {
          branch_id: branchId,
          is_available: true,
          show_on_customer_site: true,
        }),
        ...patch,
      },
    }));
  };

  const selectedCuisineName = cuisines.find((c) => c.id === cuisineId)?.name || "Indian";
  const selectedCategoryName = categories.find((c) => c.id === categoryId)?.name || "Dish";
  const selectedFoodTypeMeta =
    FOOD_TYPE_OPTIONS.find((f) => f.value === foodType) || FOOD_TYPE_OPTIONS[0];

  const handleCopyPreview = async () => {
    const text = `${name.trim() || "New Dish"}\n${selectedCuisineName} · ${selectedCategoryName} · ${selectedFoodTypeMeta.shortLabel}\n₹${Number(basePrice || 0).toFixed(2)} (${taxRate}% GST)`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedPreview(true);
      setTimeout(() => setCopiedPreview(false), 1800);
    } catch {
      // Clipboard API unavailable
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryId) {
      alert("Please select a Dish Category before saving.");
      return;
    }
    setSaving(true);
    try {
      const cleanVariants = variants
        .filter((v) => v.name.trim().length > 0)
        .map((v) => ({
          name: v.name.trim(),
          price: Number(v.price) || 0,
          sku: v.sku || null,
          is_available: v.is_available,
        }));

      const cleanBranchConfigs = allBranches
        ? Object.values(branchConfigs).map((cfg) => ({
            branch_id: cfg.branch_id,
            branch_price:
              cfg.branch_price !== null && cfg.branch_price !== undefined && !Number.isNaN(Number(cfg.branch_price))
                ? Number(cfg.branch_price)
                : null,
            is_available: cfg.is_available,
            show_on_customer_site: cfg.show_on_customer_site,
          }))
        : [];

      await onSave(
        {
          name: name.trim(),
          description: description.trim() || null,
          cuisine_id: cuisineId || null,
          food_type: foodType,
          is_veg: foodType === "VEG" || foodType === "VEGAN",
          category_id: categoryId,
          menu_id: menuId || null,
          kitchen_station_id: kitchenStationId || null,
          base_price: basePrice,
          cost_price: costPrice,
          tax_rate: taxRate,
          preparation_time: prepTime,
          sku: sku.trim() || null,
          image_url: imageUrl.trim() || null,
          is_available: isAvailable,
          show_on_customer_site: showOnSite,
          all_branches: allBranches,
          order_channels: orderChannels.length > 0 ? orderChannels : ["DineIn"],
          spice_levels: spiceLevels,
          variants: cleanVariants,
          branch_configs: cleanBranchConfigs,
          is_combo: isCombo,
          combo_components: isCombo
            ? comboComponents.map((c) => ({
                component_item_id: c.component_item_id,
                quantity: c.quantity,
              }))
            : [],
        },
        editingItem?.id || null
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
      title={editingItem ? `Edit Dish — ${editingItem.name}` : "Add New Dish"}
      subtitle="Add a photo, set name, food type, cuisine, category & price in seconds."
      maxWidthClass="max-w-5xl"
    >
      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Main Clean Form */}
        <div className="lg:col-span-8 space-y-4">
          {/* 1. Dish Photo Picker */}
          <div className="p-3.5 rounded-xl bg-well border border-line space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <DishThumbnail imageUrl={imageUrl} name={name || "Dish"} className="w-16 h-16 rounded-xl" />
                <div>
                  <p className="text-xs font-bold text-ink">Dish Photo</p>
                  <p className="text-[11px] text-ink-muted">Upload your own photo or tap a quick gallery style below.</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <label className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold cursor-pointer transition">
                  <Upload className="w-3.5 h-3.5" />
                  <span>{uploadingPhoto ? "Uploading..." : "Upload Photo"}</span>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    onChange={handlePhotoUpload}
                    disabled={uploadingPhoto}
                    className="sr-only"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => setShowUrlInput((p) => !p)}
                  className="px-2.5 py-1.5 rounded-lg border border-line bg-panel hover:bg-control text-[11px] font-semibold text-ink-2"
                >
                  {showUrlInput ? "Hide URL" : "Paste URL"}
                </button>
              </div>
            </div>

            {showUrlInput && (
              <input
                type="text"
                placeholder="https://... or /images/dishes/..."
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                className="w-full px-3 py-1.5 bg-panel border border-input-border rounded-lg text-xs text-ink"
              />
            )}

            {/* Quick Indian Dish Photo Gallery Strip */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              {DISH_PHOTO_PRESETS.map((preset) => {
                const selected = imageUrl === preset.url;
                return (
                  <button
                    key={preset.url}
                    type="button"
                    onClick={() => setImageUrl(preset.url)}
                    className={`shrink-0 flex flex-col items-center gap-1 p-1 rounded-lg border transition ${
                      selected
                        ? "border-brand-600 bg-tint-brand"
                        : "border-transparent hover:bg-panel"
                    }`}
                  >
                    <img
                      src={preset.url}
                      alt={preset.label}
                      className="w-11 h-11 rounded-md object-cover border border-line"
                    />
                    <span className="text-[10px] font-medium text-ink-2 whitespace-nowrap">
                      {preset.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Essential Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-ink-2 mb-1">Dish Name</label>
              <input
                type="text"
                required
                autoFocus
                placeholder="e.g. Chicken 65"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink-2 mb-1">Price (₹)</label>
              <input
                type="number"
                step="0.01"
                min={0}
                required
                value={basePrice}
                onChange={(e) => setBasePrice(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink-2 mb-1.5">Food Type</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {FOOD_TYPE_OPTIONS.map((opt) => {
                const active = foodType === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setFoodType(opt.value)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-semibold transition ${
                      active
                        ? "bg-tint-brand border-brand-600 text-ink shadow-sm"
                        : "bg-well border-line hover:bg-control text-ink-3"
                    }`}
                  >
                    <DietaryBadge foodType={opt.value} />
                    <span className="truncate">{opt.shortLabel}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink-2 mb-1">Cuisine</label>
              <select
                value={cuisineId}
                onChange={(e) => setCuisineId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                <option value="">-- Select Cuisine --</option>
                {cuisines.map((cu) => (
                  <option key={cu.id} value={cu.id}>{cu.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink-2 mb-1">Dish Category</label>
              <select
                required
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                {(activeCategories.length > 0 ? activeCategories : categories).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.parent_name ? `${c.parent_name} › ${c.name}` : c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink-2 mb-1">Menu Time</label>
              <select
                value={menuId}
                onChange={(e) => setMenuId(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              >
                <option value="">All-Day / Unassigned</option>
                {menus.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
            <div className="sm:col-span-8">
              <label className="block text-xs font-semibold text-ink-2 mb-1">Short Description</label>
              <textarea
                rows={2}
                placeholder="Crisp boneless chicken tempered with curry leaves & garlic..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-xs text-ink"
              />
            </div>
            <div className="sm:col-span-4 space-y-2 pt-5 text-xs">
              <label className="flex items-center gap-2 text-ink-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAvailable}
                  onChange={(e) => setIsAvailable(e.target.checked)}
                  className="w-4 h-4 rounded accent-brand-600"
                />
                <span>In Stock (Available)</span>
              </label>
              <label className="flex items-center gap-2 text-ink-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showOnSite}
                  onChange={(e) => setShowOnSite(e.target.checked)}
                  className="w-4 h-4 rounded accent-brand-600"
                />
                <span>Show on Customer Site</span>
              </label>
            </div>
          </div>

          {/* 3. Progressive Disclosure Toggle for Advanced Options */}
          <div className="border border-line rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setShowAdvanced((p) => !p)}
              className="w-full px-4 py-2.5 bg-well hover:bg-control flex items-center justify-between text-xs font-bold text-ink transition"
            >
              <span>Optional: Portion Sizes, GST %, Kitchen KOT, Spice & Branch Pricing</span>
              {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showAdvanced && (
              <div className="p-4 space-y-4 bg-panel border-t border-line">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-ink-3 mb-1">KOT Station</label>
                    <select
                      value={kitchenStationId}
                      onChange={(e) => setKitchenStationId(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink"
                    >
                      <option value="">Default Kitchen</option>
                      {stations.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-3 mb-1">GST (%)</label>
                    <input
                      type="number"
                      step="0.5"
                      min={0}
                      max={28}
                      value={taxRate}
                      onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                      className="w-full px-2.5 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-3 mb-1">Food Cost (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      min={0}
                      value={costPrice}
                      onChange={(e) => setCostPrice(parseFloat(e.target.value) || 0)}
                      className="w-full px-2.5 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-3 mb-1">Prep Time (m)</label>
                    <input
                      type="number"
                      min={1}
                      value={prepTime}
                      onChange={(e) => setPrepTime(parseInt(e.target.value) || 15)}
                      className="w-full px-2.5 py-1.5 bg-well border border-input-border rounded-lg text-xs text-ink font-mono"
                    />
                  </div>
                </div>

                {/* Variants */}
                <div className="p-3 rounded-xl bg-well border border-line space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-bold text-ink">Portion Sizes</span>
                    <div className="flex flex-wrap gap-1.5">
                      {PRESET_VARIANT_NAMES.map((preset) => (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => addVariant(preset)}
                          className="px-2 py-1 rounded-md bg-panel hover:bg-control border border-line text-[11px] font-medium text-ink-2"
                        >
                          + {preset}
                        </button>
                      ))}
                    </div>
                  </div>
                  {variants.map((v, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Size"
                        value={v.name}
                        onChange={(e) => updateVariant(idx, { name: e.target.value })}
                        className="flex-1 px-2.5 py-1 bg-panel border border-input-border rounded-lg text-xs text-ink"
                      />
                      <input
                        type="number"
                        step="0.01"
                        min={0}
                        value={v.price}
                        onChange={(e) => updateVariant(idx, { price: parseFloat(e.target.value) || 0 })}
                        className="w-24 px-2.5 py-1 bg-panel border border-input-border rounded-lg text-xs font-mono text-ink"
                      />
                      <button
                        type="button"
                        onClick={() => removeVariant(idx)}
                        className="p-1 rounded-lg bg-tint-rose text-accent-rose"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Order Channels & Spice Levels */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-well border border-line">
                    <p className="text-xs font-bold text-ink mb-2">Order Channels</p>
                    <div className="flex flex-wrap gap-1.5">
                      {ORDER_CHANNEL_OPTIONS.map((ch) => (
                        <button
                          key={ch}
                          type="button"
                          onClick={() => toggleChannel(ch)}
                          className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
                            orderChannels.includes(ch)
                              ? "bg-brand-600 text-white border-brand-600"
                              : "bg-panel text-ink-3 border-line"
                          }`}
                        >
                          {ch}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-well border border-line">
                    <p className="text-xs font-bold text-ink mb-2">Spice Customisation</p>
                    <div className="flex flex-wrap gap-1.5">
                      {SPICE_LEVEL_OPTIONS.map((sp) => (
                        <button
                          key={sp}
                          type="button"
                          onClick={() => toggleSpice(sp)}
                          className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border transition ${
                            spiceLevels.includes(sp)
                              ? "bg-amber-600 text-white border-amber-600"
                              : "bg-panel text-ink-3 border-line"
                          }`}
                        >
                          {sp}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Branch Pricing Overrides */}
                <div className="p-3 rounded-xl bg-well border border-line space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-bold text-ink">Branch Availability & Price</span>
                    <div className="flex items-center gap-3 text-xs">
                      <label className="inline-flex items-center gap-1 cursor-pointer">
                        <input type="radio" checked={allBranches} onChange={() => setAllBranches(true)} className="accent-brand-600" />
                        <span>All branches</span>
                      </label>
                      <label className="inline-flex items-center gap-1 cursor-pointer">
                        <input type="radio" checked={!allBranches} onChange={() => setAllBranches(false)} className="accent-brand-600" />
                        <span>Current branch only</span>
                      </label>
                    </div>
                  </div>
                  {allBranches && branches.map((b) => {
                    const cfg = branchConfigs[b.id] || { branch_id: b.id, branch_price: null, is_available: true, show_on_customer_site: true };
                    return (
                      <div key={b.id} className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-panel border border-line text-xs">
                        <span className="font-medium text-ink">{b.name}</span>
                        <div className="flex items-center gap-3">
                          <input
                            type="number"
                            step="0.01"
                            min={0}
                            placeholder={`₹${basePrice}`}
                            value={cfg.branch_price ?? ""}
                            onChange={(e) =>
                              updateBranchConfig(b.id, {
                                branch_price: e.target.value === "" ? null : parseFloat(e.target.value),
                              })
                            }
                            className="w-24 px-2 py-1 bg-well border border-input-border rounded text-xs font-mono text-ink"
                          />
                          <label className="inline-flex items-center gap-1 text-[11px] text-ink-3">
                            <input
                              type="checkbox"
                              checked={cfg.is_available}
                              onChange={(e) => updateBranchConfig(b.id, { is_available: e.target.checked })}
                              className="accent-brand-600"
                            />
                            <span>In Stock</span>
                          </label>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Combo Meal */}
                <div className="p-3 rounded-xl bg-well border border-line space-y-2">
                  <label className="inline-flex items-center gap-2 text-xs font-bold text-ink cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isCombo}
                      onChange={(e) => setIsCombo(e.target.checked)}
                      className="w-4 h-4 rounded accent-brand-600"
                    />
                    <span>Bundle as a Combo Meal</span>
                  </label>
                  {isCombo && (
                    <div className="space-y-2 pt-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          value={comboPickId}
                          onChange={(e) => setComboPickId(e.target.value)}
                          className="flex-1 px-2.5 py-1 bg-panel border border-input-border rounded-lg text-xs text-ink"
                        >
                          <option value="">-- Select dish --</option>
                          {allItems.filter((it) => !editingItem || it.id !== editingItem.id).map((it) => (
                            <option key={it.id} value={it.id}>{it.name} (₹{it.base_price})</option>
                          ))}
                        </select>
                        <input
                          type="number"
                          min={1}
                          value={comboPickQty}
                          onChange={(e) => setComboPickQty(parseInt(e.target.value) || 1)}
                          className="w-16 px-2 py-1 bg-panel border border-input-border rounded-lg text-xs font-mono text-ink"
                        />
                        <button
                          type="button"
                          onClick={addComboComponent}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-brand-600 text-white text-xs font-semibold"
                        >
                          <Plus className="w-3.5 h-3.5" /> Add
                        </button>
                      </div>
                      {comboComponents.map((cc) => (
                        <div key={cc.component_item_id} className="flex items-center justify-between px-2.5 py-1 rounded-lg bg-panel border border-line text-xs">
                          <span className="text-ink font-medium">{cc.quantity}x {cc.component_item_name || cc.component_item_id}</span>
                          <button
                            type="button"
                            onClick={() => setComboComponents((prev) => prev.filter((x) => x.component_item_id !== cc.component_item_id))}
                            className="text-accent-rose text-[11px] font-semibold"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Sticky Photo Card Preview */}
        <div className="lg:col-span-4 space-y-4">
          <div className="sticky top-0 p-4 rounded-2xl bg-well border border-line space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted">Live Preview</span>
              <span className="px-2 py-0.5 rounded-full bg-tint-brand text-accent-brand text-[10px] font-semibold">
                {allBranches ? "All branches" : "Branch specific"}
              </span>
            </div>

            <div className="rounded-xl bg-panel border border-line shadow-sm overflow-hidden">
              <div className="relative h-36 bg-well">
                <DishThumbnail
                  imageUrl={imageUrl}
                  name={name || "Preview Dish"}
                  className="w-full h-full rounded-none border-0"
                />
                <div className="absolute top-2 left-2">
                  <DietaryBadge foodType={foodType} showLabel />
                </div>
              </div>

              <div className="p-3.5 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-bold text-sm text-ink leading-snug">
                    {name.trim() || "Chicken 65"}
                  </h4>
                  <span className="text-base font-extrabold text-ink font-mono">
                    ₹{Number(basePrice || 0).toFixed(basePrice % 1 === 0 ? 0 : 2)}
                  </span>
                </div>
                <p className="text-xs text-accent-brand font-medium">
                  {selectedCuisineName} · {selectedCategoryName} · {selectedFoodTypeMeta.shortLabel}
                </p>
                {description.trim() && (
                  <p className="text-[11px] text-ink-muted line-clamp-2">{description}</p>
                )}
                {variants.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {variants.map((v, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-well border border-line text-[10px] font-medium text-ink-2">
                        {v.name}: ₹{v.price}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={handleCopyPreview}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border border-line bg-panel hover:bg-control text-xs font-semibold text-ink-2 transition"
            >
              {copiedPreview ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Copied dish details!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy dish summary</span>
                </>
              )}
            </button>

            <div className="pt-2 border-t border-line space-y-2">
              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition disabled:opacity-50"
              >
                {saving ? "Saving..." : editingItem ? "Update Dish" : "Save Dish"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-full py-2 rounded-xl text-xs font-semibold text-ink-3 bg-control hover:bg-control-hover transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </form>
    </ModalDialog>
  );
}
