from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Cuisine(BaseModel, TenantMixin):
    __tablename__ = "cuisines"

    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    items = relationship("MenuItem", back_populates="cuisine")


class Menu(BaseModel, TenantMixin):
    __tablename__ = "menus"

    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    schedule_type = Column(String(40), default="AllDay", nullable=False)  # AllDay, Breakfast, Lunch, Dinner, Custom
    available_from = Column(String(10), nullable=True)  # e.g. "07:00"
    available_to = Column(String(10), nullable=True)    # e.g. "11:30"
    active_days = Column(JSON, default=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    categories = relationship("MenuCategory", back_populates="menu", cascade="all, delete-orphan")
    items = relationship("MenuItem", back_populates="menu")


class MenuCategory(BaseModel, TenantMixin):
    __tablename__ = "menu_categories"

    menu_id = Column(String(36), ForeignKey("menus.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True)
    parent_id = Column(String(36), ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    menu = relationship("Menu", back_populates="categories")
    parent = relationship("MenuCategory", remote_side="MenuCategory.id", backref="subcategories")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")


class MenuItem(BaseModel, TenantMixin):
    __tablename__ = "menu_items"

    menu_id = Column(String(36), ForeignKey("menus.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True)
    cuisine_id = Column(String(36), ForeignKey("cuisines.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(String(36), ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), default=0.00)  # For COGS / food cost analysis
    tax_rate = Column(Numeric(5, 2), default=5.00)  # GST percentage per item
    preparation_time = Column(Integer, default=15)  # In minutes
    display_order = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    show_on_customer_site = Column(Boolean, default=True, nullable=False)
    food_type = Column(String(20), default="VEG", nullable=False)  # VEG, NON_VEG, EGG, VEGAN
    is_veg = Column(Boolean, default=True)  # Synced helper for backwards compatibility
    calories = Column(Integer, nullable=True)
    kitchen_station_id = Column(String(36), ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    order_channels = Column(JSON, default=lambda: ["DineIn", "Takeaway", "Delivery", "QR"])
    spice_levels = Column(JSON, default=list)  # e.g. ["Mild", "Medium", "Spicy"]
    is_combo = Column(Boolean, default=False, nullable=False)

    # Relationships
    cuisine = relationship("Cuisine", back_populates="items")
    menu = relationship("Menu", back_populates="items")
    category = relationship("MenuCategory", back_populates="items")
    variants = relationship("ItemVariant", back_populates="item", cascade="all, delete-orphan")
    modifier_groups = relationship("ItemModifierGroup", back_populates="item", cascade="all, delete-orphan")
    branch_configs = relationship("MenuItemBranchConfig", back_populates="item", cascade="all, delete-orphan")
    combo_components = relationship(
        "ComboMealItem",
        foreign_keys="ComboMealItem.combo_item_id",
        back_populates="combo_item",
        cascade="all, delete-orphan",
    )
    recipe = relationship("Recipe", back_populates="menu_item", uselist=False, cascade="all, delete-orphan")


class MenuItemBranchConfig(BaseModel, TenantMixin):
    __tablename__ = "menu_item_branch_configs"

    menu_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    branch_price = Column(Numeric(10, 2), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    show_on_customer_site = Column(Boolean, default=True, nullable=False)

    item = relationship("MenuItem", back_populates="branch_configs")


class ComboMealItem(BaseModel, TenantMixin):
    __tablename__ = "combo_meal_items"

    combo_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    component_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    combo_item = relationship("MenuItem", foreign_keys=[combo_item_id], back_populates="combo_components")
    component_item = relationship("MenuItem", foreign_keys=[component_item_id])


class ItemVariant(BaseModel, TenantMixin):
    __tablename__ = "item_variants"

    item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g. "Half", "Full", "Regular", "Large"
    price = Column(Numeric(10, 2), nullable=False)
    sku = Column(String(100), nullable=True)
    is_available = Column(Boolean, default=True)

    item = relationship("MenuItem", back_populates="variants")


class ItemModifierGroup(BaseModel, TenantMixin):
    __tablename__ = "item_modifier_groups"

    item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g. "Add Toppings", "Spice Level"
    min_selection = Column(Integer, default=0)
    max_selection = Column(Integer, default=5)

    item = relationship("MenuItem", back_populates="modifier_groups")
    modifiers = relationship("ItemModifier", back_populates="group", cascade="all, delete-orphan")


class ItemModifier(BaseModel, TenantMixin):
    __tablename__ = "item_modifiers"

    group_id = Column(String(36), ForeignKey("item_modifier_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g. "Extra Cheese", "Mild Spice"
    price = Column(Numeric(10, 2), default=0.00)
    is_available = Column(Boolean, default=True)

    group = relationship("ItemModifierGroup", back_populates="modifiers")
