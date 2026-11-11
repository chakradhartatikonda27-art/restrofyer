from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.table import DiningArea, RestaurantTable
from app.schemas.table import AreaCreate, AreaResponse, TableCreate, TableUpdate, TableResponse

router = APIRouter()

@router.get("/areas", response_model=List[AreaResponse])
def list_dining_areas(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(DiningArea).filter(
        DiningArea.tenant_id == current_user.tenant_id,
        DiningArea.branch_id == branch_id
    ).order_by(DiningArea.display_order.asc()).all()

@router.post("/areas", response_model=AreaResponse)
def create_dining_area(
    data: AreaCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_TABLES)),
    db: Session = Depends(get_db)
):
    area = DiningArea(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        name=data.name,
        display_order=data.display_order
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area

@router.get("", response_model=List[TableResponse])
def list_tables(
    area_id: str = None,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(RestaurantTable).filter(
        RestaurantTable.tenant_id == current_user.tenant_id,
        RestaurantTable.branch_id == branch_id
    )
    if area_id:
        query = query.filter(RestaurantTable.area_id == area_id)
    return query.order_by(RestaurantTable.table_number.asc()).all()

@router.post("", response_model=TableResponse)
def create_table(
    data: TableCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_TABLES)),
    db: Session = Depends(get_db)
):
    # Unique QR token for table ordering
    qr_token = f"QR-{current_user.tenant_id[:8]}-{data.table_number}-{uuid.uuid4().hex[:6]}"
    
    table = RestaurantTable(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        area_id=data.area_id,
        assigned_menu_id=data.assigned_menu_id,
        table_number=data.table_number,
        name=data.name,
        capacity=data.capacity,
        status="Available",
        pos_x=data.pos_x,
        pos_y=data.pos_y,
        qr_code_token=qr_token
    )
    db.add(table)
    db.commit()
    db.refresh(table)
    return table

@router.put("/{table_id}", response_model=TableResponse)
def update_table(
    table_id: str,
    data: TableUpdate,
    current_user = Depends(require_permission(Permission.MANAGE_TABLES)),
    db: Session = Depends(get_db)
):
    table = db.query(RestaurantTable).filter(
        RestaurantTable.id == table_id,
        RestaurantTable.tenant_id == current_user.tenant_id
    ).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    for field, val in data.dict(exclude_unset=True).items():
        setattr(table, field, val)

    if data.status == "Occupied" and not table.occupied_since:
        table.occupied_since = datetime.utcnow()
    elif data.status in ["Available", "Cleaning"]:
        table.occupied_since = None
        table.active_order_id = None

    db.commit()
    db.refresh(table)
    return table

@router.post("/{table_id}/release")
def release_table(
    table_id: str,
    current_user = Depends(require_permission(Permission.MANAGE_TABLES)),
    db: Session = Depends(get_db)
):
    table = db.query(RestaurantTable).filter(
        RestaurantTable.id == table_id,
        RestaurantTable.tenant_id == current_user.tenant_id
    ).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    table.status = "Available"
    table.active_order_id = None
    table.occupied_since = None
    db.commit()
    return {"message": f"Table {table.table_number} is now Available"}
