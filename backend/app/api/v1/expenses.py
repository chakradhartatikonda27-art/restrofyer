from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.financial import Expense
from app.schemas.financial import ExpenseCreate, ExpenseResponse

router = APIRouter()

@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Expense).filter(
        Expense.tenant_id == current_user.tenant_id,
        Expense.branch_id == branch_id
    ).order_by(Expense.expense_date.desc()).all()

@router.post("", response_model=ExpenseResponse)
def create_expense(
    data: ExpenseCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_EXPENSES)),
    db: Session = Depends(get_db)
):
    exp = Expense(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        category=data.category,
        amount=Decimal(str(data.amount)),
        payment_method=data.payment_method,
        payee=data.payee,
        notes=data.notes
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp
