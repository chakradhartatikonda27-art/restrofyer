from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse
from app.services.pos_service import create_pos_order

router = APIRouter()

@router.get("", response_model=List[OrderResponse])
def list_orders(
    status_filter: Optional[str] = None,
    order_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 50,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Order).filter(
        Order.tenant_id == current_user.tenant_id,
        Order.branch_id == branch_id
    )
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if order_type:
        query = query.filter(Order.order_type == order_type)
    if from_date:
        query = query.filter(Order.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Order.created_at <= datetime.combine(to_date, datetime.max.time()))

    return query.order_by(Order.created_at.desc()).limit(limit).all()

@router.post("", response_model=OrderResponse)
def create_order(
    data: OrderCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.CREATE_ORDER)),
    db: Session = Depends(get_db)
):
    order = create_pos_order(db, current_user.tenant_id, branch_id, data, current_user)
    return order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
