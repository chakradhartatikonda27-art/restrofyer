from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class KOTItemResponse(BaseModel):
    id: str
    order_item_id: str
    item_name: str
    variant_name: Optional[str]
    modifiers_summary: Optional[str]
    quantity: int
    notes: Optional[str]
    status: str

    class Config:
        from_attributes = True

class KOTResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    order_id: str
    kot_number: str
    kitchen_station_id: Optional[str]
    station_name: Optional[str] = None
    status: str # New, Accepted, Preparing, Ready, Served, Cancelled
    waiter_name: Optional[str]
    notes: Optional[str]
    created_at: datetime
    started_preparing_at: Optional[datetime]
    ready_at: Optional[datetime]
    items: List[KOTItemResponse] = []

    class Config:
        from_attributes = True

class KOTStatusUpdate(BaseModel):
    status: str # Accepted, Preparing, Ready, Served, Cancelled

class KitchenStationResponse(BaseModel):
    id: str
    name: str
    printer_ip: Optional[str]

    class Config:
        from_attributes = True
