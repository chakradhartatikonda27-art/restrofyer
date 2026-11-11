from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.inventory import InventoryCategory, InventoryItem, StockMovement
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    StockMovementCreate, StockMovementResponse
)

router = APIRouter()

@router.get("/items", response_model=List[InventoryItemResponse])
def list_inventory_items(
    low_stock_only: bool = False,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(InventoryItem).filter(InventoryItem.tenant_id == current_user.tenant_id)
    items = query.order_by(InventoryItem.name.asc()).all()
    
    res = []
    for item in items:
        is_low = float(item.current_stock) <= float(item.minimum_stock)
        if low_stock_only and not is_low:
            continue
        res.append(InventoryItemResponse(
            id=item.id,
            tenant_id=item.tenant_id,
            category_id=item.category_id,
            name=item.name,
            sku=item.sku,
            uom=item.uom,
            current_stock=float(item.current_stock),
            minimum_stock=float(item.minimum_stock),
            cost_per_unit=float(item.cost_per_unit),
            storage_location=item.storage_location,
            is_low_stock=is_low
        ))
    return res

@router.post("/items", response_model=InventoryItemResponse)
def create_inventory_item(
    data: InventoryItemCreate,
    current_user = Depends(require_permission(Permission.MANAGE_INVENTORY)),
    db: Session = Depends(get_db)
):
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        category_id=data.category_id,
        name=data.name,
        sku=data.sku,
        uom=data.uom,
        current_stock=Decimal(str(data.current_stock)),
        minimum_stock=Decimal(str(data.minimum_stock)),
        cost_per_unit=Decimal(str(data.cost_per_unit)),
        storage_location=data.storage_location
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return InventoryItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        category_id=item.category_id,
        name=item.name,
        sku=item.sku,
        uom=item.uom,
        current_stock=float(item.current_stock),
        minimum_stock=float(item.minimum_stock),
        cost_per_unit=float(item.cost_per_unit),
        storage_location=item.storage_location,
        is_low_stock=float(item.current_stock) <= float(item.minimum_stock)
    )

@router.post("/movements", response_model=StockMovementResponse)
def record_stock_movement(
    data: StockMovementCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_INVENTORY)),
    db: Session = Depends(get_db)
):
    item = db.query(InventoryItem).filter(
        InventoryItem.id == data.inventory_item_id,
        InventoryItem.tenant_id == current_user.tenant_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    qty = Decimal(str(data.quantity))
    item.current_stock += qty

    movement = StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        inventory_item_id=item.id,
        movement_type=data.movement_type,
        quantity=qty,
        unit_cost=Decimal(str(data.unit_cost or item.cost_per_unit)),
        reference_id=data.reference_id,
        notes=data.notes,
        created_by=current_user.full_name
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
