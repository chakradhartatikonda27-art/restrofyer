from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.crm import Customer, CustomerAddress, LoyaltyAccount
from app.schemas.crm import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter()

@router.get("", response_model=List[CustomerResponse])
def list_customers(
    search: Optional[str] = None,
    segment: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(Customer.tenant_id == current_user.tenant_id)
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%") | Customer.phone.ilike(f"%{search}%"))
    if segment:
        query = query.filter(Customer.segment == segment)

    customers = query.order_by(Customer.total_spend.desc()).limit(100).all()
    res = []
    for c in customers:
        points = c.loyalty_account.points_balance if c.loyalty_account else 0
        tier = c.loyalty_account.tier if c.loyalty_account else "Silver"
        res.append(CustomerResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            name=c.name,
            phone=c.phone,
            email=c.email,
            segment=c.segment,
            total_spend=float(c.total_spend),
            total_visits=c.total_visits,
            notes=c.notes,
            first_visit_at=c.first_visit_at,
            last_visit_at=c.last_visit_at,
            loyalty_points=points,
            loyalty_tier=tier
        ))
    return res

@router.post("", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    current_user = Depends(require_permission(Permission.MANAGE_CUSTOMERS)),
    db: Session = Depends(get_db)
):
    existing = db.query(Customer).filter(
        Customer.phone == data.phone,
        Customer.tenant_id == current_user.tenant_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this phone number already exists")

    cust = Customer(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        notes=data.notes,
        segment="New",
        total_spend=0.00,
        total_visits=1
    )
    db.add(cust)
    db.flush()

    if data.address:
        addr = CustomerAddress(
            id=str(uuid.uuid4()),
            customer_id=cust.id,
            label="Home",
            address=data.address
        )
        db.add(addr)

    # Initialize loyalty account
    loyalty = LoyaltyAccount(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        customer_id=cust.id,
        tier="Silver",
        points_balance=0
    )
    db.add(loyalty)

    db.commit()
    db.refresh(cust)

    return CustomerResponse(
        id=cust.id,
        tenant_id=cust.tenant_id,
        name=cust.name,
        phone=cust.phone,
        email=cust.email,
        segment=cust.segment,
        total_spend=0.0,
        total_visits=1,
        notes=cust.notes,
        first_visit_at=cust.first_visit_at,
        last_visit_at=cust.last_visit_at,
        loyalty_points=0,
        loyalty_tier="Silver"
    )
