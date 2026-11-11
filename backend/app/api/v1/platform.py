from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_super_admin
from app.models.saas import Tenant, Subscription, SubscriptionPlan, SubscriptionInvoice, PlatformAuditLog
from app.models.organization import Branch, User
from app.models.order import Order
from app.schemas.saas import TenantResponse, TenantUpdate, PlatformMetricsResponse, SubscriptionPlanResponse

router = APIRouter()

@router.get("/metrics", response_model=PlatformMetricsResponse)
def get_platform_metrics(db: Session = Depends(get_db), admin = Depends(get_current_super_admin)):
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.status == "Active").count()
    trial_tenants = db.query(Tenant).filter(Tenant.status == "Trial").count()
    suspended_tenants = db.query(Tenant).filter(Tenant.status == "Suspended").count()
    total_branches = db.query(Branch).count()
    total_orders = db.query(Order).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    # Calculate MRR from active subscriptions
    active_subs = db.query(Subscription).join(SubscriptionPlan).filter(Subscription.status == "Active").all()
    mrr = sum([float(s.plan.monthly_price) for s in active_subs if s.plan])
    arr = mrr * 12.0

    return PlatformMetricsResponse(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        suspended_tenants=suspended_tenants,
        monthly_recurring_revenue=round(mrr, 2),
        annual_recurring_revenue=round(arr, 2),
        total_orders_processed=total_orders,
        total_branches=total_branches,
        active_users=active_users
    )

@router.get("/tenants", response_model=List[TenantResponse])
def list_tenants(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin = Depends(get_current_super_admin)
):
    query = db.query(Tenant)
    if search:
        query = query.filter(Tenant.name.ilike(f"%{search}%") | Tenant.contact_email.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Tenant.status == status_filter)

    tenants = query.order_by(Tenant.created_at.desc()).all()
    res = []
    for t in tenants:
        sub = db.query(Subscription).filter(Subscription.tenant_id == t.id).first()
        plan_name = sub.plan.name if sub and sub.plan else "None"
        branch_count = db.query(Branch).filter(Branch.tenant_id == t.id).count()
        res.append(TenantResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            business_type=t.business_type,
            status=t.status,
            contact_email=t.contact_email,
            contact_phone=t.contact_phone,
            country=t.country,
            currency=t.currency,
            timezone=t.timezone,
            onboarding_completed=t.onboarding_completed,
            onboarding_step=t.onboarding_step,
            created_at=t.created_at,
            plan_name=plan_name,
            branch_count=branch_count
        ))
    return res

@router.put("/tenants/{tenant_id}/status")
def update_tenant_status(
    tenant_id: str,
    status_val: str = Query(..., pattern="^(Active|Suspended|Trial|Deactivated)$"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_super_admin)
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    old_status = tenant.status
    tenant.status = status_val
    
    # Audit event
    log = PlatformAuditLog(
        tenant_id=tenant.id,
        actor_id=admin.id,
        actor_email=admin.email,
        action="TENANT_STATUS_UPDATED",
        entity_type="Tenant",
        entity_id=tenant.id,
        details={"old_status": old_status, "new_status": status_val}
    )
    db.add(log)
    db.commit()
    return {"message": f"Tenant status updated from {old_status} to {status_val}"}

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(db: Session = Depends(get_db)):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

@router.get("/audit-logs")
def list_platform_audit_logs(limit: int = 50, db: Session = Depends(get_db), admin = Depends(get_current_super_admin)):
    logs = db.query(PlatformAuditLog).order_by(PlatformAuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "tenant_id": l.tenant_id,
            "actor_email": l.actor_email,
            "action": l.action,
            "entity_type": l.entity_type,
            "details": l.details,
            "created_at": l.created_at
        }
        for l in logs
    ]
