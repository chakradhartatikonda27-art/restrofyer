from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class InventoryItemCreate(BaseModel):
    category_id: Optional[str] = None
    name: str
    sku: Optional[str] = None
    uom: str = "kg"
    current_stock: float = 0.0
    minimum_stock: float = 5.0
    cost_per_unit: float = 0.0
    storage_location: str = "Main Walk-in Cooler"

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    sku: Optional[str] = None
    uom: Optional[str] = None
    minimum_stock: Optional[float] = None
    cost_per_unit: Optional[float] = None
    storage_location: Optional[str] = None

class InventoryItemResponse(BaseModel):
    id: str
    tenant_id: str
    category_id: Optional[str]
    name: str
    sku: Optional[str]
    uom: str
    current_stock: float
    minimum_stock: float
    cost_per_unit: float
    storage_location: str
    is_low_stock: Optional[bool] = False

    class Config:
        from_attributes = True

class StockMovementCreate(BaseModel):
    inventory_item_id: str
    movement_type: str # PURCHASE_RECEIPT, SALES_CONSUMPTION, TRANSFER, WASTAGE, ADJUSTMENT
    quantity: float
    unit_cost: float = 0.0
    reference_id: Optional[str] = None
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    inventory_item_id: str
    movement_type: str
    quantity: float
    unit_cost: float
    reference_id: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class RecipeItemInput(BaseModel):
    inventory_item_id: str
    quantity: float
    uom: str = "g"

class RecipeCreate(BaseModel):
    menu_item_id: str
    yield_portions: int = 1
    preparation_loss_percent: float = 0.0
    instructions: Optional[str] = None
    items: List[RecipeItemInput] = []

class RecipeResponse(BaseModel):
    id: str
    menu_item_id: str
    yield_portions: int
    preparation_loss_percent: float
    instructions: Optional[str]
    items: List[dict] = []

    class Config:
        from_attributes = True
