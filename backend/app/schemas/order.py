from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class OrderModifierInput(BaseModel):
    name: str
    price: float

class OrderItemCreate(BaseModel):
    menu_item_id: str
    quantity: int = Field(..., gt=0)
    variant_id: Optional[str] = None
    modifiers: List[OrderModifierInput] = []
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    order_type: str = "DineIn" # DineIn, Takeaway, Delivery, Online, QR
    table_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    discount_amount: float = 0.0
    discount_reason: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    menu_item_id: str
    item_name: str
    unit_price: float
    cost_price: float
    quantity: int
    subtotal: float
    tax_rate: float
    variant_name: Optional[str]
    modifiers: List[Dict[str, Any]] = []
    notes: Optional[str]

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    amount: float
    payment_method: str = "Cash" # Cash, Card, UPI, Split
    payment_reference: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    order_id: str
    amount: float
    payment_method: str
    payment_reference: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    order_id: str
    invoice_number: str
    subtotal: float
    discount: float
    tax: float
    service_charge: float
    total_amount: float
    paid_amount: float
    status: str
    created_at: datetime
    payments: List[PaymentResponse] = []

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    order_number: str
    order_type: str
    status: str
    table_id: Optional[str]
    table_number: Optional[str]
    customer_id: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    subtotal: float
    discount_amount: float
    discount_reason: Optional[str]
    tax_amount: float
    service_charge: float
    total_amount: float
    cashier_name: Optional[str]
    waiter_name: Optional[str]
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse] = []
    invoice: Optional[InvoiceResponse] = None

    class Config:
        from_attributes = True

class RefundCreate(BaseModel):
    payment_id: str
    amount: float
    reason: str
