from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.table import Reservation, RestaurantTable
from app.schemas.table import ReservationCreate, ReservationResponse

router = APIRouter()

@router.get("", response_model=List[ReservationResponse])
def list_reservations(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Reservation).filter(
        Reservation.tenant_id == current_user.tenant_id,
        Reservation.branch_id == branch_id
    ).order_by(Reservation.reservation_time.asc()).all()

@router.post("", response_model=ReservationResponse)
def create_reservation(
    data: ReservationCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_RESERVATIONS)),
    db: Session = Depends(get_db)
):
    if data.table_id:
        table = db.query(RestaurantTable).filter(
            RestaurantTable.id == data.table_id,
            RestaurantTable.tenant_id == current_user.tenant_id
        ).first()
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        table.status = "Reserved"

    res = Reservation(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        table_id=data.table_id,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        party_size=data.party_size,
        reservation_time=data.reservation_time,
        status="Confirmed",
        special_requests=data.special_requests
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@router.patch("/{res_id}/status")
def update_reservation_status(
    res_id: str,
    status_val: str,
    current_user = Depends(require_permission(Permission.MANAGE_RESERVATIONS)),
    db: Session = Depends(get_db)
):
    res = db.query(Reservation).filter(
        Reservation.id == res_id,
        Reservation.tenant_id == current_user.tenant_id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")

    res.status = status_val
    if status_val == "CheckedIn" and res.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == res.table_id).first()
        if table:
            table.status = "Occupied"
            table.occupied_since = datetime.utcnow()
    elif status_val in ["Completed", "Cancelled", "NoShow"] and res.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == res.table_id).first()
        if table and table.status == "Reserved":
            table.status = "Available"

    db.commit()
    return {"id": res.id, "status": res.status}
