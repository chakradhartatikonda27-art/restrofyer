import pytest
from decimal import Decimal
import uuid

from app.models.menu import MenuCategory, MenuItem
from app.models.inventory import InventoryItem
from app.models.crm import Customer

def test_tenant_isolation_branches(client, seed_two_tenants):
    token_a = seed_two_tenants["token_a"]
    token_b = seed_two_tenants["token_b"]
    branch_a_name = seed_two_tenants["branch_a"].name
    branch_b_name = seed_two_tenants["branch_b"].name

    # Tenant A requests branches
    res_a = client.get("/api/v1/branches", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    names_a = [b["name"] for b in res_a.json()]
    assert branch_a_name in names_a
    assert branch_b_name not in names_a # Tenant B's branch must NOT be visible

    # Tenant B requests branches
    res_b = client.get("/api/v1/branches", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    names_b = [b["name"] for b in res_b.json()]
    assert branch_b_name in names_b
    assert branch_a_name not in names_b # Tenant A's branch must NOT be visible

def test_tenant_cannot_read_or_update_other_tenant_customer(client, db, seed_two_tenants):
    tenant_b = seed_two_tenants["tenant_b"]
    token_a = seed_two_tenants["token_a"]

    # Create customer belonging to Tenant B
    cust_b = Customer(
        id=str(uuid.uuid4()),
        tenant_id=tenant_b.id,
        name="Private Client B",
        phone="+91 99999 88888",
        total_spend=Decimal("5000.00"),
        total_visits=2
    )
    db.add(cust_b)
    db.commit()

    # Tenant A attempts to list customers
    res_a = client.get("/api/v1/crm", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    cust_ids = [c["id"] for c in res_a.json()]
    assert cust_b.id not in cust_ids

def test_tenant_cannot_see_other_tenant_inventory(client, db, seed_two_tenants):
    tenant_b = seed_two_tenants["tenant_b"]
    token_a = seed_two_tenants["token_a"]

    # Create secret raw material for Tenant B
    item_b = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_b.id,
        name="Secret Saffron Reserve",
        sku="SKU-B-SAFFRON",
        uom="g",
        current_stock=Decimal("50.000"),
        minimum_stock=Decimal("10.000"),
        cost_per_unit=Decimal("500.00")
    )
    db.add(item_b)
    db.commit()

    # Tenant A requests inventory
    res_a = client.get("/api/v1/inventory/items", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    item_names = [i["name"] for i in res_a.json()]
    assert "Secret Saffron Reserve" not in item_names

def test_missing_auth_denies_access(client):
    res = client.get("/api/v1/orders")
    assert res.status_code == 401
