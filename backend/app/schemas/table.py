from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AreaCreate(BaseModel):
    name: str
    display_order: int = 0


class AreaResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    name: str
    display_order: int

    class Config:
        from_attributes = True


class TableCreate(BaseModel):
    area_id: str
    table_number: str
    name: Optional[str] = None
    capacity: int = 4
    pos_x: int = 0
    pos_y: int = 0
    assigned_menu_id: Optional[str] = None


class TableUpdate(BaseModel):
    table_number: Optional[str] = None
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    active_order_id: Optional[str] = None
    assigned_menu_id: Optional[str] = None


class TableResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    area_id: str
    assigned_menu_id: Optional[str] = None
    table_number: str
    name: Optional[str]
    capacity: int
    status: str
    pos_x: int
    pos_y: int
    qr_code_token: Optional[str]
    occupied_since: Optional[datetime]
    active_order_id: Optional[str]

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    table_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    party_size: int = 2
    reservation_time: datetime
    special_requests: Optional[str] = None


class ReservationResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    table_id: Optional[str]
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    party_size: int
    reservation_time: datetime
    status: str
    special_requests: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
