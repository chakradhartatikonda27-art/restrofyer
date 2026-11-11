from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, TenantMixin, BranchMixin

class Supplier(BaseModel, TenantMixin):
    __tablename__ = "suppliers"
    
    name = Column(String(255), nullable=False) # e.g. "FarmFresh Organic Dairy", "Metro Food Supplies"
    contact_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=False)
    address = Column(String(500), nullable=True)
    tax_number = Column(String(50), nullable=True) # GSTIN / Tax ID
    payment_terms = Column(String(100), default="Net 30 Days")
    
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class PurchaseOrder(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "purchase_orders"
    
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    po_number = Column(String(50), unique=True, nullable=False) # e.g. "PO-2026-0012"
    status = Column(String(30), default="Draft") # Draft, Submitted, Approved, PartiallyReceived, Received, Cancelled
    total_amount = Column(Numeric(10, 2), default=0.00)
    expected_delivery_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderItem(BaseModel):
    __tablename__ = "purchase_order_items"
    
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(String(36), ForeignKey("inventory_items.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="items")

class GoodsReceipt(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "goods_receipts"
    
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    grn_number = Column(String(50), unique=True, nullable=False) # e.g. "GRN-2026-0012"
    received_date = Column(DateTime, default=datetime.utcnow)
    received_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
