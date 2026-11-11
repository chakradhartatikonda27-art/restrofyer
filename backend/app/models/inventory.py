from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin, BranchMixin

class InventoryCategory(BaseModel, TenantMixin):
    __tablename__ = "inventory_categories"
    
    name = Column(String(100), nullable=False) # e.g. "Dairy", "Meat & Poultry", "Produce", "Dry Goods", "Beverages"
    
    items = relationship("InventoryItem", back_populates="category")

class InventoryItem(BaseModel, TenantMixin):
    __tablename__ = "inventory_items"
    
    category_id = Column(String(36), ForeignKey("inventory_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False) # e.g. "Mozzarella Cheese", "San Marzano Tomatoes", "Arborio Rice"
    sku = Column(String(50), nullable=True)
    uom = Column(String(20), default="kg") # kg, g, l, ml, pcs
    current_stock = Column(Numeric(12, 3), default=0.000, nullable=False)
    minimum_stock = Column(Numeric(12, 3), default=5.000, nullable=False) # Reorder threshold
    cost_per_unit = Column(Numeric(10, 2), default=0.00, nullable=False)
    storage_location = Column(String(100), default="Main Walk-in Cooler")
    
    category = relationship("InventoryCategory", back_populates="items")
    stock_movements = relationship("StockMovement", back_populates="item", cascade="all, delete-orphan")
    recipe_items = relationship("RecipeItem", back_populates="inventory_item")

class StockMovement(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "stock_movements"
    
    inventory_item_id = Column(String(36), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(String(50), nullable=False) # PURCHASE_RECEIPT, SALES_CONSUMPTION, TRANSFER, WASTAGE, ADJUSTMENT
    quantity = Column(Numeric(12, 3), nullable=False) # Positive or negative
    unit_cost = Column(Numeric(10, 2), default=0.00)
    reference_id = Column(String(100), nullable=True) # Order ID or PO ID
    notes = Column(String(255), nullable=True)
    created_by = Column(String(100), nullable=True)
    
    item = relationship("InventoryItem", back_populates="stock_movements")

class Recipe(BaseModel, TenantMixin):
    __tablename__ = "recipes"
    
    menu_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), unique=True, nullable=False)
    yield_portions = Column(Integer, default=1)
    preparation_loss_percent = Column(Numeric(5, 2), default=0.00)
    instructions = Column(Text, nullable=True)
    
    menu_item = relationship("MenuItem", back_populates="recipe")
    items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")

class RecipeItem(BaseModel):
    __tablename__ = "recipe_items"
    
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(String(36), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False) # Amount used per portion
    uom = Column(String(20), default="g")
    
    recipe = relationship("Recipe", back_populates="items")
    inventory_item = relationship("InventoryItem", back_populates="recipe_items")
