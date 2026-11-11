from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Text, DateTime
from datetime import datetime
from app.models.base import BaseModel, TenantMixin, BranchMixin

class DeliveryExecutive(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "delivery_executives"
    
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    vehicle_number = Column(String(50), nullable=True)
    is_available = Column(Boolean, default=True)

class DeliveryOrder(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "delivery_orders"
    
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    delivery_address = Column(String(500), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=40.00)
    status = Column(String(30), default="Pending") # Pending, Assigned, PickedUp, OutForDelivery, Delivered, Failed, Cancelled
    rider_id = Column(String(36), ForeignKey("delivery_executives.id", ondelete="SET NULL"), nullable=True)
    rider_name = Column(String(100), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
