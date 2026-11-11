from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.models.saas import Tenant, Subscription, SubscriptionPlan, PlatformUser, PlatformAuditLog
from app.models.organization import Branch, User, BranchMembership, AuditLog
from app.schemas.auth import LoginRequest, PlatformLoginRequest, TenantRegisterRequest, Token, UserProfileResponse
from app.core.deps import get_current_user_or_admin, get_current_user

router = APIRouter()

@router.post("/register", response_model=Token)
def register_tenant(data: TenantRegisterRequest, db: Session = Depends(get_db)):
    # 1. Check if email already registered
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    slug_base = data.restaurant_name.lower().replace(" ", "-").replace("'", "")
    existing_slug = db.query(Tenant).filter(Tenant.slug == slug_base).first()
    slug = slug_base if not existing_slug else f"{slug_base}-{str(uuid.uuid4())[:6]}"

    # 2. Create Tenant
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=data.restaurant_name,
        slug=slug,
        business_type=data.business_type,
        contact_email=data.email,
        contact_phone=data.phone,
        country=data.country,
        currency=data.currency,
        status="Active",
        onboarding_completed=False,
        onboarding_step=1
    )
    db.add(tenant)
    db.flush()

    # 3. Create Default First Branch
    branch = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name=f"{data.restaurant_name} - Main Branch",
        code="BRANCH-01",
        address="123 Culinary Boulevard",
        city="Hyderabad",
        state="Telangana",
        currency=data.currency,
        tax_rate=5.00,
        is_active=True
    )
    db.add(branch)
    db.flush()

    # 4. Create Tenant Owner User
    owner = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.owner_name,
        phone=data.phone,
        role="TENANT_OWNER",
        branch_id=branch.id,
        is_active=True
    )
    db.add(owner)
    db.flush()

    # 5. Assign Subscription
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == data.plan_code).first()
    if not plan:
        plan = db.query(SubscriptionPlan).first() # Fallback to first available

    if plan:
        sub = Subscription(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            plan_id=plan.id,
            status="Active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
        db.add(sub)

    # Log Platform Event
    audit = PlatformAuditLog(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        actor_id=owner.id,
        actor_email=owner.email,
        action="TENANT_REGISTERED",
        entity_type="Tenant",
        entity_id=tenant.id,
        details={"restaurant_name": data.restaurant_name, "plan": data.plan_code}
    )
    db.add(audit)

    db.commit()

    token = create_access_token(
        subject=owner.id,
        tenant_id=tenant.id,
        role="TENANT_OWNER",
        branch_id=branch.id,
        is_super_admin=False
    )
    return Token(
        access_token=token,
        refresh_token=create_refresh_token(owner.id),
        role="TENANT_OWNER",
        tenant_id=tenant.id,
        branch_id=branch.id,
        user_name=owner.full_name,
        is_super_admin=False
    )

@router.post("/login", response_model=Token)
def login_tenant_user(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or tenant.status == "Suspended":
        raise HTTPException(status_code=403, detail="Restaurant organization is suspended. Please contact support.")

    token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        branch_id=user.branch_id,
        is_super_admin=False
    )
    return Token(
        access_token=token,
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        tenant_id=user.tenant_id,
        branch_id=user.branch_id,
        user_name=user.full_name,
        is_super_admin=False
    )

@router.post("/platform-login", response_model=Token)
def login_platform_admin(data: PlatformLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(PlatformUser).filter(PlatformUser.email == data.email).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Invalid platform credentials")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Platform account disabled")

    token = create_access_token(
        subject=admin.id,
        role="SUPER_ADMIN",
        is_super_admin=True
    )
    return Token(
        access_token=token,
        refresh_token=create_refresh_token(admin.id),
        role="SUPER_ADMIN",
        user_name=admin.full_name,
        is_super_admin=True
    )

@router.get("/me", response_model=UserProfileResponse)
def get_me(user = Depends(get_current_user_or_admin), db: Session = Depends(get_db)):
    if isinstance(user, PlatformUser):
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role="SUPER_ADMIN",
            is_super_admin=True
        )

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    branch = db.query(Branch).filter(Branch.id == user.branch_id).first() if user.branch_id else None

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_name=tenant.name if tenant else None,
        tenant_slug=tenant.slug if tenant else None,
        branch_id=user.branch_id,
        branch_name=branch.name if branch else None,
        is_super_admin=False
    )
