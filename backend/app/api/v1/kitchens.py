from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.kitchen import KitchenStation, KOT, KOTItem
from app.schemas.kitchen import KOTResponse, KOTStatusUpdate, KitchenStationResponse

router = APIRouter()

@router.get("/stations", response_model=List[KitchenStationResponse])
def list_stations(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(KitchenStation).filter(
        KitchenStation.tenant_id == current_user.tenant_id,
        KitchenStation.branch_id == branch_id
    ).all()

@router.get("/kots", response_model=List[KOTResponse])
def list_active_kots(
    station_id: Optional[str] = None,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(KOT).filter(
        KOT.tenant_id == current_user.tenant_id,
        KOT.branch_id == branch_id,
        KOT.status.in_(["New", "Accepted", "Preparing", "Ready"])
    )
    if station_id:
        query = query.filter(KOT.kitchen_station_id == station_id)

    kots = query.order_by(KOT.created_at.asc()).all()
    res = []
    for kot in kots:
        station_name = kot.station.name if kot.station else "Main Kitchen"
        kot_dict = {
            "id": kot.id,
            "tenant_id": kot.tenant_id,
            "branch_id": kot.branch_id,
            "order_id": kot.order_id,
            "kot_number": kot.kot_number,
            "kitchen_station_id": kot.kitchen_station_id,
            "station_name": station_name,
            "status": kot.status,
            "waiter_name": kot.waiter_name,
            "notes": kot.notes,
            "created_at": kot.created_at,
            "started_preparing_at": kot.started_preparing_at,
            "ready_at": kot.ready_at,
            "items": [
                {
                    "id": item.id,
                    "order_item_id": item.order_item_id,
                    "item_name": item.item_name,
                    "variant_name": item.variant_name,
                    "modifiers_summary": item.modifiers_summary,
                    "quantity": item.quantity,
                    "notes": item.notes,
                    "status": item.status
                }
                for item in kot.items
            ]
        }
        res.append(KOTResponse(**kot_dict))
    return res

@router.patch("/kots/{kot_id}/status", response_model=KOTResponse)
def update_kot_status(
    kot_id: str,
    data: KOTStatusUpdate,
    current_user = Depends(require_permission(Permission.UPDATE_KOT_STATUS)),
    db: Session = Depends(get_db)
):
    kot = db.query(KOT).filter(
        KOT.id == kot_id,
        KOT.tenant_id == current_user.tenant_id
    ).first()
    if not kot:
        raise HTTPException(status_code=404, detail="KOT not found")

    kot.status = data.status
    if data.status == "Preparing" and not kot.started_preparing_at:
        kot.started_preparing_at = datetime.utcnow()
    elif data.status == "Ready":
        kot.ready_at = datetime.utcnow()
    elif data.status == "Served":
        kot.served_at = datetime.utcnow()

    # Update item statuses as well
    for item in kot.items:
        item.status = data.status

    db.commit()
    db.refresh(kot)
    
    station_name = kot.station.name if kot.station else "Main Kitchen"
    return KOTResponse(
        id=kot.id,
        tenant_id=kot.tenant_id,
        branch_id=kot.branch_id,
        order_id=kot.order_id,
        kot_number=kot.kot_number,
        kitchen_station_id=kot.kitchen_station_id,
        station_name=station_name,
        status=kot.status,
        waiter_name=kot.waiter_name,
        notes=kot.notes,
        created_at=kot.created_at,
        started_preparing_at=kot.started_preparing_at,
        ready_at=kot.ready_at,
        items=[
            {
                "id": item.id,
                "order_item_id": item.order_item_id,
                "item_name": item.item_name,
                "variant_name": item.variant_name,
                "modifiers_summary": item.modifiers_summary,
                "quantity": item.quantity,
                "notes": item.notes,
                "status": item.status
            }
            for item in kot.items
        ]
    )
