from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    monthly_price: float
    annual_price: float
    branch_limit: int
    user_limit: int
    pos_terminal_limit: int
    features: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True

class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    business_type: str
    status: str
    contact_email: str
    contact_phone: Optional[str]
    country: str
    currency: str
    timezone: str
    onboarding_completed: bool
    onboarding_step: int
    created_at: datetime
    plan_name: Optional[str] = None
    branch_count: Optional[int] = 0

    class Config:
        from_attributes = True

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    contact_phone: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None
    onboarding_step: Optional[int] = None
    onboarding_completed: Optional[bool] = None

class PlatformMetricsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    suspended_tenants: int
    monthly_recurring_revenue: float
    annual_recurring_revenue: float
    total_orders_processed: int
    total_branches: int
    active_users: int
