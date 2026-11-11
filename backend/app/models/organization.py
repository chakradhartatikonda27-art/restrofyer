from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin

class Branch(BaseModel, TenantMixin):
    __tablename__ = "branches"
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False) # e.g. "MAIN-01", "DOWNTOWN-02"
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), default="Hyderabad")
    state = Column(String(100), default="Telangana")
    postal_code = Column(String(20), nullable=True)
    
    # Financial/Tax configurations per branch
    tax_rate = Column(Numeric(5, 2), default=5.00) # GST/VAT percentage
    service_charge_rate = Column(Numeric(5, 2), default=0.00)
    currency = Column(String(10), default="INR")
    is_active = Column(Boolean, default=True)
    operating_hours = Column(JSON, default=dict) # e.g. {"mon": "11:00-23:00"}
    
    # Relationships
    tenant = relationship("Tenant", back_populates="branches")
    users = relationship("User", back_populates="primary_branch")
    tables = relationship("RestaurantTable", back_populates="branch", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="branch")
    dining_areas = relationship("DiningArea", back_populates="branch", cascade="all, delete-orphan")

class User(BaseModel, TenantMixin):
    __tablename__ = "users"
    
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), default="CASHIER", nullable=False) # TENANT_OWNER, TENANT_ADMIN, BRANCH_MANAGER, CASHIER, WAITER, KITCHEN_STAFF, INVENTORY_MANAGER
    is_active = Column(Boolean, default=True)
    
    # Primary assigned branch (can be None for Tenant Owner/Admin who access all branches)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    
    tenant = relationship("Tenant", back_populates="users")
    primary_branch = relationship("Branch", back_populates="users")
    memberships = relationship("BranchMembership", back_populates="user", cascade="all, delete-orphan")

class BranchMembership(BaseModel, TenantMixin):
    __tablename__ = "branch_memberships"
    
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    
    user = relationship("User", back_populates="memberships")
    branch = relationship("Branch")

class AuditLog(BaseModel, TenantMixin):
    __tablename__ = "audit_logs"
    
    branch_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False) # ORDER_CREATED, PAYMENT_PROCESSED, VOID_ORDER, PRICE_CHANGED
    entity_type = Column(String(100), nullable=False) # Order, Invoice, MenuItem, InventoryItem
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
