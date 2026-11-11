from sqlalchemy import Column, String, Numeric, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel, TenantMixin, BranchMixin

class CashRegister(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "cash_registers"
    
    name = Column(String(100), nullable=False) # e.g. "Main Terminal POS 01"
    status = Column(String(30), default="Closed") # Open, Closed
    
    sessions = relationship("CashRegisterSession", back_populates="register", cascade="all, delete-orphan")

class CashRegisterSession(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "cash_register_sessions"
    
    register_id = Column(String(36), ForeignKey("cash_registers.id", ondelete="CASCADE"), nullable=False)
    cashier_id = Column(String(36), nullable=False)
    cashier_name = Column(String(100), nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Financial reconciliation variables
    opening_float = Column(Numeric(10, 2), default=0.00, nullable=False) # Cash placed in drawer at open
    cash_sales = Column(Numeric(10, 2), default=0.00, nullable=False)
    cash_in = Column(Numeric(10, 2), default=0.00, nullable=False)
    cash_out = Column(Numeric(10, 2), default=0.00, nullable=False)
    cash_refunds = Column(Numeric(10, 2), default=0.00, nullable=False)
    expected_closing_cash = Column(Numeric(10, 2), default=0.00, nullable=False)
    actual_closing_cash = Column(Numeric(10, 2), nullable=True)
    variance = Column(Numeric(10, 2), default=0.00) # actual - expected
    status = Column(String(30), default="Open") # Open, Closed
    notes = Column(Text, nullable=True)
    
    register = relationship("CashRegister", back_populates="sessions")
    cash_transactions = relationship("CashTransaction", back_populates="session", cascade="all, delete-orphan")

class CashTransaction(BaseModel):
    __tablename__ = "cash_transactions"
    
    session_id = Column(String(36), ForeignKey("cash_register_sessions.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(30), nullable=False) # CASH_IN, CASH_OUT
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    authorized_by = Column(String(100), nullable=False)
    
    session = relationship("CashRegisterSession", back_populates="cash_transactions")

class Expense(BaseModel, TenantMixin, BranchMixin):
    __tablename__ = "expenses"
    
    category = Column(String(100), nullable=False) # Rent, Electricity/Water, Vendor Payout, Repairs, Petty Cash
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), default="Cash") # Cash, Bank Transfer, UPI, Cheque
    payee = Column(String(255), nullable=False)
    receipt_url = Column(String(500), nullable=True)
    expense_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
