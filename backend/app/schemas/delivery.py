from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeliveryOrderResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    order_id: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    delivery_fee: float
    status: str # Pending, Assigned, PickedUp, OutForDelivery, Delivered, Failed, Cancelled
    rider_id: Optional[str]
    rider_name: Optional[str]
    dispatched_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryAssignRequest(BaseModel):
    rider_id: str
    rider_name: str

class DeliveryStatusUpdate(BaseModel):
    status: str # PickedUp, OutForDelivery, Delivered, Failed, Cancelled
    notes: Optional[str] = None
