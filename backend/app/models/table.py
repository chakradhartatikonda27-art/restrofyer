from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin, BranchMixin


class DiningArea(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "dining_areas"

    name = Column(String(100), nullable=False)  # "Indoor Hall", "Rooftop Terrace", "VIP Section"
    display_order = Column(Integer, default=0)

    branch = relationship("Branch", back_populates="dining_areas")
    tables = relationship("RestaurantTable", back_populates="area", cascade="all, delete-orphan")


class RestaurantTable(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "restaurant_tables"

    area_id = Column(String(36), ForeignKey("dining_areas.id", ondelete="CASCADE"), nullable=False)
    assigned_menu_id = Column(String(36), ForeignKey("menus.id", ondelete="SET NULL"), nullable=True)
    table_number = Column(String(20), nullable=False)  # e.g. "T-01", "T-02"
    name = Column(String(50), nullable=True)  # e.g. "Corner Booth", "Window 4"
    capacity = Column(Integer, default=4)
    status = Column(String(30), default="Available")  # Available, Occupied, Reserved, Cleaning, Blocked
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    qr_code_token = Column(String(100), unique=True, nullable=True)
    occupied_since = Column(DateTime, nullable=True)
    active_order_id = Column(String(36), nullable=True)

    branch = relationship("Branch", back_populates="tables")
    area = relationship("DiningArea", back_populates="tables")
    reservations = relationship("Reservation", back_populates="table")


class Reservation(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "reservations"

    table_id = Column(String(36), ForeignKey("restaurant_tables.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_email = Column(String(255), nullable=True)
    party_size = Column(Integer, default=2)
    reservation_time = Column(DateTime, nullable=False)
    status = Column(String(30), default="Confirmed")  # Pending, Confirmed, CheckedIn, Completed, Cancelled, NoShow
    special_requests = Column(Text, nullable=True)

    table = relationship("RestaurantTable", back_populates="reservations")
