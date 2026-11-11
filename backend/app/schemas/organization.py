from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BranchCreate(BaseModel):
    name: str = Field(..., min_length=2)
    code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: str
    city: str = "Hyderabad"
    state: str = "Telangana"
    postal_code: Optional[str] = None
    tax_rate: float = 5.0
    service_charge_rate: float = 0.0
    currency: str = "INR"

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_rate: Optional[float] = None
    service_charge_rate: Optional[float] = None
    is_active: Optional[bool] = None

class BranchResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    phone: Optional[str]
    email: Optional[str]
    address: str
    city: str
    state: str
    postal_code: Optional[str]
    tax_rate: float
    service_charge_rate: float
    currency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: str # TENANT_ADMIN, BRANCH_MANAGER, CASHIER, WAITER, KITCHEN_STAFF, INVENTORY_MANAGER
    phone: Optional[str] = None
    branch_id: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    branch_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
