from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, get_active_branch_id, require_permission
from app.core.permissions import Permission
from app.models.procurement import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt
from app.models.inventory import InventoryItem, StockMovement
from app.schemas.procurement import (
    SupplierCreate, SupplierResponse,
    PurchaseOrderCreate, PurchaseOrderResponse, GoodsReceiptCreate
)

router = APIRouter()

@router.get("/suppliers", response_model=List[SupplierResponse])
def list_suppliers(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.tenant_id == current_user.tenant_id).order_by(Supplier.name.asc()).all()

@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(
    data: SupplierCreate,
    current_user = Depends(require_permission(Permission.MANAGE_SUPPLIERS)),
    db: Session = Depends(get_db)
):
    sup = Supplier(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=data.name,
        contact_name=data.contact_name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        tax_number=data.tax_number,
        payment_terms=data.payment_terms
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return sup

@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == current_user.tenant_id,
        PurchaseOrder.branch_id == branch_id
    ).order_by(PurchaseOrder.created_at.desc()).all()

@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
def create_purchase_order(
    data: PurchaseOrderCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_PURCHASES)),
    db: Session = Depends(get_db)
):
    po_count = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == current_user.tenant_id).count()
    po_number = f"PO-{datetime.utcnow().strftime('%y%m')}-{po_count + 1:04d}"

    total_amt = Decimal("0.00")
    items_to_create = []

    for item_in in data.items:
        line_total = Decimal(str(item_in.quantity)) * Decimal(str(item_in.unit_price))
        total_amt += line_total
        po_item = PurchaseOrderItem(
            id=str(uuid.uuid4()),
            inventory_item_id=item_in.inventory_item_id,
            item_name=item_in.item_name,
            quantity=Decimal(str(item_in.quantity)),
            unit_price=Decimal(str(item_in.unit_price)),
            total_price=line_total
        )
        items_to_create.append(po_item)

    po = PurchaseOrder(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        supplier_id=data.supplier_id,
        po_number=po_number,
        status="Submitted",
        total_amount=total_amt,
        expected_delivery_date=data.expected_delivery_date,
        notes=data.notes
    )
    db.add(po)
    db.flush()

    for item in items_to_create:
        item.po_id = po.id
        db.add(item)

    db.commit()
    db.refresh(po)
    return po

@router.post("/goods-receipts")
def receive_goods(
    data: GoodsReceiptCreate,
    branch_id: str = Depends(get_active_branch_id),
    current_user = Depends(require_permission(Permission.MANAGE_PURCHASES)),
    db: Session = Depends(get_db)
):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == data.po_id,
        PurchaseOrder.tenant_id == current_user.tenant_id
    ).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    grn_count = db.query(GoodsReceipt).filter(GoodsReceipt.tenant_id == current_user.tenant_id).count()
    grn_number = f"GRN-{datetime.utcnow().strftime('%y%m')}-{grn_count + 1:04d}"

    grn = GoodsReceipt(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        po_id=po.id,
        grn_number=grn_number,
        received_by=current_user.full_name,
        notes=data.notes
    )
    db.add(grn)

    # Automatically replenish inventory stock & log stock movements!
    for po_item in po.items:
        inv_item = db.query(InventoryItem).filter(InventoryItem.id == po_item.inventory_item_id).first()
        if inv_item:
            inv_item.current_stock += po_item.quantity
            # Update weighted average cost
            inv_item.cost_per_unit = po_item.unit_price
            
            movement = StockMovement(
                id=str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                branch_id=branch_id,
                inventory_item_id=inv_item.id,
                movement_type="PURCHASE_RECEIPT",
                quantity=po_item.quantity,
                unit_cost=po_item.unit_price,
                reference_id=grn_number,
                notes=f"Goods Receipt from {po.po_number}",
                created_by=current_user.full_name
            )
            db.add(movement)

    po.status = "Received"
    db.commit()
    return {"message": "Goods received successfully and stock balances updated", "grn_number": grn_number}
