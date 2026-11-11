from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.crm import Customer, LoyaltyAccount, LoyaltyTransaction
from app.schemas.crm import LoyaltyTransactionCreate

router = APIRouter()

@router.get("/customers/{customer_id}/transactions")
def get_loyalty_transactions(
    customer_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(LoyaltyAccount).filter(
        LoyaltyAccount.customer_id == customer_id,
        LoyaltyAccount.tenant_id == current_user.tenant_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Loyalty account not found")

    txs = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.account_id == account.id
    ).order_by(LoyaltyTransaction.created_at.desc()).all()

    return {
        "account_id": account.id,
        "points_balance": account.points_balance,
        "tier": account.tier,
        "transactions": [
            {
                "id": t.id,
                "type": t.transaction_type,
                "points": t.points,
                "running_balance": t.running_balance,
                "reason": t.reason,
                "created_at": t.created_at
            }
            for t in txs
        ]
    }

@router.post("/customers/{customer_id}/adjust")
def adjust_loyalty_points(
    customer_id: str,
    data: LoyaltyTransactionCreate,
    current_user = Depends(require_permission(Permission.MANAGE_LOYALTY)),
    db: Session = Depends(get_db)
):
    account = db.query(LoyaltyAccount).filter(
        LoyaltyAccount.customer_id == customer_id,
        LoyaltyAccount.tenant_id == current_user.tenant_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Loyalty account not found")

    account.points_balance += data.points
    if account.points_balance < 0:
        account.points_balance = 0

    tx = LoyaltyTransaction(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        account_id=account.id,
        transaction_type="ADJUSTMENT",
        points=data.points,
        running_balance=account.points_balance,
        reason=data.reason
    )
    db.add(tx)
    db.commit()
    return {"message": "Loyalty balance adjusted", "new_balance": account.points_balance}
