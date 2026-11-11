from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    branch_id: Optional[str] = None
    user_name: Optional[str] = None
    is_super_admin: bool = False

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[str] = None
    is_super_admin: bool = False

class LoginRequest(BaseModel):
    email: str
    password: str

class PlatformLoginRequest(BaseModel):
    email: str
    password: str

class TenantRegisterRequest(BaseModel):
    restaurant_name: str = Field(..., min_length=2, max_length=255)
    owner_name: str = Field(..., min_length=2, max_length=255)
    email: str
    password: str = Field(..., min_length=6)
    phone: str
    business_type: str = "Fine Dining"
    country: str = "India"
    currency: str = "INR"
    plan_code: str = "starter" # starter, growth, pro, enterprise

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_slug: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    is_super_admin: bool = False
