from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.order import Invoice, Payment, Refund, Order
from app.schemas.order import InvoiceResponse, PaymentCreate, RefundCreate
from app.services.pos_service import process_order_payment

router = APIRouter()

@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id,
        Invoice.branch_id == branch_id
    ).order_by(Invoice.created_at.desc()).limit(100).all()

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/orders/{order_id}/payments", response_model=InvoiceResponse)
def pay_order(
    order_id: str,
    data: PaymentCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.PROCESS_PAYMENT)),
    db: Session = Depends(get_db)
):
    invoice = process_order_payment(db, current_user.tenant_id, branch_id, order_id, data, current_user)
    return invoice

@router.post("/refunds")
def process_refund(
    data: RefundCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.PROCESS_REFUND)),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(
        Payment.id == data.payment_id,
        Payment.tenant_id == current_user.tenant_id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    refund_amt = Decimal(str(data.amount))
    if refund_amt > payment.amount:
        raise HTTPException(status_code=400, detail="Refund amount exceeds initial payment amount")

    refund = Refund(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        payment_id=payment.id,
        invoice_id=payment.invoice_id,
        amount=refund_amt,
        reason=data.reason,
        authorized_by=current_user.full_name
    )
    db.add(refund)
    payment.status = "Refunded"

    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if invoice:
        invoice.status = "Refunded"

    db.commit()
    return {"message": "Refund processed successfully", "refund_id": refund.id}
