import pytest
from decimal import Decimal
import uuid

from app.models.kitchen import KitchenStation, KOT, KOTItem
from app.models.order import Order

def test_kds_status_pipeline_transitions(client, db, seed_two_tenants):
    tenant_a = seed_two_tenants["tenant_a"]
    branch_a = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]

    headers = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}

    # Setup Order & KOT
    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        order_number="ORD-TEST-0099",
        order_type="DineIn",
        status="InKitchen",
        table_number="T-01"
    )
    db.add(order)
    db.flush()

    kot = KOT(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        order_id=order.id,
        kot_number="KOT-9999",
        status="New",
        waiter_name="Test Waiter"
    )
    db.add(kot)
    db.flush()

    kot_item = KOTItem(
        id=str(uuid.uuid4()),
        kot_id=kot.id,
        order_item_id="OI-1",
        item_name="Penne Arbiatta",
        quantity=1,
        status="New"
    )
    db.add(kot_item)
    db.commit()

    # 1. Transition to Preparing
    res_prep = client.patch(f"/api/v1/kitchens/kots/{kot.id}/status", json={"status": "Preparing"}, headers=headers)
    assert res_prep.status_code == 200
    assert res_prep.json()["status"] == "Preparing"
    assert res_prep.json()["started_preparing_at"] is not None

    # 2. Transition to Ready
    res_ready = client.patch(f"/api/v1/kitchens/kots/{kot.id}/status", json={"status": "Ready"}, headers=headers)
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "Ready"
    assert res_ready.json()["ready_at"] is not None

    # 3. Transition to Served
    res_served = client.patch(f"/api/v1/kitchens/kots/{kot.id}/status", json={"status": "Served"}, headers=headers)
    assert res_served.status_code == 200
    assert res_served.json()["status"] == "Served"
