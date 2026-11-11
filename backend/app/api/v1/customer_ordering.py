from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.models.saas import Tenant
from app.models.organization import Branch
from app.models.table import RestaurantTable
from app.models.menu import Menu, Cuisine, MenuCategory, MenuItem, MenuItemBranchConfig
from app.schemas.order import OrderCreate, OrderResponse
from app.services.pos_service import create_pos_order

router = APIRouter()

class MockCustomerStaff:
    """Mock staff object to attribute online & QR orders in the audit logs."""
    def __init__(self, tenant_id: str):
        self.id = "CUSTOMER_ONLINE"
        self.full_name = "Online / QR Customer"
        self.tenant_id = tenant_id

@router.get("/{tenant_slug}/menu")
def get_public_storefront_menu(
    tenant_slug: str,
    menu_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    cuisine_id: Optional[str] = None,
    food_type: Optional[str] = None,
    category_id: Optional[str] = None,
    order_channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug, Tenant.status == "Active").first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Restaurant storefront not found")

    if branch_id:
        branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == tenant.id, Branch.is_active == True).first()
    else:
        branch = db.query(Branch).filter(Branch.tenant_id == tenant.id, Branch.is_active == True).first()

    cuisines = db.query(Cuisine).filter(
        Cuisine.tenant_id == tenant.id,
        Cuisine.is_active == True
    ).order_by(Cuisine.display_order.asc(), Cuisine.name.asc()).all()
    cuisine_map = {cu.id: cu.name for cu in cuisines}

    menus = db.query(Menu).filter(
        Menu.tenant_id == tenant.id,
        Menu.is_active == True
    ).order_by(Menu.created_at.asc()).all()

    categories = db.query(MenuCategory).filter(
        MenuCategory.tenant_id == tenant.id,
        MenuCategory.is_active == True
    ).order_by(MenuCategory.display_order.asc(), MenuCategory.name.asc()).all()

    allowed_cat_ids = None
    if category_id:
        allowed_cat_ids = {category_id} | {c.id for c in categories if c.parent_id == category_id}

    branch_cfg_map = {}
    if branch:
        cfgs = db.query(MenuItemBranchConfig).filter(
            MenuItemBranchConfig.tenant_id == tenant.id,
            MenuItemBranchConfig.branch_id == branch.id,
        ).all()
        branch_cfg_map = {cfg.menu_item_id: cfg for cfg in cfgs}

    normalized_food_type = food_type.strip().upper() if food_type else None

    def _serialize_visible_items(cat_items):
        result = []
        for i in sorted(cat_items, key=lambda x: (x.display_order or 0, x.name)):
            cfg = branch_cfg_map.get(i.id)
            effective_available = cfg.is_available if cfg else i.is_available
            effective_customer_site = cfg.show_on_customer_site if cfg else getattr(i, "show_on_customer_site", True)
            if not effective_available or not effective_customer_site:
                continue
            if menu_id and i.menu_id != menu_id:
                continue
            if cuisine_id and i.cuisine_id != cuisine_id:
                continue
            item_food_type = (i.food_type or ("VEG" if i.is_veg else "NON_VEG")).upper()
            if normalized_food_type and item_food_type != normalized_food_type:
                continue
            channels = i.order_channels if isinstance(i.order_channels, list) else ["DineIn", "Takeaway", "Delivery", "QR"]
            if order_channel and order_channel not in channels:
                continue

            effective_price = (
                float(cfg.branch_price)
                if (cfg and cfg.branch_price is not None)
                else float(i.base_price)
            )
            result.append({
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "base_price": effective_price,
                "image_url": i.image_url,
                "is_veg": i.is_veg,
                "food_type": item_food_type,
                "cuisine_id": i.cuisine_id,
                "cuisine_name": cuisine_map.get(i.cuisine_id) if i.cuisine_id else None,
                "tax_rate": float(i.tax_rate or 0),
                "is_available": effective_available,
                "preparation_time": i.preparation_time,
                "order_channels": channels,
                "spice_levels": i.spice_levels if isinstance(i.spice_levels, list) else [],
                "is_combo": bool(i.is_combo),
                "combo_components": [
                    {
                        "component_item_id": cc.component_item_id,
                        "component_name": cc.component_item.name if cc.component_item else None,
                        "quantity": cc.quantity,
                    }
                    for cc in (i.combo_components or [])
                ],
                "variants": [{"id": v.id, "name": v.name, "price": float(v.price)} for v in i.variants if v.is_available],
                "modifiers": [
                    {
                        "group_name": mg.name,
                        "min": mg.min_selection,
                        "max": mg.max_selection,
                        "options": [{"id": m.id, "name": m.name, "price": float(m.price)} for m in mg.modifiers if m.is_available]
                    }
                    for mg in i.modifier_groups
                ]
            })
        return result

    rendered_categories = []
    for c in categories:
        if allowed_cat_ids is not None and c.id not in allowed_cat_ids:
            continue
        visible_items = _serialize_visible_items(c.items)
        if visible_items:
            rendered_categories.append({
                "id": c.id,
                "name": c.name,
                "icon": c.icon,
                "parent_id": c.parent_id,
                "items": visible_items,
            })

    return {
        "restaurant_name": tenant.name,
        "slug": tenant.slug,
        "currency": tenant.currency,
        "branch_id": branch.id if branch else None,
        "cuisines": [
            {"id": cu.id, "name": cu.name, "description": cu.description, "display_order": cu.display_order}
            for cu in cuisines
        ],
        "menus": [
            {
                "id": m.id,
                "name": m.name,
                "schedule_type": m.schedule_type,
                "available_from": m.available_from,
                "available_to": m.available_to,
            }
            for m in menus
        ],
        "categories": rendered_categories,
    }

@router.get("/table/{qr_token}")
def get_table_by_qr(qr_token: str, db: Session = Depends(get_db)):
    table = db.query(RestaurantTable).filter(RestaurantTable.qr_code_token == qr_token).first()
    if not table:
        raise HTTPException(status_code=404, detail="Invalid QR code or table not found")

    tenant = db.query(Tenant).filter(Tenant.id == table.tenant_id).first()
    return {
        "table_id": table.id,
        "table_number": table.table_number,
        "assigned_menu_id": table.assigned_menu_id,
        "tenant_id": table.tenant_id,
        "tenant_slug": tenant.slug,
        "tenant_name": tenant.name,
        "currency": tenant.currency,
        "branch_id": table.branch_id
    }

@router.post("/{tenant_slug}/orders", response_model=OrderResponse)
def submit_customer_order(
    tenant_slug: str,
    data: OrderCreate,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug, Tenant.status == "Active").first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find applicable branch
    branch_id = None
    if data.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == data.table_id).first()
        if table:
            branch_id = table.branch_id
    if not branch_id:
        first_branch = db.query(Branch).filter(Branch.tenant_id == tenant.id, Branch.is_active == True).first()
        if not first_branch:
            raise HTTPException(status_code=400, detail="No active branch configured for this restaurant")
        branch_id = first_branch.id

    mock_staff = MockCustomerStaff(tenant.id)
    order = create_pos_order(db, tenant.id, branch_id, data, mock_staff)
    return order
