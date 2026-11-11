from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, TenantMixin

class Customer(BaseModel, TenantMixin):
    __tablename__ = "customers"
    
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    segment = Column(String(50), default="New") # New, Returning, VIP, HighSpending, Inactive
    total_spend = Column(Numeric(12, 2), default=0.00)
    total_visits = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    first_visit_at = Column(DateTime, default=datetime.utcnow)
    last_visit_at = Column(DateTime, default=datetime.utcnow)
    
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    loyalty_account = relationship("LoyaltyAccount", back_populates="customer", uselist=False, cascade="all, delete-orphan")

class CustomerAddress(BaseModel):
    __tablename__ = "customer_addresses"
    
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(50), default="Home") # Home, Office, Other
    address = Column(String(500), nullable=False)
    landmark = Column(String(255), nullable=True)
    city = Column(String(100), default="Hyderabad")
    postal_code = Column(String(20), nullable=True)
    
    customer = relationship("Customer", back_populates="addresses")

class LoyaltyAccount(BaseModel, TenantMixin):
    __tablename__ = "loyalty_accounts"
    
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False)
    tier = Column(String(30), default="Silver") # Silver, Gold, Platinum
    points_balance = Column(Integer, default=0, nullable=False)
    
    customer = relationship("Customer", back_populates="loyalty_account")
    transactions = relationship("LoyaltyTransaction", back_populates="account", cascade="all, delete-orphan")

class LoyaltyTransaction(BaseModel, TenantMixin):
    __tablename__ = "loyalty_transactions"
    
    account_id = Column(String(36), ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(30), nullable=False) # EARN, REDEEM, ADJUSTMENT, EXPIRED
    points = Column(Integer, nullable=False) # Positive or negative
    running_balance = Column(Integer, nullable=False)
    order_id = Column(String(36), nullable=True)
    reason = Column(String(255), nullable=True)
    
    account = relationship("LoyaltyAccount", back_populates="transactions")
