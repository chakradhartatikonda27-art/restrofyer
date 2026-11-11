from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal


FoodTypeLiteral = Literal["VEG", "NON_VEG", "EGG", "VEGAN"]


class CuisineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CuisineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CuisineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    item_count: int = 0


class ItemModifierCreate(BaseModel):
    name: str
    price: float = 0.0
    is_available: bool = True


class ItemModifierStandaloneCreate(BaseModel):
    group_id: str
    name: str
    price: float = 0.0
    is_available: bool = True


class ItemModifierUpdate(BaseModel):
    group_id: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None


class ItemModifierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    name: str
    price: float
    is_available: bool


class ItemModifierGroupCreate(BaseModel):
    name: str
    min_selection: int = 0
    max_selection: int = 5
    modifiers: List[ItemModifierCreate] = []


class ModifierGroupStandaloneCreate(BaseModel):
    item_id: str
    name: str
    min_selection: int = 0
    max_selection: int = 5
    modifiers: List[ItemModifierCreate] = []


class ModifierGroupUpdate(BaseModel):
    item_id: Optional[str] = None
    name: Optional[str] = None
    min_selection: Optional[int] = None
    max_selection: Optional[int] = None


class ItemModifierGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    name: str
    min_selection: int
    max_selection: int
    modifiers: List[ItemModifierResponse] = []


class ItemVariantCreate(BaseModel):
    name: str
    price: float
    sku: Optional[str] = None
    is_available: bool = True


class ItemVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: float
    sku: Optional[str] = None
    is_available: bool


class BranchConfigInput(BaseModel):
    branch_id: str
    branch_price: Optional[float] = None
    is_available: bool = True
    show_on_customer_site: bool = True


class BranchConfigResponse(BaseModel):
    branch_id: str
    branch_name: Optional[str] = None
    branch_price: Optional[float] = None
    is_available: bool = True
    show_on_customer_site: bool = True


class ComboComponentInput(BaseModel):
    component_item_id: str
    quantity: int = 1


class ComboComponentResponse(BaseModel):
    component_item_id: str
    component_item_name: Optional[str] = None
    quantity: int = 1


class MenuItemCreate(BaseModel):
    menu_id: Optional[str] = None
    branch_id: Optional[str] = None
    all_branches: Optional[bool] = None
    cuisine_id: Optional[str] = None
    category_id: str
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    base_price: float
    cost_price: float = 0.0
    tax_rate: float = 5.0
    preparation_time: int = 15
    display_order: int = 0
    is_available: bool = True
    show_on_customer_site: bool = True
    food_type: Optional[FoodTypeLiteral] = None
    is_veg: bool = True
    calories: Optional[int] = None
    kitchen_station_id: Optional[str] = None
    order_channels: List[str] = Field(default_factory=lambda: ["DineIn", "Takeaway", "Delivery", "QR"])
    spice_levels: List[str] = []
    is_combo: bool = False
    variants: List[ItemVariantCreate] = []
    modifier_groups: List[ItemModifierGroupCreate] = []
    branch_configs: List[BranchConfigInput] = []
    combo_components: List[ComboComponentInput] = []


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    menu_id: Optional[str] = None
    branch_id: Optional[str] = None
    all_branches: Optional[bool] = None
    cuisine_id: Optional[str] = None
    category_id: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    base_price: Optional[float] = None
    cost_price: Optional[float] = None
    tax_rate: Optional[float] = None
    preparation_time: Optional[int] = None
    display_order: Optional[int] = None
    is_available: Optional[bool] = None
    show_on_customer_site: Optional[bool] = None
    food_type: Optional[FoodTypeLiteral] = None
    is_veg: Optional[bool] = None
    calories: Optional[int] = None
    kitchen_station_id: Optional[str] = None
    order_channels: Optional[List[str]] = None
    spice_levels: Optional[List[str]] = None
    is_combo: Optional[bool] = None
    variants: Optional[List[ItemVariantCreate]] = None
    branch_configs: Optional[List[BranchConfigInput]] = None
    combo_components: Optional[List[ComboComponentInput]] = None


class MenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    menu_id: Optional[str] = None
    branch_id: Optional[str] = None
    all_branches: Optional[bool] = None
    cuisine_id: Optional[str] = None
    cuisine_name: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None
    parent_category_id: Optional[str] = None
    menu_name: Optional[str] = None
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    base_price: float
    effective_price: float
    cost_price: float
    tax_rate: float
    preparation_time: int
    display_order: int = 0
    is_available: bool
    show_on_customer_site: bool = True
    food_type: str = "VEG"
    is_veg: bool
    calories: Optional[int] = None
    kitchen_station_id: Optional[str] = None
    kitchen_station_name: Optional[str] = None
    order_channels: List[str] = ["DineIn", "Takeaway", "Delivery", "QR"]
    spice_levels: List[str] = []
    is_combo: bool = False
    variants: List[ItemVariantResponse] = []
    modifier_groups: List[ItemModifierGroupResponse] = []
    branch_configs: List[BranchConfigResponse] = []
    combo_components: List[ComboComponentResponse] = []


class MenuCategoryCreate(BaseModel):
    menu_id: Optional[str] = None
    branch_id: Optional[str] = None
    parent_id: Optional[str] = None
    name: str
    display_order: int = 0
    icon: Optional[str] = None
    is_active: bool = True


class MenuCategoryUpdate(BaseModel):
    menu_id: Optional[str] = None
    parent_id: Optional[str] = None
    name: Optional[str] = None
    display_order: Optional[int] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class MenuCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    menu_id: Optional[str] = None
    branch_id: Optional[str] = None
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    name: str
    display_order: int
    icon: Optional[str] = None
    is_active: bool
    item_count: int = 0
    items: List[MenuItemResponse] = []


class MenuCreate(BaseModel):
    name: str
    description: Optional[str] = None
    branch_id: Optional[str] = None
    schedule_type: str = "AllDay"
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    active_days: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    display_order: int = 0
    is_active: bool = True


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    active_days: Optional[List[str]] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class MenuSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    schedule_type: str = "AllDay"
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    active_days: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    display_order: int = 0
    is_active: bool = True
    item_count: int = 0
    assigned_table_ids: List[str] = []


class MenuResponse(MenuSummaryResponse):
    categories: List[MenuCategoryResponse] = []


class CopyMenusRequest(BaseModel):
    target_branch_id: str
    menu_ids: List[str]


class CopyItemsRequest(BaseModel):
    target_branch_id: str
    target_menu_id: Optional[str] = None
    item_ids: List[str]


class AssignMenuTablesRequest(BaseModel):
    table_ids: List[str]


class ReorderItemEntry(BaseModel):
    id: str
    display_order: int
    menu_id: Optional[str] = None
    category_id: Optional[str] = None


class ReorderItemsRequest(BaseModel):
    items: List[ReorderItemEntry]


class BulkUploadItemRow(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    cost_price: float = 0.0
    cuisine_name: Optional[str] = None
    food_type: FoodTypeLiteral = "VEG"
    category_name: str = "General"
    menu_name: Optional[str] = None
    is_veg: Optional[bool] = None
    is_available: bool = True
    show_on_customer_site: bool = True
    preparation_time: int = 15
    tax_rate: float = 5.0
    sku: Optional[str] = None


class BulkUploadItemsRequest(BaseModel):
    default_menu_id: Optional[str] = None
    items: List[BulkUploadItemRow]


class TemplateApplyRequest(BaseModel):
    cuisines: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    include_sample_dishes: bool = False
    create_scheduled_menus: bool = True
