from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    address: Optional[str] = None
    tax_number: Optional[str] = None
    payment_terms: str = "Net 30 Days"

class SupplierResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: str
    address: Optional[str]
    tax_number: Optional[str]
    payment_terms: str

    class Config:
        from_attributes = True

class PurchaseOrderItemInput(BaseModel):
    inventory_item_id: str
    item_name: str
    quantity: float
    unit_price: float

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[PurchaseOrderItemInput]

class PurchaseOrderItemResponse(BaseModel):
    id: str
    inventory_item_id: str
    item_name: str
    quantity: float
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class PurchaseOrderResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    supplier_id: str
    po_number: str
    status: str
    total_amount: float
    expected_delivery_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    items: List[PurchaseOrderItemResponse] = []

    class Config:
        from_attributes = True

class GoodsReceiptCreate(BaseModel):
    po_id: str
    notes: Optional[str] = None
