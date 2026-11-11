import uuid
from decimal import Decimal

from app.models.organization import Branch
from app.models.table import DiningArea, RestaurantTable
from app.models.inventory import InventoryItem, Recipe, RecipeItem


def test_menu_crud_and_tenant_isolation(client, db, seed_two_tenants):
    token_a = seed_two_tenants["token_a"]
    branch_a = seed_two_tenants["branch_a"]
    token_b = seed_two_tenants["token_b"]

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Create a Menu for Tenant A
    res_create = client.post(
        "/api/v1/menus",
        json={"name": "Veg Curries", "description": "Andhra specials", "display_order": 1},
        headers=headers_a,
    )
    assert res_create.status_code == 200, res_create.text
    menu_a = res_create.json()
    assert menu_a["name"] == "Veg Curries"
    assert menu_a["item_count"] == 0

    # 2. Tenant B cannot see or mutate Tenant A's menu
    res_list_b = client.get("/api/v1/menus", headers=headers_b)
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0

    res_update_b = client.put(
        f"/api/v1/menus/{menu_a['id']}",
        json={"name": "Hacked"},
        headers=headers_b,
    )
    assert res_update_b.status_code == 404

    res_delete_b = client.delete(f"/api/v1/menus/{menu_a['id']}", headers=headers_b)
    assert res_delete_b.status_code == 404

    # 3. Tenant A updates menu
    res_update_a = client.put(
        f"/api/v1/menus/{menu_a['id']}",
        json={"name": "Veg Curries Deluxe"},
        headers=headers_a,
    )
    assert res_update_a.status_code == 200
    assert res_update_a.json()["name"] == "Veg Curries Deluxe"


def test_menu_items_customer_site_visibility_modifiers_and_csv_bulk(client, db, seed_two_tenants):
    tenant_a = seed_two_tenants["tenant_a"]
    branch_a = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}

    # Create second branch for Tenant A to test Copy Between Branches
    branch_a2 = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="Branch A2",
        code="A-02",
        address="200 Gamma St",
        tax_rate=Decimal("5.00"),
        is_active=True,
    )
    db.add(branch_a2)

    # Create Dining Area + Table for Assign Menu to Table
    area = DiningArea(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        name="Main Hall",
        display_order=1,
    )
    db.add(area)
    db.flush()

    tbl = RestaurantTable(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        area_id=area.id,
        table_number="T-01",
        name="Window 1",
        capacity=4,
        status="Available",
        qr_code_token="QR-TEST-A1",
    )
    db.add(tbl)
    db.commit()

    # 1. Create Menu & Category
    menu = client.post(
        "/api/v1/menus",
        json={"name": "Veg Curries", "display_order": 1},
        headers=headers_a,
    ).json()

    cat = client.post(
        "/api/v1/menus/categories",
        json={"name": "Curries", "menu_id": menu["id"], "display_order": 1},
        headers=headers_a,
    ).json()

    # 2. Create Item 1 (Visible on customer site) & Item 2 (Hidden on customer site)
    item1 = client.post(
        "/api/v1/menus/items",
        json={
            "menu_id": menu["id"],
            "category_id": cat["id"],
            "name": "Gutti Vankaya",
            "description": "Stuffed brinjals",
            "base_price": 150.0,
            "is_veg": True,
            "is_available": True,
            "show_on_customer_site": True,
        },
        headers=headers_a,
    ).json()

    item2 = client.post(
        "/api/v1/menus/items",
        json={
            "menu_id": menu["id"],
            "category_id": cat["id"],
            "name": "Pappu Charu",
            "description": "Telugu authentic food",
            "base_price": 30.0,
            "is_veg": True,
            "is_available": True,
            "show_on_customer_site": True,
        },
        headers=headers_a,
    ).json()

    # Toggle show_on_customer_site off for item2
    res_toggle = client.patch(
        f"/api/v1/menus/items/{item2['id']}/toggle-customer-site",
        headers=headers_a,
    )
    assert res_toggle.status_code == 200
    assert res_toggle.json()["show_on_customer_site"] is False

    # Verify public storefront hides item2 while preserving item1
    public_res = client.get(f"/api/v1/public/{tenant_a.slug}/menu")
    assert public_res.status_code == 200
    public_names = [
        it["name"]
        for c in public_res.json()["categories"]
        for it in c["items"]
    ]
    assert "Gutti Vankaya" in public_names
    assert "Pappu Charu" not in public_names

    # 3. Assign Menu to Table & verify QR lookup reflects assigned_menu_id
    res_assign = client.post(
        f"/api/v1/menus/{menu['id']}/assign-tables",
        json={"table_ids": [tbl.id]},
        headers=headers_a,
    )
    assert res_assign.status_code == 200
    assert tbl.id in res_assign.json()["assigned_table_ids"]

    qr_res = client.get("/api/v1/public/table/QR-TEST-A1")
    assert qr_res.status_code == 200
    assert qr_res.json()["assigned_menu_id"] == menu["id"]

    # 4. Modifier Group & Item Modifier CRUD
    mg_res = client.post(
        "/api/v1/menus/modifier-groups",
        json={
            "item_id": item1["id"],
            "name": "Spice Level",
            "min_selection": 1,
            "max_selection": 1,
            "modifiers": [{"name": "Extra Guntur", "price": 15.0}],
        },
        headers=headers_a,
    )
    assert mg_res.status_code == 200
    mg = mg_res.json()
    assert len(mg["modifiers"]) == 1

    mod_add = client.post(
        "/api/v1/menus/modifiers",
        json={"group_id": mg["id"], "name": "Mild Spice", "price": 0.0},
        headers=headers_a,
    )
    assert mod_add.status_code == 200
    mod_id = mod_add.json()["id"]

    mod_toggle = client.patch(
        f"/api/v1/menus/modifiers/{mod_id}/toggle-availability",
        headers=headers_a,
    )
    assert mod_toggle.status_code == 200
    assert mod_toggle.json()["is_available"] is False

    # 5. Reorder Items
    res_reorder = client.put(
        "/api/v1/menus/items/reorder",
        json={
            "items": [
                {"id": item2["id"], "display_order": 0},
                {"id": item1["id"], "display_order": 1},
            ]
        },
        headers=headers_a,
    )
    assert res_reorder.status_code == 200
    ordered_items = client.get(f"/api/v1/menus/items?menu_id={menu['id']}", headers=headers_a).json()
    assert ordered_items[0]["id"] == item2["id"]
    assert ordered_items[1]["id"] == item1["id"]

    # 6. Bulk Upload & CSV Export
    bulk_res = client.post(
        "/api/v1/menus/items/bulk-upload",
        json={
            "default_menu_id": menu["id"],
            "items": [
                {
                    "name": "Mushroom cashew",
                    "description": "Soft mushrooms and crunchy cashews",
                    "base_price": 15.0,
                    "category_name": "Veg",
                    "menu_name": "Veg Curries",
                    "is_veg": True,
                }
            ],
        },
        headers=headers_a,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["created_count"] == 1

    csv_res = client.get("/api/v1/menus/items/export/csv", headers=headers_a)
    assert csv_res.status_code == 200
    assert "Gutti Vankaya" in csv_res.text
    assert "Mushroom cashew" in csv_res.text

    # 7. Copy Between Branches (A1 -> A2) and reject cross-tenant target branch
    copy_res = client.post(
        "/api/v1/menus/copy-between-branches",
        json={"target_branch_id": branch_a2.id, "menu_ids": [menu["id"]]},
        headers=headers_a,
    )
    assert copy_res.status_code == 200
    assert copy_res.json()["copied_menus"] == 1
    assert copy_res.json()["copied_items"] == 3

    headers_a2 = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a2.id}
    menus_a2 = client.get("/api/v1/menus", headers=headers_a2).json()
    assert len(menus_a2) == 1
    assert menus_a2[0]["item_count"] == 3

    cross_copy = client.post(
        "/api/v1/menus/copy-between-branches",
        json={"target_branch_id": seed_two_tenants["branch_b"].id, "menu_ids": [menu["id"]]},
        headers=headers_a,
    )
    assert cross_copy.status_code == 404

    # 8. Safe Delete checks: Category with items blocks delete, deleting items then category works
    del_cat_blocked = client.delete(f"/api/v1/menus/categories/{cat['id']}", headers=headers_a)
    assert del_cat_blocked.status_code == 400


def test_3d_hierarchy_cuisines_food_types_subcategories_and_templates(client, db, seed_two_tenants):
    branch_a = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]
    token_b = seed_two_tenants["token_b"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Cuisines CRUD & tenant isolation
    c_south = client.post(
        "/api/v1/menus/cuisines",
        json={"name": "South Indian", "description": "Authentic Southern dishes", "display_order": 1},
        headers=headers_a,
    ).json()
    c_north = client.post(
        "/api/v1/menus/cuisines",
        json={"name": "North Indian", "display_order": 2},
        headers=headers_a,
    ).json()
    assert c_south["name"] == "South Indian"
    assert len(client.get("/api/v1/menus/cuisines", headers=headers_b).json()) == 0
    assert client.put(f"/api/v1/menus/cuisines/{c_south['id']}", json={"name": "Hijacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/menus/cuisines/{c_south['id']}", headers=headers_b).status_code == 404

    # 2. Custom Categories & Subcategories
    cat_curries = client.post(
        "/api/v1/menus/categories",
        json={"name": "Curries & Gravies", "display_order": 1},
        headers=headers_a,
    ).json()
    cat_andhra_sub = client.post(
        "/api/v1/menus/categories",
        json={"name": "Andhra Curries", "parent_id": cat_curries["id"], "display_order": 2},
        headers=headers_a,
    ).json()
    assert cat_andhra_sub["parent_id"] == cat_curries["id"]
    assert cat_andhra_sub["parent_name"] == "Curries & Gravies"

    cat_starters = client.post(
        "/api/v1/menus/categories",
        json={"name": "Starters", "display_order": 3},
        headers=headers_a,
    ).json()

    # 3. Scheduled Menu
    dinner_menu = client.post(
        "/api/v1/menus",
        json={
            "name": "Dinner Menu",
            "schedule_type": "Dinner",
            "available_from": "18:30",
            "available_to": "23:30",
            "active_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        },
        headers=headers_a,
    ).json()
    assert dinner_menu["schedule_type"] == "Dinner"
    assert dinner_menu["available_from"] == "18:30"

    # 4. Items spanning all 4 food_type values + independent cuisines & categories
    chicken_65 = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Chicken 65",
            "base_price": 220.0,
            "cuisine_id": c_south["id"],
            "food_type": "NON_VEG",
            "category_id": cat_starters["id"],
            "menu_id": dinner_menu["id"],
            "tax_rate": 5.0,
            "order_channels": ["DineIn", "Takeaway", "QR"],
            "spice_levels": ["Medium", "Spicy"],
            "variants": [{"name": "Half", "price": 130.0}, {"name": "Full", "price": 220.0}],
        },
        headers=headers_a,
    )
    assert chicken_65.status_code == 200, chicken_65.text
    chicken_65_data = chicken_65.json()
    assert chicken_65_data["cuisine_name"] == "South Indian"
    assert chicken_65_data["food_type"] == "NON_VEG"
    assert chicken_65_data["is_veg"] is False
    assert len(chicken_65_data["variants"]) == 2

    egg_pakoda = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Egg Pakoda",
            "base_price": 140.0,
            "cuisine_id": c_south["id"],
            "food_type": "EGG",
            "category_id": cat_starters["id"],
            "order_channels": ["DineIn", "Delivery"],
        },
        headers=headers_a,
    ).json()
    assert egg_pakoda["food_type"] == "EGG"
    assert egg_pakoda["is_veg"] is False

    gutti_vankaya = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Gutti Vankaya",
            "base_price": 180.0,
            "cuisine_id": c_south["id"],
            "food_type": "VEG",
            "category_id": cat_andhra_sub["id"],
        },
        headers=headers_a,
    ).json()

    chole_vegan = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Chole Masala",
            "base_price": 165.0,
            "cuisine_id": c_north["id"],
            "food_type": "VEGAN",
            "category_id": cat_curries["id"],
        },
        headers=headers_a,
    ).json()
    assert chole_vegan["food_type"] == "VEGAN"
    assert chole_vegan["is_veg"] is True

    # 5. Multi-dimensional filtering tests
    res_south_nonveg_starters = client.get(
        f"/api/v1/menus/items?cuisine_id={c_south['id']}&food_type=NON_VEG&category_id={cat_starters['id']}",
        headers=headers_a,
    ).json()
    assert [i["name"] for i in res_south_nonveg_starters] == ["Chicken 65"]

    res_parent_cat = client.get(
        f"/api/v1/menus/items?category_id={cat_curries['id']}",
        headers=headers_a,
    ).json()
    # Parent category filter includes subcategory Gutti Vankaya + direct Chole Masala
    assert {i["name"] for i in res_parent_cat} == {"Gutti Vankaya", "Chole Masala"}

    res_qr_only = client.get("/api/v1/menus/items?order_channel=QR", headers=headers_a).json()
    assert "Chicken 65" in {i["name"] for i in res_qr_only}
    assert "Egg Pakoda" not in {i["name"] for i in res_qr_only}

    # 6. Indian Default Template application & idempotency
    tpl_1 = client.post(
        "/api/v1/menus/templates/apply-indian-default",
        json={"include_sample_dishes": True, "create_scheduled_menus": True},
        headers=headers_a,
    )
    assert tpl_1.status_code == 200, tpl_1.text
    d1 = tpl_1.json()
    assert d1["created_cuisines"] >= 8  # South/North already created
    assert d1["created_categories"] >= 11
    assert d1["created_items"] > 20

    tpl_2 = client.post(
        "/api/v1/menus/templates/apply-indian-default",
        json={"include_sample_dishes": True, "create_scheduled_menus": True},
        headers=headers_a,
    ).json()
    assert tpl_2["created_cuisines"] == 0
    assert tpl_2["created_categories"] == 0
    assert tpl_2["created_items"] == 0


def test_branch_pricing_availability_gst_and_combo_depletion(client, db, seed_two_tenants):
    tenant_a = seed_two_tenants["tenant_a"]
    branch_a1 = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]

    branch_a2 = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="Airport Kiosk",
        code="A-AIR",
        address="Terminal 1",
        tax_rate=Decimal("5.00"),
        is_active=True,
    )
    db.add(branch_a2)
    db.commit()

    headers_a1 = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a1.id}
    headers_a2 = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a2.id}

    cuisine = client.post(
        "/api/v1/menus/cuisines",
        json={"name": "Telangana Special"},
        headers=headers_a1,
    ).json()
    cat = client.post(
        "/api/v1/menus/categories",
        json={"name": "Combos / Special Meals"},
        headers=headers_a1,
    ).json()

    biryani = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Mutton Dum Biryani",
            "base_price": 300.0,
            "cuisine_id": cuisine["id"],
            "food_type": "NON_VEG",
            "category_id": cat["id"],
            "tax_rate": 5.0,
            "branch_configs": [
                {
                    "branch_id": branch_a2.id,
                    "branch_price": 380.0,
                    "is_available": True,
                    "show_on_customer_site": True,
                }
            ],
        },
        headers=headers_a1,
    ).json()

    starter = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Tandoori Prawns",
            "base_price": 400.0,
            "cuisine_id": cuisine["id"],
            "food_type": "NON_VEG",
            "category_id": cat["id"],
            "tax_rate": 18.0,
            "branch_configs": [
                {
                    "branch_id": branch_a2.id,
                    "is_available": False,
                    "show_on_customer_site": False,
                }
            ],
        },
        headers=headers_a1,
    ).json()

    # Create Inventory + Recipe on Biryani (2.0 kg rice per portion)
    rice = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="Aged Basmati Rice",
        uom="kg",
        current_stock=Decimal("10.000"),
        minimum_stock=Decimal("2.000"),
        cost_per_unit=Decimal("100.00"),
    )
    db.add(rice)
    db.flush()
    recipe = Recipe(id=str(uuid.uuid4()), tenant_id=tenant_a.id, menu_item_id=biryani["id"], yield_portions=1)
    db.add(recipe)
    db.flush()
    db.add(RecipeItem(id=str(uuid.uuid4()), recipe_id=recipe.id, inventory_item_id=rice.id, quantity=Decimal("2.000"), uom="kg"))
    db.commit()

    # Create Combo Meal containing 2x Biryani at 12% GST
    combo = client.post(
        "/api/v1/menus/items",
        json={
            "name": "Nizam Biryani Combo",
            "base_price": 600.0,
            "cuisine_id": cuisine["id"],
            "food_type": "NON_VEG",
            "category_id": cat["id"],
            "tax_rate": 12.0,
            "is_combo": True,
            "combo_components": [{"component_item_id": biryani["id"], "quantity": 2}],
        },
        headers=headers_a1,
    )
    assert combo.status_code == 200, combo.text
    combo_data = combo.json()
    assert combo_data["is_combo"] is True
    assert len(combo_data["combo_components"]) == 1

    # Verify branch-effective views on Branch A2
    items_a2 = client.get("/api/v1/menus/items", headers=headers_a2).json()
    by_name = {i["name"]: i for i in items_a2}
    assert by_name["Mutton Dum Biryani"]["effective_price"] == 380.0
    assert by_name["Tandoori Prawns"]["is_available"] is False

    # Customer storefront with branch_id reflects branch pricing & hides unavailable items
    pub_menu = client.get(
        f"/api/v1/public/{tenant_a.slug}/menu?branch_id={branch_a2.id}&cuisine_id={cuisine['id']}&food_type=NON_VEG"
    )
    assert pub_menu.status_code == 200
    pub_items = {it["name"]: it for c in pub_menu.json()["categories"] for it in c["items"]}
    assert pub_items["Mutton Dum Biryani"]["base_price"] == 380.0
    assert "Tandoori Prawns" not in pub_items

    # POS rejects branch-unavailable item on Branch A2
    res_unavail = client.post(
        "/api/v1/orders",
        json={
            "order_type": "DineIn",
            "items": [{"menu_item_id": starter["id"], "quantity": 1, "modifiers": []}],
        },
        headers=headers_a2,
    )
    assert res_unavail.status_code == 400

    # POS uses branch override price (380.0 for Biryani) + combo GST (12% of 600 = 72) + combo inventory depletion
    res_order = client.post(
        "/api/v1/orders",
        json={
            "order_type": "DineIn",
            "items": [
                {"menu_item_id": biryani["id"], "quantity": 1, "modifiers": []},
                {"menu_item_id": combo_data["id"], "quantity": 1, "modifiers": []},
            ],
        },
        headers=headers_a2,
    )
    assert res_order.status_code == 200, res_order.text
    order_json = res_order.json()
    # Subtotal: 380 (branch price) + 600 (combo) = 980
    # Weighted GST: (380 * 5%) + (600 * 12%) = 19.00 + 72.00 = 91.00
    assert float(order_json["subtotal"]) == 980.0
    assert float(order_json["tax_amount"]) == 91.0

    # Settle invoice to trigger recipe + combo inventory depletion
    res_pay = client.post(
        f"/api/v1/invoices/orders/{order_json['id']}/payments",
        json={"amount": float(order_json["total_amount"]), "payment_method": "Cash"},
        headers=headers_a2,
    )
    assert res_pay.status_code == 200, res_pay.text

    db.refresh(rice)
    # Depletion: 1x Biryani (2.0 kg) + 1x Combo of 2x Biryani (4.0 kg) = 6.0 kg -> remaining 4.0 kg
    assert float(rice.current_stock) == 4.0


def test_dish_photo_upload_and_validation(client, seed_two_tenants):
    import os
    token_a = seed_two_tenants["token_a"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Unauthenticated request rejected
    res_unauth = client.post(
        "/api/v1/menus/upload-image",
        files={"file": ("dosa.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert res_unauth.status_code in (401, 403)

    # Disallowed file extension rejected
    res_bad = client.post(
        "/api/v1/menus/upload-image",
        files={"file": ("script.exe", b"MZ", "application/octet-stream")},
        headers=headers_a,
    )
    assert res_bad.status_code == 400

    # Valid image upload succeeds and is served via /uploads/dishes/...
    res_ok = client.post(
        "/api/v1/menus/upload-image",
        files={"file": ("masala_dosa.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00", "image/png")},
        headers=headers_a,
    )
    assert res_ok.status_code == 200, res_ok.text
    image_url = res_ok.json()["image_url"]
    assert "/uploads/dishes/" in image_url and image_url.endswith(".png")

    rel_path = image_url.split("/uploads/dishes/")[-1]
    res_fetch = client.get(f"/uploads/dishes/{rel_path}")
    assert res_fetch.status_code == 200

    # Clean up temporary uploaded test asset
    uploaded_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "uploads", "dishes", rel_path
    )
    if os.path.exists(uploaded_file):
        os.remove(uploaded_file)
