from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RegisterOpenRequest(BaseModel):
    register_id: str
    opening_float: float = 0.0

class RegisterCloseRequest(BaseModel):
    actual_closing_cash: float
    notes: Optional[str] = None

class CashTransactionCreate(BaseModel):
    transaction_type: str # CASH_IN, CASH_OUT
    amount: float
    reason: str

class CashTransactionResponse(BaseModel):
    id: str
    session_id: str
    transaction_type: str
    amount: float
    reason: str
    authorized_by: str
    created_at: datetime

    class Config:
        from_attributes = True

class CashSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    register_id: str
    cashier_id: str
    cashier_name: str
    opened_at: datetime
    closed_at: Optional[datetime]
    opening_float: float
    cash_sales: float
    cash_in: float
    cash_out: float
    cash_refunds: float
    expected_closing_cash: float
    actual_closing_cash: Optional[float]
    variance: float
    status: str
    notes: Optional[str]
    transactions: List[CashTransactionResponse] = []

    class Config:
        from_attributes = True

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    payment_method: str = "Cash"
    payee: str
    notes: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    category: str
    amount: float
    payment_method: str
    payee: str
    expense_date: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True
