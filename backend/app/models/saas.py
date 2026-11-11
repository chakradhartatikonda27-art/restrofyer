from sqlalchemy import Column, String, Boolean, Numeric, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, generate_uuid

class Tenant(BaseModel):
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    business_type = Column(String(100), default="Fine Dining")
    status = Column(String(50), default="Active", nullable=False) # Active, Trial, Suspended, Deactivated
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    country = Column(String(100), default="India")
    currency = Column(String(10), default="INR") # INR, USD, EUR, GBP
    timezone = Column(String(50), default="Asia/Kolkata")
    
    # Onboarding tracking
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=1)
    
    # Relationships
    branches = relationship("Branch", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    invoices = relationship("SubscriptionInvoice", back_populates="tenant", cascade="all, delete-orphan")

class SubscriptionPlan(BaseModel):
    __tablename__ = "subscription_plans"
    
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False) # starter, growth, pro, enterprise
    description = Column(String(500), nullable=True)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    annual_price = Column(Numeric(10, 2), nullable=False)
    branch_limit = Column(Integer, default=1)
    user_limit = Column(Integer, default=5)
    pos_terminal_limit = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    
    # Feature entitlement flags stored as JSON
    # e.g., {"pos": True, "kds": True, "inventory": True, "recipes": True, "loyalty": True, "qr_ordering": True}
    features = Column(JSON, default=dict)
    
    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(50), default="Active", nullable=False) # Trial, Active, PastDue, Suspended, Cancelled
    billing_cycle = Column(String(20), default="monthly") # monthly, annual
    current_period_start = Column(DateTime, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    tenant = relationship("Tenant", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

class SubscriptionInvoice(BaseModel):
    __tablename__ = "subscription_invoices"
    
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="Paid") # Paid, Pending, Failed
    payment_method = Column(String(50), default="Credit Card")
    payment_reference = Column(String(255), nullable=True)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    tenant = relationship("Tenant", back_populates="invoices")

class PlatformUser(BaseModel):
    __tablename__ = "platform_users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="SUPER_ADMIN") # SUPER_ADMIN, SAAS_SUPPORT, FINANCE_ADMIN
    is_active = Column(Boolean, default=True)

class PlatformAuditLog(BaseModel):
    __tablename__ = "platform_audit_logs"
    
    tenant_id = Column(String(36), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
