from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.organization import User, Branch
from app.models.saas import Subscription
from app.schemas.organization import UserCreate, UserUpdate, UserResponse

router = APIRouter()

@router.get("", response_model=List[UserResponse])
def list_users(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Strict tenant isolation
    return db.query(User).filter(User.tenant_id == current_user.tenant_id).all()

@router.post("", response_model=UserResponse)
def create_staff_user(
    data: UserCreate,
    current_user = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    # Enforce Subscription User Limit
    sub = db.query(Subscription).filter(Subscription.tenant_id == current_user.tenant_id).first()
    if sub and sub.plan:
        current_user_count = db.query(User).filter(User.tenant_id == current_user.tenant_id).count()
        if current_user_count >= sub.plan.user_limit:
            raise HTTPException(
                status_code=403,
                detail=f"User limit reached for plan ({sub.plan.name}: max {sub.plan.user_limit} users). Upgrade to add more staff."
            )

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
        phone=data.phone,
        branch_id=data.branch_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_staff_user(
    user_id: str,
    data: UserUpdate,
    current_user = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
