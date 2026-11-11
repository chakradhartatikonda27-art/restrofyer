from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.financial import CashRegister, CashRegisterSession, CashTransaction
from app.schemas.financial import (
    RegisterOpenRequest, RegisterCloseRequest, CashTransactionCreate,
    CashTransactionResponse, CashSessionResponse
)
from app.services.cash_register_service import (
    open_register_session, add_cash_transaction, close_register_session
)

router = APIRouter()

@router.get("", response_model=List[dict])
def list_cash_registers(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    registers = db.query(CashRegister).filter(
        CashRegister.tenant_id == current_user.tenant_id,
        CashRegister.branch_id == branch_id
    ).all()
    return [{"id": r.id, "name": r.name, "status": r.status} for r in registers]

@router.get("/active-session", response_model=CashSessionResponse)
def get_active_session(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CashRegisterSession).filter(
        CashRegisterSession.tenant_id == current_user.tenant_id,
        CashRegisterSession.branch_id == branch_id,
        CashRegisterSession.status == "Open"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="No active cash register session")

    # Refresh expected closing cash dynamically
    session.expected_closing_cash = (
        session.opening_float +
        session.cash_sales +
        session.cash_in -
        session.cash_out -
        session.cash_refunds
    )
    return session

@router.post("/open", response_model=CashSessionResponse)
def open_register(
    data: RegisterOpenRequest,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.OPERATE_CASH_REGISTER)),
    db: Session = Depends(get_db)
):
    session = open_register_session(db, current_user.tenant_id, branch_id, data, current_user)
    return session

@router.post("/sessions/{session_id}/transactions", response_model=CashTransactionResponse)
def cash_in_out(
    session_id: str,
    data: CashTransactionCreate,
    current_user = Depends(require_permission(Permission.OPERATE_CASH_REGISTER)),
    db: Session = Depends(get_db)
):
    tx = add_cash_transaction(db, current_user.tenant_id, session_id, data, current_user)
    return tx

@router.post("/sessions/{session_id}/close", response_model=CashSessionResponse)
def close_register(
    session_id: str,
    data: RegisterCloseRequest,
    current_user = Depends(require_permission(Permission.RECONCILE_CASH_REGISTER)),
    db: Session = Depends(get_db)
):
    session = close_register_session(db, current_user.tenant_id, session_id, data, current_user)
    return session
