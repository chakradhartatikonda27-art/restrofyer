from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.organization import Branch
from app.models.saas import Tenant, Subscription, SubscriptionPlan
from app.schemas.organization import BranchCreate, BranchUpdate, BranchResponse

router = APIRouter()

@router.get("", response_model=List[BranchResponse])
def list_branches(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Tenant-isolated branch list
    return db.query(Branch).filter(Branch.tenant_id == current_user.tenant_id).order_by(Branch.created_at.asc()).all()

@router.post("", response_model=BranchResponse)
def create_branch(
    data: BranchCreate,
    current_user = Depends(require_permission(Permission.MANAGE_BRANCHES)),
    db: Session = Depends(get_db)
):
    # Enforce Subscription Branch Limit
    sub = db.query(Subscription).filter(Subscription.tenant_id == current_user.tenant_id).first()
    if sub and sub.plan:
        current_branches = db.query(Branch).filter(Branch.tenant_id == current_user.tenant_id).count()
        if current_branches >= sub.plan.branch_limit:
            raise HTTPException(
                status_code=403, 
                detail=f"Branch limit reached for current plan ({sub.plan.name}: max {sub.plan.branch_limit} branches). Upgrade plan to add more."
            )

    branch = Branch(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=data.name,
        code=data.code,
        phone=data.phone,
        email=data.email,
        address=data.address,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        tax_rate=data.tax_rate,
        service_charge_rate=data.service_charge_rate,
        currency=data.currency,
        is_active=True
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch

@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: str,
    data: BranchUpdate,
    current_user = Depends(require_permission(Permission.MANAGE_BRANCHES)),
    db: Session = Depends(get_db)
):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == current_user.tenant_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(branch, field, value)

    db.commit()
    db.refresh(branch)
    return branch
