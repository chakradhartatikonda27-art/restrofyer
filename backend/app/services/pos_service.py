from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.organization import Branch, AuditLog
from app.models.menu import MenuItem, ItemVariant, ItemModifier, MenuItemBranchConfig, ComboMealItem
from app.models.table import RestaurantTable
from app.models.order import Order, OrderItem, Invoice, Payment, Refund
from app.models.kitchen import KOT, KOTItem
from app.models.inventory import Recipe, RecipeItem, InventoryItem, StockMovement
from app.models.crm import Customer, LoyaltyAccount, LoyaltyTransaction
from app.models.financial import CashRegisterSession
from app.schemas.order import OrderCreate, PaymentCreate

def generate_order_number(db: Session, tenant_id: str, branch_id: str) -> str:
    count = db.query(Order).filter(Order.tenant_id == tenant_id).count()
    return f"ORD-{datetime.utcnow().strftime('%y%m%d')}-{count + 1:04d}"

def generate_invoice_number(db: Session, tenant_id: str) -> str:
    count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id).count()
    return f"INV-{datetime.utcnow().strftime('%y%m%d')}-{count + 1:04d}"

def generate_kot_number(db: Session, tenant_id: str) -> str:
    count = db.query(KOT).filter(KOT.tenant_id == tenant_id).count()
    return f"KOT-{count + 1:04d}"

def create_pos_order(db: Session, tenant_id: str, branch_id: str, order_data: OrderCreate, current_user) -> Order:
    # 1. Fetch branch for tax and service charge rates
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == tenant_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    table_number = None
    if order_data.table_id:
        table = db.query(RestaurantTable).filter(
            RestaurantTable.id == order_data.table_id,
            RestaurantTable.tenant_id == tenant_id
        ).first()
        if table:
            table_number = table.table_number
            table.status = "Occupied"
            table.occupied_since = datetime.utcnow()

    # 2. Build order items and calculate totals
    subtotal = Decimal("0.00")
    order_items_to_create = []
    station_routing_map = {} # station_id -> list of items

    for item_in in order_data.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item_in.menu_item_id,
            MenuItem.tenant_id == tenant_id
        ).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {item_in.menu_item_id} not found")

        branch_cfg = db.query(MenuItemBranchConfig).filter(
            MenuItemBranchConfig.menu_item_id == menu_item.id,
            MenuItemBranchConfig.branch_id == branch_id,
            MenuItemBranchConfig.tenant_id == tenant_id,
        ).first()
        effective_available = branch_cfg.is_available if branch_cfg else menu_item.is_available
        if not effective_available:
            raise HTTPException(status_code=400, detail=f"Menu item '{menu_item.name}' is currently unavailable at this branch")

        # Price calculation with branch-specific pricing, variant & modifiers
        unit_price = (
            Decimal(str(branch_cfg.branch_price))
            if (branch_cfg and branch_cfg.branch_price is not None)
            else Decimal(str(menu_item.base_price))
        )
        variant_name = None
        if item_in.variant_id:
            variant = db.query(ItemVariant).filter(ItemVariant.id == item_in.variant_id).first()
            if variant:
                unit_price = Decimal(str(variant.price))
                variant_name = variant.name

        modifiers_snapshot = []
        for mod in item_in.modifiers:
            mod_price = Decimal(str(mod.price))
            unit_price += mod_price
            modifiers_snapshot.append({"name": mod.name, "price": float(mod_price)})

        item_subtotal = unit_price * item_in.quantity
        subtotal += item_subtotal

        order_item = OrderItem(
            id=str(uuid.uuid4()),
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            unit_price=unit_price,
            cost_price=Decimal(str(menu_item.cost_price)),
            quantity=item_in.quantity,
            subtotal=item_subtotal,
            tax_rate=Decimal(str(menu_item.tax_rate)) if menu_item.tax_rate is not None else Decimal(str(branch.tax_rate or 5.00)),
            variant_id=item_in.variant_id,
            variant_name=variant_name,
            modifiers=modifiers_snapshot,
            notes=item_in.notes
        )
        order_items_to_create.append(order_item)

        # Map to kitchen station for KOT routing
        station_id = menu_item.kitchen_station_id or "default"
        station_routing_map.setdefault(station_id, []).append(order_item)

    discount_amount = Decimal(str(order_data.discount_amount or 0.00))
    taxable_amount = max(Decimal("0.00"), subtotal - discount_amount)
    branch_tax_rate = Decimal(str(branch.tax_rate or 5.00))
    if subtotal > Decimal("0.00") and order_items_to_create:
        weighted_tax = sum(
            (oi.subtotal / subtotal) * taxable_amount * (oi.tax_rate / Decimal("100.00"))
            for oi in order_items_to_create
        )
        tax_amount = round(weighted_tax, 2)
    else:
        tax_amount = round((taxable_amount * branch_tax_rate) / Decimal("100.00"), 2)
    service_charge_rate = Decimal(str(branch.service_charge_rate or 0.00))
    service_charge = round((taxable_amount * service_charge_rate) / Decimal("100.00"), 2)
    total_amount = taxable_amount + tax_amount + service_charge

    # 3. Create Order
    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=branch_id,
        order_number=generate_order_number(db, tenant_id, branch_id),
        order_type=order_data.order_type,
        status="InKitchen",
        table_id=order_data.table_id,
        table_number=table_number,
        customer_id=order_data.customer_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        subtotal=subtotal,
        discount_amount=discount_amount,
        discount_reason=order_data.discount_reason,
        tax_amount=tax_amount,
        service_charge=service_charge,
        total_amount=total_amount,
        cashier_id=current_user.id,
        cashier_name=current_user.full_name,
        notes=order_data.notes
    )
    db.add(order)
    db.flush()

    # Attach order items
    for oi in order_items_to_create:
        oi.order_id = order.id
        db.add(oi)
    db.flush()

    # 4. Generate KOTs routed by Kitchen Station
    for station_id, items in station_routing_map.items():
        actual_station_id = None if station_id == "default" else station_id
        kot = KOT(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            order_id=order.id,
            kitchen_station_id=actual_station_id,
            kot_number=generate_kot_number(db, tenant_id),
            status="New",
            waiter_name=current_user.full_name,
            notes=order_data.notes
        )
        db.add(kot)
        db.flush()

        for oi in items:
            mods_summary = ", ".join([m["name"] for m in oi.modifiers]) if oi.modifiers else None
            kot_item = KOTItem(
                id=str(uuid.uuid4()),
                kot_id=kot.id,
                order_item_id=oi.id,
                item_name=oi.item_name,
                variant_name=oi.variant_name,
                modifiers_summary=mods_summary,
                quantity=oi.quantity,
                notes=oi.notes,
                status="New"
            )
            db.add(kot_item)

    if order_data.table_id and table:
        table.active_order_id = order.id

    db.commit()
    db.refresh(order)
    return order

def process_order_payment(db: Session, tenant_id: str, branch_id: str, order_id: str, payment_data: PaymentCreate, current_user) -> Invoice:
    order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 1. Create or retrieve Invoice
    invoice = db.query(Invoice).filter(Invoice.order_id == order.id).first()
    if not invoice:
        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            order_id=order.id,
            invoice_number=generate_invoice_number(db, tenant_id),
            subtotal=order.subtotal,
            discount=order.discount_amount,
            tax=order.tax_amount,
            service_charge=order.service_charge,
            total_amount=order.total_amount,
            paid_amount=Decimal("0.00"),
            status="Unpaid"
        )
        db.add(invoice)
        db.flush()

    payment_amt = Decimal(str(payment_data.amount))
    
    # Check open cash register session for cashier
    cash_session = None
    if payment_data.payment_method == "Cash":
        cash_session = db.query(CashRegisterSession).filter(
            CashRegisterSession.tenant_id == tenant_id,
            CashRegisterSession.branch_id == branch_id,
            CashRegisterSession.status == "Open"
        ).first()

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=branch_id,
        invoice_id=invoice.id,
        order_id=order.id,
        amount=payment_amt,
        payment_method=payment_data.payment_method,
        payment_reference=payment_data.payment_reference,
        status="Success",
        cash_register_session_id=cash_session.id if cash_session else None
    )
    db.add(payment)

    invoice.paid_amount += payment_amt
    if invoice.paid_amount >= invoice.total_amount:
        invoice.status = "Paid"
        order.status = "Completed"
        
        # Free table if DineIn
        if order.table_id:
            table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first()
            if table:
                table.status = "Cleaning"
                table.active_order_id = None
                table.occupied_since = None

        # 2. Trigger automatic inventory consumption from Recipe BOM!
        deplete_inventory_from_order(db, tenant_id, branch_id, order)

        # 3. Update customer spend & loyalty points
        if order.customer_id:
            update_customer_loyalty(db, tenant_id, order.customer_id, order)

    else:
        invoice.status = "PartiallyPaid"

    # Update cash register session total if cash payment
    if cash_session and payment_data.payment_method == "Cash":
        cash_session.cash_sales += payment_amt
        cash_session.expected_closing_cash = (
            cash_session.opening_float + 
            cash_session.cash_sales + 
            cash_session.cash_in - 
            cash_session.cash_out - 
            cash_session.cash_refunds
        )

    db.commit()
    db.refresh(invoice)
    return invoice

def _deplete_recipe_for_item(
    db: Session,
    tenant_id: str,
    branch_id: str,
    menu_item_id: str,
    portions_ordered: Decimal,
    order_number: str,
    notes: str,
):
    recipe = db.query(Recipe).filter(Recipe.menu_item_id == menu_item_id).first()
    if not recipe or not recipe.items:
        return
    recipe_yield = Decimal(str(recipe.yield_portions or 1))
    for r_item in recipe.items:
        qty_per_portion = Decimal(str(r_item.quantity))
        total_depletion = (qty_per_portion * portions_ordered) / recipe_yield
        inv_item = db.query(InventoryItem).filter(
            InventoryItem.id == r_item.inventory_item_id,
            InventoryItem.tenant_id == tenant_id
        ).first()
        if inv_item:
            inv_item.current_stock -= total_depletion
            db.add(StockMovement(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                inventory_item_id=inv_item.id,
                movement_type="SALES_CONSUMPTION",
                quantity=-total_depletion,
                unit_cost=inv_item.cost_per_unit,
                reference_id=order_number,
                notes=notes,
            ))


def deplete_inventory_from_order(db: Session, tenant_id: str, branch_id: str, order: Order):
    """Calculates recipe BOM ingredient consumption (including combo components) and deducts from inventory balances."""
    for item in order.items:
        portions = Decimal(str(item.quantity))
        _deplete_recipe_for_item(
            db,
            tenant_id,
            branch_id,
            item.menu_item_id,
            portions,
            order.order_number,
            f"Order fulfillment: {item.quantity}x {item.item_name}",
        )
        combo_components = db.query(ComboMealItem).filter(
            ComboMealItem.combo_item_id == item.menu_item_id,
            ComboMealItem.tenant_id == tenant_id,
        ).all()
        for cc in combo_components:
            comp_portions = portions * Decimal(str(cc.quantity or 1))
            _deplete_recipe_for_item(
                db,
                tenant_id,
                branch_id,
                cc.component_item_id,
                comp_portions,
                order.order_number,
                f"Order fulfillment combo ({item.item_name}): {comp_portions}x component",
            )

def update_customer_loyalty(db: Session, tenant_id: str, customer_id: str, order: Order):
    """Accredits ledger points (1 point per 10 currency spent) and updates customer metrics."""
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        return
        
    customer.total_spend += order.total_amount
    customer.total_visits += 1
    customer.last_visit_at = datetime.utcnow()
    
    # Segmentation logic
    if customer.total_spend > Decimal("5000.00"):
        customer.segment = "VIP"
    elif customer.total_visits > 3:
        customer.segment = "Returning"

    # Loyalty ledger entry
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.customer_id == customer.id).first()
    if not account:
        account = LoyaltyAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=customer.id,
            tier="Silver",
            points_balance=0
        )
        db.add(account)
        db.flush()

    earned_points = int(order.total_amount // Decimal("10.00")) # 1 pt per 10 units
    if earned_points > 0:
        account.points_balance += earned_points
        if account.points_balance >= 500:
            account.tier = "Platinum"
        elif account.points_balance >= 200:
            account.tier = "Gold"

        ledger_tx = LoyaltyTransaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            account_id=account.id,
            transaction_type="EARN",
            points=earned_points,
            running_balance=account.points_balance,
            order_id=order.id,
            reason=f"Earned on Order {order.order_number}"
        )
        db.add(ledger_tx)
