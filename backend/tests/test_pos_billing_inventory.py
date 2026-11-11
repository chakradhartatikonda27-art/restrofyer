import pytest
from decimal import Decimal
import uuid

from app.models.menu import MenuCategory, MenuItem
from app.models.inventory import InventoryItem, Recipe, RecipeItem
from app.models.crm import Customer, LoyaltyAccount
from app.models.kitchen import KitchenStation, KOT
from app.models.order import Order, Invoice, Payment

def test_pos_order_creation_pricing_and_inventory_depletion(client, db, seed_two_tenants):
    tenant_a = seed_two_tenants["tenant_a"]
    branch_a = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]

    # 1. Setup Kitchen Station
    station = KitchenStation(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        name="Hot Grill & Oven"
    )
    db.add(station)

    # 2. Setup Category & Menu Item
    cat = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_a.id, name="Artisan Pizzas", is_active=True)
    db.add(cat)
    db.flush()

    item = MenuItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        category_id=cat.id,
        name="Classic Margherita",
        base_price=Decimal("400.00"),
        cost_price=Decimal("120.00"),
        tax_rate=Decimal("5.00"),
        is_available=True,
        kitchen_station_id=station.id
    )
    db.add(item)
    db.flush()

    # 3. Setup Raw Material Inventory & Recipe BOM
    cheese = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="Mozzarella Cheese",
        uom="kg",
        current_stock=Decimal("10.000"),
        minimum_stock=Decimal("2.000"),
        cost_per_unit=Decimal("400.00")
    )
    db.add(cheese)
    db.flush()

    # Recipe: 1 Margherita uses 0.200 kg Mozzarella
    recipe = Recipe(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        menu_item_id=item.id,
        yield_portions=1
    )
    db.add(recipe)
    db.flush()

    recipe_item = RecipeItem(
        id=str(uuid.uuid4()),
        recipe_id=recipe.id,
        inventory_item_id=cheese.id,
        quantity=Decimal("0.200"),
        uom="kg"
    )
    db.add(recipe_item)

    # 4. Setup Customer
    customer = Customer(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="John Doe",
        phone="+91 98765 00000",
        total_spend=Decimal("0.00"),
        total_visits=0
    )
    db.add(customer)
    db.flush()

    db.commit()

    # 5. Place POS Order (2x Margherita)
    headers = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}
    order_payload = {
        "order_type": "DineIn",
        "customer_id": customer.id,
        "customer_name": customer.name,
        "customer_phone": customer.phone,
        "discount_amount": 50.0,
        "discount_reason": "Welcome Coupon",
        "items": [
            {
                "menu_item_id": item.id,
                "quantity": 2,
                "modifiers": [],
                "notes": "Extra crispy"
            }
        ]
    }
    res_order = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res_order.status_code == 200, res_order.text
    order_data = res_order.json()
    order_id = order_data["id"]

    # Calculation verification:
    # Subtotal: 2 * 400 = 800
    # Discount: 50
    # Taxable: 750
    # Tax (5% of 750): 37.50
    # Service Charge (0%): 0.00
    # Total: 787.50
    assert order_data["subtotal"] == 800.0
    assert order_data["discount_amount"] == 50.0
    assert order_data["tax_amount"] == 37.5
    assert order_data["total_amount"] == 787.5

    # Verify KOT generation
    kots = db.query(KOT).filter(KOT.order_id == order_id).all()
    assert len(kots) == 1
    assert kots[0].status == "New"
    assert len(kots[0].items) == 1
    assert kots[0].items[0].quantity == 2

    # 6. Process Payment
    payment_payload = {
        "amount": 787.50,
        "payment_method": "Card",
        "payment_reference": "TXN_774920"
    }
    res_pay = client.post(f"/api/v1/invoices/orders/{order_id}/payments", json=payment_payload, headers=headers)
    assert res_pay.status_code == 200
    invoice_data = res_pay.json()
    assert invoice_data["status"] == "Paid"
    assert invoice_data["total_amount"] == 787.50

    # 7. Verify Automatic Recipe BOM Inventory Depletion!
    # Initial stock: 10.000 kg. 2 pizzas * 0.200 kg = 0.400 kg consumed -> Remaining: 9.600 kg
    db.refresh(cheese)
    assert float(cheese.current_stock) == pytest.approx(9.600, rel=1e-3)

    # 8. Verify Customer Loyalty Points Accreditation!
    # Spend 787.50 -> 78 points awarded (1 pt per 10 units)
    loyalty_acc = db.query(LoyaltyAccount).filter(LoyaltyAccount.customer_id == customer.id).first()
    assert loyalty_acc is not None
    assert loyalty_acc.points_balance == 78
