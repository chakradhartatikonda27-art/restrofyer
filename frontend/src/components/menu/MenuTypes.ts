export type FoodType = "VEG" | "NON_VEG" | "EGG" | "VEGAN";

export const FOOD_TYPE_OPTIONS: { value: FoodType; label: string; shortLabel: string }[] = [
  { value: "VEG", label: "Vegetarian", shortLabel: "Veg" },
  { value: "NON_VEG", label: "Non-Vegetarian", shortLabel: "Non-Veg" },
  { value: "EGG", label: "Egg", shortLabel: "Egg" },
  { value: "VEGAN", label: "Vegan", shortLabel: "Vegan" },
];

export const ORDER_CHANNEL_OPTIONS = ["DineIn", "Takeaway", "Delivery", "QR"] as const;
export const SPICE_LEVEL_OPTIONS = ["Mild", "Medium", "Spicy", "Extra Hot"] as const;

export interface CuisineRecord {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  display_order: number;
  is_active: boolean;
  item_count: number;
}

export interface MenuSummary {
  id: string;
  tenant_id: string;
  branch_id?: string | null;
  name: string;
  description?: string | null;
  schedule_type: string;
  available_from?: string | null;
  available_to?: string | null;
  active_days: string[];
  display_order: number;
  is_active: boolean;
  item_count: number;
  assigned_table_ids: string[];
}

export interface ItemModifier {
  id: string;
  group_id?: string | null;
  group_name?: string | null;
  item_id?: string | null;
  item_name?: string | null;
  name: string;
  price: number;
  is_available: boolean;
}

export interface ModifierGroup {
  id: string;
  item_id?: string | null;
  item_name?: string | null;
  name: string;
  min_selection: number;
  max_selection: number;
  modifiers: ItemModifier[];
}

export interface ItemVariant {
  id?: string;
  name: string;
  price: number;
  sku?: string | null;
  is_available: boolean;
}

export interface BranchConfigRecord {
  branch_id: string;
  branch_name?: string | null;
  branch_price?: number | null;
  is_available: boolean;
  show_on_customer_site: boolean;
}

export interface ComboComponentRecord {
  component_item_id: string;
  component_item_name?: string | null;
  quantity: number;
}

export interface KitchenStationRecord {
  id: string;
  name: string;
  kitchen_id?: string | null;
}

export interface MenuItemRecord {
  id: string;
  tenant_id: string;
  menu_id?: string | null;
  branch_id?: string | null;
  cuisine_id?: string | null;
  cuisine_name?: string | null;
  category_id: string;
  category_name?: string | null;
  parent_category_id?: string | null;
  menu_name?: string | null;
  name: string;
  sku?: string | null;
  description?: string | null;
  image_url?: string | null;
  base_price: number;
  effective_price: number;
  cost_price: number;
  tax_rate: number;
  preparation_time: number;
  display_order: number;
  is_available: boolean;
  show_on_customer_site: boolean;
  food_type: FoodType;
  is_veg: boolean;
  calories?: number | null;
  kitchen_station_id?: string | null;
  kitchen_station_name?: string | null;
  order_channels: string[];
  spice_levels: string[];
  is_combo: boolean;
  variants: ItemVariant[];
  modifier_groups: ModifierGroup[];
  branch_configs: BranchConfigRecord[];
  combo_components: ComboComponentRecord[];
}

export interface MenuCategory {
  id: string;
  tenant_id: string;
  menu_id?: string | null;
  branch_id?: string | null;
  parent_id?: string | null;
  parent_name?: string | null;
  name: string;
  display_order: number;
  icon?: string | null;
  is_active: boolean;
  item_count: number;
}

export interface BranchRecord {
  id: string;
  name: string;
  code: string;
}

export interface TableRecord {
  id: string;
  table_number: string;
  name?: string | null;
  capacity: number;
  status: string;
  assigned_menu_id?: string | null;
}
