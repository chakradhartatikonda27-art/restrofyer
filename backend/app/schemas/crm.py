from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    phone: str
    email: Optional[str]
    segment: str
    total_spend: float
    total_visits: int
    notes: Optional[str]
    first_visit_at: datetime
    last_visit_at: datetime
    loyalty_points: Optional[int] = 0
    loyalty_tier: Optional[str] = "Silver"

    class Config:
        from_attributes = True

class LoyaltyTransactionCreate(BaseModel):
    points: int
    reason: str
