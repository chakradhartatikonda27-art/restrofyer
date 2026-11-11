from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, TenantMixin, BranchMixin

class Kitchen(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "kitchens"
    
    name = Column(String(100), nullable=False) # e.g. "Main Kitchen"
    
    stations = relationship("KitchenStation", back_populates="kitchen", cascade="all, delete-orphan")

class KitchenStation(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "kitchen_stations"
    
    kitchen_id = Column(String(36), ForeignKey("kitchens.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False) # "Grill Station", "Wok / Asian", "Pizza / Bakery", "Beverage / Bar"
    printer_ip = Column(String(50), nullable=True)
    
    kitchen = relationship("Kitchen", back_populates="stations")
    kots = relationship("KOT", back_populates="station")

class KOT(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "kots"
    
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    kitchen_station_id = Column(String(36), ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    kot_number = Column(String(50), nullable=False) # e.g. "KOT-1042"
    status = Column(String(30), default="New") # New, Accepted, Preparing, Ready, Served, Cancelled
    waiter_name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    started_preparing_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    served_at = Column(DateTime, nullable=True)
    
    station = relationship("KitchenStation", back_populates="kots")
    order = relationship("Order", back_populates="kots")
    items = relationship("KOTItem", back_populates="kot", cascade="all, delete-orphan")

class KOTItem(BaseModel):
    __tablename__ = "kot_items"
    
    kot_id = Column(String(36), ForeignKey("kots.id", ondelete="CASCADE"), nullable=False)
    order_item_id = Column(String(36), nullable=False)
    item_name = Column(String(255), nullable=False)
    variant_name = Column(String(100), nullable=True)
    modifiers_summary = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1)
    notes = Column(String(255), nullable=True)
    status = Column(String(30), default="New") # New, Preparing, Ready
    
    kot = relationship("KOT", back_populates="items")
