from decimal import Decimal
import uuid

from app.core.security import create_access_token
from app.models.organization import Branch
from seed_data import seed_spice_symphony_menus, seed_spice_symphony_full_operations


def test_spice_symphony_full_operational_seed_end_to_end(client, db, seed_two_tenants):
    tenant = seed_two_tenants["tenant_a"]
    branch_1 = seed_two_tenants["branch_a"]
    owner = seed_two_tenants["user_a"]
    branch_2 = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name="Branch A2",
        code="A-02",
        address="202 Second St",
        tax_rate=Decimal("5.00"),
        is_active=True,
    )
    db.add(branch_2)
    db.commit()

    # Seed menu + operational data twice to verify strict idempotency
    seed_spice_symphony_menus(db, tenant.id, branch_1.id)
    seed_spice_symphony_full_operations(db, tenant.id, branch_1.id, branch_2.id, owner)
    seed_spice_symphony_menus(db, tenant.id, branch_1.id)
    seed_spice_symphony_full_operations(db, tenant.id, branch_1.id, branch_2.id, owner)
    db.commit()

    token = create_access_token(subject=owner.id, tenant_id=tenant.id, role=owner.role, branch_id=branch_1.id)
    headers = {"Authorization": f"Bearer {token}", "X-Branch-Id": branch_1.id}

    sales = client.get("/api/v1/reports/sales", headers=headers)
    assert sales.status_code == 200
    sales_json = sales.json()
    assert sales_json["total_orders"] == 8
    assert sales_json["total_sales"] > 0
    assert len(sales_json["daily_sales_trend"]) == 7
    assert len(sales_json["top_selling_items"]) >= 3

    pnl = client.get("/api/v1/reports/profit-loss", headers=headers)
    assert pnl.status_code == 200
    assert pnl.json()["total_revenue"] > 0
    assert pnl.json()["total_operating_expenses"] > 0

    orders = client.get("/api/v1/orders", headers=headers)
    assert orders.status_code == 200
    assert len(orders.json()) == 11

    kots = client.get("/api/v1/kitchens/kots", headers=headers)
    assert kots.status_code == 200
    assert len(kots.json()) >= 3

    low_stock = client.get("/api/v1/inventory/items?low_stock_only=true", headers=headers)
    assert low_stock.status_code == 200
    assert len(low_stock.json()) == 2

    items_res = client.get("/api/v1/menus/items", headers=headers)
    assert items_res.status_code == 200
    items_json = items_res.json()
    assert len(items_json) == 30
    assert len({it["image_url"] for it in items_json if it.get("image_url")}) == 30
    by_name = {it["name"]: it for it in items_json}
    assert by_name["Idli (2 Pcs)"]["image_url"] == "/images/dishes/idli.jpg"
    assert by_name["Paneer Tikka"]["image_url"] == "/images/dishes/paneer-tikka.jpg"
    assert by_name["Butter Naan"]["image_url"] == "/images/dishes/butter-naan.jpg"
    assert by_name["Madras Filter Coffee"]["image_url"] == "/images/dishes/filter-coffee.jpg"

    first_item_id = items_json[0]["id"]
    first_recipe = client.get(f"/api/v1/recipes/{first_item_id}", headers=headers)
    assert first_recipe.status_code == 200
    assert len(first_recipe.json()["items"]) >= 1

    assert len(client.get("/api/v1/tables", headers=headers).json()) == 6
    assert len(client.get("/api/v1/reservations", headers=headers).json()) == 4
    assert len(client.get("/api/v1/procurement/suppliers", headers=headers).json()) == 3
    assert len(client.get("/api/v1/procurement/purchase-orders", headers=headers).json()) == 2
    assert len(client.get("/api/v1/crm", headers=headers).json()) == 5
    assert client.get("/api/v1/cash-registers/active-session", headers=headers).status_code == 200
    assert len(client.get("/api/v1/delivery/orders", headers=headers).json()) == 3
    assert len(client.get("/api/v1/users", headers=headers).json()) >= 5

    # Verify second branch also has live data when switching active branch header
    b2_headers = {"Authorization": f"Bearer {token}", "X-Branch-Id": branch_2.id}
    assert client.get("/api/v1/reports/sales", headers=b2_headers).json()["total_orders"] == 2
    assert len(client.get("/api/v1/kitchens/kots", headers=b2_headers).json()) >= 1
    assert client.get("/api/v1/cash-registers/active-session", headers=b2_headers).status_code == 200
