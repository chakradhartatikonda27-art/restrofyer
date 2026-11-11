from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.financial import CashRegister, CashRegisterSession, CashTransaction
from app.schemas.financial import RegisterOpenRequest, RegisterCloseRequest, CashTransactionCreate

def open_register_session(db: Session, tenant_id: str, branch_id: str, open_req: RegisterOpenRequest, current_user) -> CashRegisterSession:
    register = db.query(CashRegister).filter(
        CashRegister.id == open_req.register_id,
        CashRegister.tenant_id == tenant_id,
        CashRegister.branch_id == branch_id
    ).first()
    if not register:
        raise HTTPException(status_code=404, detail="Cash register not found")

    # Check if an open session already exists for this register
    active_session = db.query(CashRegisterSession).filter(
        CashRegisterSession.register_id == register.id,
        CashRegisterSession.status == "Open"
    ).first()
    if active_session:
        raise HTTPException(status_code=400, detail="An open session already exists on this cash register")

    float_amount = Decimal(str(open_req.opening_float))
    session = CashRegisterSession(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=branch_id,
        register_id=register.id,
        cashier_id=current_user.id,
        cashier_name=current_user.full_name,
        opening_float=float_amount,
        cash_sales=Decimal("0.00"),
        cash_in=Decimal("0.00"),
        cash_out=Decimal("0.00"),
        cash_refunds=Decimal("0.00"),
        expected_closing_cash=float_amount,
        status="Open"
    )
    register.status = "Open"
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def add_cash_transaction(db: Session, tenant_id: str, session_id: str, tx_data: CashTransactionCreate, current_user) -> CashTransaction:
    session = db.query(CashRegisterSession).filter(
        CashRegisterSession.id == session_id,
        CashRegisterSession.tenant_id == tenant_id
    ).first()
    if not session or session.status != "Open":
        raise HTTPException(status_code=400, detail="Active open session not found")

    amount = Decimal(str(tx_data.amount))
    tx = CashTransaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        transaction_type=tx_data.transaction_type,
        amount=amount,
        reason=tx_data.reason,
        authorized_by=current_user.full_name
    )
    db.add(tx)

    if tx_data.transaction_type == "CASH_IN":
        session.cash_in += amount
    elif tx_data.transaction_type == "CASH_OUT":
        session.cash_out += amount

    # Recalculate Expected Closing Cash
    session.expected_closing_cash = (
        session.opening_float +
        session.cash_sales +
        session.cash_in -
        session.cash_out -
        session.cash_refunds
    )

    db.commit()
    db.refresh(tx)
    return tx

def close_register_session(db: Session, tenant_id: str, session_id: str, close_req: RegisterCloseRequest, current_user) -> CashRegisterSession:
    session = db.query(CashRegisterSession).filter(
        CashRegisterSession.id == session_id,
        CashRegisterSession.tenant_id == tenant_id
    ).first()
    if not session or session.status != "Open":
        raise HTTPException(status_code=400, detail="Active open session not found")

    actual_cash = Decimal(str(close_req.actual_closing_cash))
    session.actual_closing_cash = actual_cash
    
    # Recalculate expected closing cash
    session.expected_closing_cash = (
        session.opening_float +
        session.cash_sales +
        session.cash_in -
        session.cash_out -
        session.cash_refunds
    )
    
    # Variance = Actual Closing Cash - Expected Closing Cash
    session.variance = actual_cash - session.expected_closing_cash
    session.status = "Closed"
    session.closed_at = datetime.utcnow()
    session.notes = close_req.notes

    # Update Register status
    register = db.query(CashRegister).filter(CashRegister.id == session.register_id).first()
    if register:
        register.status = "Closed"

    db.commit()
    db.refresh(session)
    return session
