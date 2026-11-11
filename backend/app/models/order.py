from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, TenantMixin, BranchMixin

class Order(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "orders"
    
    order_number = Column(String(50), nullable=False) # e.g. "ORD-2026-0042"
    order_type = Column(String(30), default="DineIn") # DineIn, Takeaway, Delivery, Online, QR
    status = Column(String(30), default="Confirmed") # Draft, Confirmed, InKitchen, Ready, Served, Completed, Cancelled
    
    # Dining table if DineIn / QR
    table_id = Column(String(36), ForeignKey("restaurant_tables.id", ondelete="SET NULL"), nullable=True)
    table_number = Column(String(20), nullable=True)
    
    # Customer
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    
    # Financial breakdown
    subtotal = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_reason = Column(String(255), nullable=True)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    service_charge = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Staff attribution
    cashier_id = Column(String(36), nullable=True)
    cashier_name = Column(String(100), nullable=True)
    waiter_id = Column(String(36), nullable=True)
    waiter_name = Column(String(100), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    branch = relationship("Branch", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    kots = relationship("KOT", back_populates="order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderItem(BaseModel):
    __tablename__ = "order_items"
    
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(String(36), nullable=False)
    item_name = Column(String(255), nullable=False) # Snapshot of name at order time
    unit_price = Column(Numeric(10, 2), nullable=False) # Immutable price snapshot
    cost_price = Column(Numeric(10, 2), default=0.00) # Cost snapshot for margin tracking
    quantity = Column(Integer, default=1, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=5.00)
    
    # Variant and modifier snapshots
    variant_id = Column(String(36), nullable=True)
    variant_name = Column(String(100), nullable=True)
    modifiers = Column(JSON, default=list) # e.g. [{"name": "Extra Cheese", "price": 40.0}]
    notes = Column(String(255), nullable=True)
    
    order = relationship("Order", back_populates="items")

class Invoice(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "invoices"
    
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False) # e.g. "INV-2026-0042"
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0.00)
    tax = Column(Numeric(10, 2), default=0.00)
    service_charge = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00)
    status = Column(String(30), default="Paid") # Paid, Unpaid, PartiallyPaid, Refunded
    
    order = relationship("Order", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class Payment(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "payments"
    
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(String(36), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), default="Cash") # Cash, Card, UPI, Wallet, Split
    payment_reference = Column(String(255), nullable=True)
    status = Column(String(30), default="Success") # Success, Failed, Refunded
    cash_register_session_id = Column(String(36), nullable=True)
    
    invoice = relationship("Invoice", back_populates="payments")

class Refund(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "refunds"
    
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    invoice_id = Column(String(36), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    authorized_by = Column(String(100), nullable=False)
