from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.delivery import DeliveryOrder, DeliveryExecutive
from app.schemas.delivery import DeliveryOrderResponse, DeliveryAssignRequest, DeliveryStatusUpdate

router = APIRouter()

@router.get("/orders", response_model=List[DeliveryOrderResponse])
def list_delivery_orders(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(DeliveryOrder).filter(
        DeliveryOrder.tenant_id == current_user.tenant_id,
        DeliveryOrder.branch_id == branch_id
    ).order_by(DeliveryOrder.created_at.desc()).all()

@router.get("/executives", response_model=List[dict])
def list_delivery_executives(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    execs = db.query(DeliveryExecutive).filter(
        DeliveryExecutive.tenant_id == current_user.tenant_id,
        DeliveryExecutive.branch_id == branch_id
    ).all()
    return [{"id": e.id, "name": e.name, "phone": e.phone, "is_available": e.is_available} for e in execs]

@router.post("/orders/{order_id}/assign", response_model=DeliveryOrderResponse)
def assign_rider(
    order_id: str,
    data: DeliveryAssignRequest,
    current_user = Depends(require_permission(Permission.ACCESS_DELIVERY)),
    db: Session = Depends(get_db)
):
    deliv = db.query(DeliveryOrder).filter(
        DeliveryOrder.id == order_id,
        DeliveryOrder.tenant_id == current_user.tenant_id
    ).first()
    if not deliv:
        raise HTTPException(status_code=404, detail="Delivery order not found")

    deliv.rider_id = data.rider_id
    deliv.rider_name = data.rider_name
    deliv.status = "Assigned"
    db.commit()
    db.refresh(deliv)
    return deliv

@router.patch("/orders/{order_id}/status", response_model=DeliveryOrderResponse)
def update_delivery_status(
    order_id: str,
    data: DeliveryStatusUpdate,
    current_user = Depends(require_permission(Permission.UPDATE_DELIVERY_STATUS)),
    db: Session = Depends(get_db)
):
    deliv = db.query(DeliveryOrder).filter(
        DeliveryOrder.id == order_id,
        DeliveryOrder.tenant_id == current_user.tenant_id
    ).first()
    if not deliv:
        raise HTTPException(status_code=404, detail="Delivery order not found")

    deliv.status = data.status
    if data.status == "PickedUp":
        deliv.dispatched_at = datetime.utcnow()
    elif data.status == "Delivered":
        deliv.delivered_at = datetime.utcnow()

    db.commit()
    db.refresh(deliv)
    return deliv
