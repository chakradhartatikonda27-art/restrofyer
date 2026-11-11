from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from decimal import Decimal
import csv
import io
import os
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission, get_optional_branch_id
from app.core.permissions import Permission
from app.models.organization import Branch
from app.models.table import RestaurantTable
from app.models.kitchen import KitchenStation
from app.models.menu import (
    Cuisine,
    Menu,
    MenuCategory,
    MenuItem,
    MenuItemBranchConfig,
    ComboMealItem,
    ItemVariant,
    ItemModifierGroup,
    ItemModifier,
)
from app.schemas.menu import (
    CuisineCreate,
    CuisineUpdate,
    CuisineResponse,
    MenuCreate,
    MenuUpdate,
    MenuSummaryResponse,
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    ModifierGroupStandaloneCreate,
    ModifierGroupUpdate,
    ItemModifierGroupResponse,
    ItemModifierStandaloneCreate,
    ItemModifierUpdate,
    ItemModifierResponse,
    CopyMenusRequest,
    CopyItemsRequest,
    AssignMenuTablesRequest,
    ReorderItemsRequest,
    BulkUploadItemsRequest,
    TemplateApplyRequest,
)
from app.services.menu_template_service import apply_indian_menu_template

router = APIRouter()


def _branch_filter(model_cls, branch_id: Optional[str]):
    if not branch_id:
        return True
    if model_cls is MenuItem:
        return or_(
            MenuItem.branch_id == branch_id,
            MenuItem.branch_id.is_(None),
            MenuItem.branch_configs.any(MenuItemBranchConfig.branch_id == branch_id),
        )
    return or_(model_cls.branch_id == branch_id, model_cls.branch_id.is_(None))


def _normalize_food_type(food_type: Optional[str], is_veg: Optional[bool]) -> Tuple[str, bool]:
    if food_type in ("VEG", "NON_VEG", "EGG", "VEGAN"):
        return food_type, food_type in ("VEG", "VEGAN")
    if is_veg is False:
        return "NON_VEG", False
    return "VEG", True


def _resolve_branch_effective_state(
    item: MenuItem, branch_id: Optional[str]
) -> Tuple[float, bool, bool]:
    base_price = float(item.base_price)
    avail = bool(item.is_available)
    on_site = bool(item.show_on_customer_site)

    if branch_id and item.branch_configs:
        for cfg in item.branch_configs:
            if cfg.branch_id == branch_id:
                eff_price = float(cfg.branch_price) if cfg.branch_price is not None else base_price
                return eff_price, bool(cfg.is_available), bool(cfg.show_on_customer_site)

    return base_price, avail, on_site


def _serialize_item(item: MenuItem, db: Session, branch_id: Optional[str] = None) -> dict:
    eff_price, eff_avail, eff_site = _resolve_branch_effective_state(item, branch_id)
    branch_names = {
        b.id: b.name
        for b in db.query(Branch).filter(Branch.tenant_id == item.tenant_id).all()
    }
    station_name = None
    if item.kitchen_station_id:
        st = db.query(KitchenStation).filter(KitchenStation.id == item.kitchen_station_id).first()
        station_name = st.name if st else None

    return {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "menu_id": item.menu_id,
        "branch_id": item.branch_id,
        "cuisine_id": item.cuisine_id,
        "cuisine_name": item.cuisine.name if item.cuisine else None,
        "category_id": item.category_id,
        "category_name": item.category.name if item.category else None,
        "parent_category_id": item.category.parent_id if item.category else None,
        "menu_name": item.menu.name if item.menu else None,
        "name": item.name,
        "sku": item.sku,
        "description": item.description,
        "image_url": item.image_url,
        "base_price": float(item.base_price),
        "effective_price": eff_price,
        "cost_price": float(item.cost_price or 0.0),
        "tax_rate": float(item.tax_rate or 5.0),
        "preparation_time": item.preparation_time or 15,
        "display_order": item.display_order or 0,
        "is_available": eff_avail,
        "show_on_customer_site": eff_site,
        "food_type": item.food_type or ("VEG" if item.is_veg else "NON_VEG"),
        "is_veg": bool(item.is_veg),
        "calories": item.calories,
        "kitchen_station_id": item.kitchen_station_id,
        "kitchen_station_name": station_name,
        "order_channels": item.order_channels or ["DineIn", "Takeaway", "Delivery", "QR"],
        "spice_levels": item.spice_levels or [],
        "is_combo": bool(item.is_combo),
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "price": float(v.price),
                "sku": v.sku,
                "is_available": bool(v.is_available),
            }
            for v in (item.variants or [])
        ],
        "modifier_groups": [
            {
                "id": mg.id,
                "item_id": mg.item_id,
                "item_name": item.name,
                "name": mg.name,
                "min_selection": mg.min_selection,
                "max_selection": mg.max_selection,
                "modifiers": [
                    {
                        "id": m.id,
                        "group_id": m.group_id,
                        "group_name": mg.name,
                        "item_id": item.id,
                        "item_name": item.name,
                        "name": m.name,
                        "price": float(m.price),
                        "is_available": bool(m.is_available),
                    }
                    for m in (mg.modifiers or [])
                ],
            }
            for mg in (item.modifier_groups or [])
        ],
        "branch_configs": [
            {
                "branch_id": bc.branch_id,
                "branch_name": branch_names.get(bc.branch_id),
                "branch_price": float(bc.branch_price) if bc.branch_price is not None else None,
                "is_available": bool(bc.is_available),
                "show_on_customer_site": bool(bc.show_on_customer_site),
            }
            for bc in (item.branch_configs or [])
        ],
        "combo_components": [
            {
                "component_item_id": cc.component_item_id,
                "component_item_name": cc.component_item.name if cc.component_item else None,
                "quantity": cc.quantity,
            }
            for cc in (item.combo_components or [])
        ],
    }


def _serialize_category(cat: MenuCategory, db: Session, branch_id: Optional[str]) -> dict:
    scoped_items = [
        i
        for i in (cat.items or [])
        if branch_id is None
        or i.branch_id is None
        or i.branch_id == branch_id
        or any(cfg.branch_id == branch_id for cfg in (i.branch_configs or []))
    ]
    parent_name = cat.parent.name if cat.parent else None
    return {
        "id": cat.id,
        "tenant_id": cat.tenant_id,
        "menu_id": cat.menu_id,
        "branch_id": cat.branch_id,
        "parent_id": cat.parent_id,
        "parent_name": parent_name,
        "name": cat.name,
        "display_order": cat.display_order or 0,
        "icon": cat.icon,
        "is_active": bool(cat.is_active),
        "item_count": len(scoped_items),
        "items": [
            _serialize_item(i, db, branch_id)
            for i in sorted(scoped_items, key=lambda x: (x.display_order or 0, x.name))
        ],
    }


def _serialize_menu(menu: Menu, db: Session, branch_id: Optional[str]) -> dict:
    item_count = (
        db.query(MenuItem)
        .filter(
            MenuItem.tenant_id == menu.tenant_id,
            MenuItem.menu_id == menu.id,
            _branch_filter(MenuItem, branch_id),
        )
        .count()
    )
    assigned_tables = (
        db.query(RestaurantTable.id)
        .filter(
            RestaurantTable.tenant_id == menu.tenant_id,
            RestaurantTable.assigned_menu_id == menu.id,
        )
        .all()
    )
    return {
        "id": menu.id,
        "tenant_id": menu.tenant_id,
        "branch_id": menu.branch_id,
        "name": menu.name,
        "description": menu.description,
        "schedule_type": menu.schedule_type or "AllDay",
        "available_from": menu.available_from,
        "available_to": menu.available_to,
        "active_days": menu.active_days or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "display_order": menu.display_order or 0,
        "is_active": bool(menu.is_active),
        "item_count": item_count,
        "assigned_table_ids": [row[0] for row in assigned_tables],
    }


def _sync_branch_configs(
    db: Session, tenant_id: str, item_id: str, branch_configs: list
) -> None:
    db.query(MenuItemBranchConfig).filter(
        MenuItemBranchConfig.tenant_id == tenant_id,
        MenuItemBranchConfig.menu_item_id == item_id,
    ).delete()
    for cfg in branch_configs:
        branch = (
            db.query(Branch)
            .filter(Branch.id == cfg.branch_id, Branch.tenant_id == tenant_id)
            .first()
        )
        if not branch:
            continue
        db.add(
            MenuItemBranchConfig(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                menu_item_id=item_id,
                branch_id=cfg.branch_id,
                branch_price=Decimal(str(cfg.branch_price)) if cfg.branch_price is not None else None,
                is_available=cfg.is_available,
                show_on_customer_site=cfg.show_on_customer_site,
            )
        )


def _sync_combo_components(
    db: Session, tenant_id: str, combo_item_id: str, components: list
) -> None:
    db.query(ComboMealItem).filter(
        ComboMealItem.tenant_id == tenant_id,
        ComboMealItem.combo_item_id == combo_item_id,
    ).delete()
    for comp in components:
        if comp.component_item_id == combo_item_id:
            continue
        target = (
            db.query(MenuItem)
            .filter(MenuItem.id == comp.component_item_id, MenuItem.tenant_id == tenant_id)
            .first()
        )
        if target:
            db.add(
                ComboMealItem(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    combo_item_id=combo_item_id,
                    component_item_id=target.id,
                    quantity=max(1, comp.quantity),
                )
            )


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
UPLOAD_DISHES_DIR = (
    "/tmp/uploads/dishes"
    if os.getenv("VERCEL")
    else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "uploads",
        "dishes",
    )
)


@router.post("/upload-image")
async def upload_dish_image(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
):
    """Uploads a custom dish photo (JPG, PNG, WEBP, GIF <= 5 MB) and returns its public URL."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format. Allowed: JPG, JPEG, PNG, WEBP, GIF.",
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 5 MB limit.")

    os.makedirs(UPLOAD_DISHES_DIR, exist_ok=True)
    safe_name = f"{current_user.tenant_id[:8]}_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(UPLOAD_DISHES_DIR, safe_name)
    with open(target_path, "wb") as out_f:
        out_f.write(content)

    base = str(request.base_url).rstrip("/")
    return {"image_url": f"{base}/uploads/dishes/{safe_name}"}


# ---------------------------------------------------------------------------
# Templates (Indian Menu Catalog Onboarding / One-Click Populate)
# ---------------------------------------------------------------------------

@router.post("/templates/apply-indian-default")
def apply_indian_default_template(
    data: TemplateApplyRequest,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    summary = apply_indian_menu_template(
        db=db,
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        cuisines_filter=data.cuisines,
        categories_filter=data.categories,
        include_sample_dishes=data.include_sample_dishes,
        create_scheduled_menus=data.create_scheduled_menus,
    )
    return {
        "message": "Default Indian menu template applied cleanly",
        **summary,
    }


# ---------------------------------------------------------------------------
# Cuisines Dimension (Static routes BEFORE /{menu_id})
# ---------------------------------------------------------------------------

@router.get("/cuisines", response_model=List[CuisineResponse])
def list_cuisines(
    include_inactive: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Cuisine).filter(Cuisine.tenant_id == current_user.tenant_id)
    if not include_inactive:
        query = query.filter(Cuisine.is_active == True)
    cuisines = query.order_by(Cuisine.display_order.asc(), Cuisine.name.asc()).all()
    return [
        {
            "id": c.id,
            "tenant_id": c.tenant_id,
            "name": c.name,
            "description": c.description,
            "display_order": c.display_order or 0,
            "is_active": bool(c.is_active),
            "item_count": len(c.items or []),
        }
        for c in cuisines
    ]


@router.post("/cuisines", response_model=CuisineResponse)
def create_cuisine(
    data: CuisineCreate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Cuisine)
        .filter(Cuisine.tenant_id == current_user.tenant_id, Cuisine.name == data.name.strip())
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"Cuisine '{data.name}' already exists")

    cuisine = Cuisine(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=data.name.strip(),
        description=data.description,
        display_order=data.display_order,
        is_active=data.is_active,
    )
    db.add(cuisine)
    db.commit()
    db.refresh(cuisine)
    return {
        "id": cuisine.id,
        "tenant_id": cuisine.tenant_id,
        "name": cuisine.name,
        "description": cuisine.description,
        "display_order": cuisine.display_order or 0,
        "is_active": bool(cuisine.is_active),
        "item_count": 0,
    }


@router.put("/cuisines/{cuisine_id}", response_model=CuisineResponse)
def update_cuisine(
    cuisine_id: str,
    data: CuisineUpdate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cuisine = (
        db.query(Cuisine)
        .filter(Cuisine.id == cuisine_id, Cuisine.tenant_id == current_user.tenant_id)
        .first()
    )
    if not cuisine:
        raise HTTPException(status_code=404, detail="Cuisine not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(cuisine, field, val)
    db.commit()
    db.refresh(cuisine)
    return {
        "id": cuisine.id,
        "tenant_id": cuisine.tenant_id,
        "name": cuisine.name,
        "description": cuisine.description,
        "display_order": cuisine.display_order or 0,
        "is_active": bool(cuisine.is_active),
        "item_count": len(cuisine.items or []),
    }


@router.delete("/cuisines/{cuisine_id}")
def delete_cuisine(
    cuisine_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cuisine = (
        db.query(Cuisine)
        .filter(Cuisine.id == cuisine_id, Cuisine.tenant_id == current_user.tenant_id)
        .first()
    )
    if not cuisine:
        raise HTTPException(status_code=404, detail="Cuisine not found")

    db.query(MenuItem).filter(
        MenuItem.tenant_id == current_user.tenant_id,
        MenuItem.cuisine_id == cuisine.id,
    ).update({"cuisine_id": None})
    name = cuisine.name
    db.delete(cuisine)
    db.commit()
    return {"message": f"Deleted cuisine '{name}'"}


# ---------------------------------------------------------------------------
# Menus Branch Copy
# ---------------------------------------------------------------------------

@router.post("/copy-between-branches")
def copy_menus_between_branches(
    data: CopyMenusRequest,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    target_branch = (
        db.query(Branch)
        .filter(
            Branch.id == data.target_branch_id,
            Branch.tenant_id == current_user.tenant_id,
            Branch.is_active == True,
        )
        .first()
    )
    if not target_branch:
        raise HTTPException(status_code=404, detail="Target branch not found")
    if branch_id and target_branch.id == branch_id:
        raise HTTPException(status_code=400, detail="Target branch must be different from active branch")

    source_menus = (
        db.query(Menu)
        .filter(
            Menu.tenant_id == current_user.tenant_id,
            Menu.id.in_(data.menu_ids),
        )
        .all()
    )
    if not source_menus:
        raise HTTPException(status_code=404, detail="No matching menus found to copy")

    copied_menus = 0
    copied_items = 0

    for src_menu in source_menus:
        existing_target = (
            db.query(Menu)
            .filter(
                Menu.tenant_id == current_user.tenant_id,
                Menu.branch_id == target_branch.id,
                Menu.name == src_menu.name,
            )
            .first()
        )
        if existing_target:
            target_menu = existing_target
        else:
            target_menu = Menu(
                id=str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                branch_id=target_branch.id,
                name=src_menu.name,
                description=src_menu.description,
                schedule_type=src_menu.schedule_type or "AllDay",
                available_from=src_menu.available_from,
                available_to=src_menu.available_to,
                active_days=src_menu.active_days,
                display_order=src_menu.display_order or 0,
                is_active=True,
            )
            db.add(target_menu)
            db.flush()
            copied_menus += 1

        src_items = (
            db.query(MenuItem)
            .filter(
                MenuItem.tenant_id == current_user.tenant_id,
                MenuItem.menu_id == src_menu.id,
                _branch_filter(MenuItem, branch_id),
            )
            .all()
        )
        for src_item in src_items:
            copied_items += _clone_item_to_branch(
                db=db,
                tenant_id=current_user.tenant_id,
                src_item=src_item,
                target_branch_id=target_branch.id,
                target_menu_id=target_menu.id,
            )

    db.commit()
    return {
        "message": f"Copied {copied_menus} menu(s) and {copied_items} menu item(s) to {target_branch.name}",
        "copied_menus": copied_menus,
        "copied_items": copied_items,
    }


def _clone_item_to_branch(
    db: Session,
    tenant_id: str,
    src_item: MenuItem,
    target_branch_id: str,
    target_menu_id: Optional[str],
) -> int:
    cat_name = src_item.category.name if src_item.category else "General"
    target_cat = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.tenant_id == tenant_id,
            MenuCategory.name == cat_name,
            or_(MenuCategory.branch_id == target_branch_id, MenuCategory.branch_id.is_(None)),
        )
        .first()
    )
    if not target_cat:
        target_cat = MenuCategory(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=target_branch_id,
            menu_id=target_menu_id,
            name=cat_name,
            display_order=src_item.category.display_order if src_item.category else 0,
            icon=src_item.category.icon if src_item.category else None,
            is_active=True,
        )
        db.add(target_cat)
        db.flush()

    duplicate = (
        db.query(MenuItem)
        .filter(
            MenuItem.tenant_id == tenant_id,
            MenuItem.branch_id == target_branch_id,
            MenuItem.name == src_item.name,
            MenuItem.menu_id == target_menu_id,
        )
        .first()
    )
    if duplicate:
        return 0

    new_item = MenuItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=target_branch_id,
        menu_id=target_menu_id,
        cuisine_id=src_item.cuisine_id,
        category_id=target_cat.id,
        name=src_item.name,
        sku=src_item.sku,
        description=src_item.description,
        image_url=src_item.image_url,
        base_price=src_item.base_price,
        cost_price=src_item.cost_price,
        tax_rate=src_item.tax_rate,
        preparation_time=src_item.preparation_time,
        display_order=src_item.display_order,
        is_available=src_item.is_available,
        show_on_customer_site=src_item.show_on_customer_site,
        food_type=src_item.food_type,
        is_veg=src_item.is_veg,
        calories=src_item.calories,
        order_channels=src_item.order_channels,
        spice_levels=src_item.spice_levels,
        is_combo=src_item.is_combo,
    )
    db.add(new_item)
    db.flush()

    for v in src_item.variants or []:
        db.add(
            ItemVariant(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                item_id=new_item.id,
                name=v.name,
                price=v.price,
                sku=v.sku,
                is_available=v.is_available,
            )
        )

    for mg in src_item.modifier_groups or []:
        new_mg = ItemModifierGroup(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            item_id=new_item.id,
            name=mg.name,
            min_selection=mg.min_selection,
            max_selection=mg.max_selection,
        )
        db.add(new_mg)
        db.flush()
        for m in mg.modifiers or []:
            db.add(
                ItemModifier(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    group_id=new_mg.id,
                    name=m.name,
                    price=m.price,
                    is_available=m.is_available,
                )
            )
    return 1


# ---------------------------------------------------------------------------
# Item Categories (with custom subcategories & active/inactive customization)
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=List[MenuCategoryResponse])
def list_categories(
    menu_id: Optional[str] = None,
    include_inactive: bool = False,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MenuCategory).filter(
        MenuCategory.tenant_id == current_user.tenant_id,
        _branch_filter(MenuCategory, branch_id),
    )
    if not include_inactive:
        query = query.filter(MenuCategory.is_active == True)
    if menu_id:
        query = query.filter(MenuCategory.menu_id == menu_id)
    cats = query.order_by(MenuCategory.display_order.asc(), MenuCategory.name.asc()).all()
    return [_serialize_category(c, db, branch_id) for c in cats]


@router.post("/categories", response_model=MenuCategoryResponse)
def create_category(
    data: MenuCategoryCreate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cat = MenuCategory(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=data.branch_id or branch_id,
        menu_id=data.menu_id,
        parent_id=data.parent_id or None,
        name=data.name.strip(),
        display_order=data.display_order,
        icon=data.icon,
        is_active=data.is_active,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _serialize_category(cat, db, branch_id)


@router.put("/categories/{category_id}", response_model=MenuCategoryResponse)
def update_category(
    category_id: str,
    data: MenuCategoryUpdate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(MenuCategory)
        .filter(MenuCategory.id == category_id, MenuCategory.tenant_id == current_user.tenant_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    updates = data.model_dump(exclude_unset=True)
    if updates.get("parent_id") == category_id:
        raise HTTPException(status_code=400, detail="Category cannot be its own parent")

    for field, val in updates.items():
        setattr(cat, field, val)

    db.commit()
    db.refresh(cat)
    return _serialize_category(cat, db, branch_id)


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(MenuCategory)
        .filter(MenuCategory.id == category_id, MenuCategory.tenant_id == current_user.tenant_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    item_count = db.query(MenuItem).filter(MenuItem.category_id == cat.id).count()
    if item_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category '{cat.name}' because {item_count} item(s) still belong to it. Reassign or remove those items first.",
        )

    db.delete(cat)
    db.commit()
    return {"message": f"Deleted category '{cat.name}'"}


# ---------------------------------------------------------------------------
# Menu Items (static routes BEFORE dynamic /{item_id})
# ---------------------------------------------------------------------------

@router.get("/items/export/csv")
def export_menu_items_csv(
    menu_id: Optional[str] = None,
    cuisine_id: Optional[str] = None,
    food_type: Optional[str] = None,
    category_id: Optional[str] = None,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MenuItem).filter(
        MenuItem.tenant_id == current_user.tenant_id,
        _branch_filter(MenuItem, branch_id),
    )
    if menu_id:
        query = query.filter(MenuItem.menu_id == menu_id)
    if cuisine_id:
        query = query.filter(MenuItem.cuisine_id == cuisine_id)
    if food_type:
        query = query.filter(MenuItem.food_type == food_type)
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)
    items = query.order_by(MenuItem.display_order.asc(), MenuItem.name.asc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "name",
        "description",
        "base_price",
        "cost_price",
        "cuisine_name",
        "food_type",
        "category_name",
        "menu_name",
        "tax_rate",
        "is_available",
        "show_on_customer_site",
        "preparation_time",
        "sku",
    ])
    for it in items:
        eff_price, eff_avail, eff_site = _resolve_branch_effective_state(it, branch_id)
        writer.writerow([
            it.name,
            it.description or "",
            eff_price,
            float(it.cost_price or 0.0),
            it.cuisine.name if it.cuisine else "",
            it.food_type or ("VEG" if it.is_veg else "NON_VEG"),
            it.category.name if it.category else "General",
            it.menu.name if it.menu else "",
            float(it.tax_rate or 5.0),
            "true" if eff_avail else "false",
            "true" if eff_site else "false",
            it.preparation_time or 15,
            it.sku or "",
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=menu_items_export.csv"},
    )


@router.post("/items/bulk-upload")
def bulk_upload_menu_items(
    data: BulkUploadItemsRequest,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="No menu items supplied in bulk upload")

    created_count = 0
    for idx, row in enumerate(data.items):
        # 1. Resolve Menu
        resolved_menu_id = data.default_menu_id
        if row.menu_name:
            menu_obj = (
                db.query(Menu)
                .filter(
                    Menu.tenant_id == current_user.tenant_id,
                    Menu.name == row.menu_name.strip(),
                    _branch_filter(Menu, branch_id),
                )
                .first()
            )
            if not menu_obj:
                menu_obj = Menu(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    branch_id=branch_id,
                    name=row.menu_name.strip(),
                    is_active=True,
                )
                db.add(menu_obj)
                db.flush()
            resolved_menu_id = menu_obj.id

        # 2. Resolve Cuisine
        resolved_cuisine_id = None
        if row.cuisine_name:
            cuisine_obj = (
                db.query(Cuisine)
                .filter(
                    Cuisine.tenant_id == current_user.tenant_id,
                    Cuisine.name == row.cuisine_name.strip(),
                )
                .first()
            )
            if not cuisine_obj:
                cuisine_obj = Cuisine(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    name=row.cuisine_name.strip(),
                    is_active=True,
                )
                db.add(cuisine_obj)
                db.flush()
            resolved_cuisine_id = cuisine_obj.id

        # 3. Resolve Dish Category
        cat_name = (row.category_name or "General").strip()
        cat_obj = (
            db.query(MenuCategory)
            .filter(
                MenuCategory.tenant_id == current_user.tenant_id,
                MenuCategory.name == cat_name,
                _branch_filter(MenuCategory, branch_id),
            )
            .first()
        )
        if not cat_obj:
            cat_obj = MenuCategory(
                id=str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                branch_id=branch_id,
                menu_id=resolved_menu_id,
                name=cat_name,
                is_active=True,
            )
            db.add(cat_obj)
            db.flush()

        ftype, veg_flag = _normalize_food_type(row.food_type, row.is_veg)
        item = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            branch_id=branch_id,
            menu_id=resolved_menu_id,
            cuisine_id=resolved_cuisine_id,
            category_id=cat_obj.id,
            name=row.name.strip(),
            description=row.description,
            base_price=row.base_price,
            cost_price=row.cost_price,
            tax_rate=row.tax_rate,
            food_type=ftype,
            is_veg=veg_flag,
            is_available=row.is_available,
            show_on_customer_site=row.show_on_customer_site,
            preparation_time=row.preparation_time,
            sku=row.sku,
            display_order=idx,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
        )
        db.add(item)
        created_count += 1

    db.commit()
    return {"message": f"Successfully uploaded {created_count} menu item(s)", "created_count": created_count}


@router.post("/items/copy-between-branches")
def copy_items_between_branches(
    data: CopyItemsRequest,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    target_branch = (
        db.query(Branch)
        .filter(
            Branch.id == data.target_branch_id,
            Branch.tenant_id == current_user.tenant_id,
            Branch.is_active == True,
        )
        .first()
    )
    if not target_branch:
        raise HTTPException(status_code=404, detail="Target branch not found")
    if branch_id and target_branch.id == branch_id:
        raise HTTPException(status_code=400, detail="Target branch must be different from active branch")

    src_items = (
        db.query(MenuItem)
        .filter(
            MenuItem.tenant_id == current_user.tenant_id,
            MenuItem.id.in_(data.item_ids),
        )
        .all()
    )
    if not src_items:
        raise HTTPException(status_code=404, detail="No matching menu items selected")

    copied = 0
    for src_item in src_items:
        target_menu_id = data.target_menu_id
        if not target_menu_id and src_item.menu:
            matching_menu = (
                db.query(Menu)
                .filter(
                    Menu.tenant_id == current_user.tenant_id,
                    Menu.branch_id == target_branch.id,
                    Menu.name == src_item.menu.name,
                )
                .first()
            )
            if not matching_menu:
                matching_menu = Menu(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    branch_id=target_branch.id,
                    name=src_item.menu.name,
                    description=src_item.menu.description,
                    schedule_type=src_item.menu.schedule_type or "AllDay",
                    is_active=True,
                )
                db.add(matching_menu)
                db.flush()
            target_menu_id = matching_menu.id

        copied += _clone_item_to_branch(
            db=db,
            tenant_id=current_user.tenant_id,
            src_item=src_item,
            target_branch_id=target_branch.id,
            target_menu_id=target_menu_id,
        )

    db.commit()
    return {"message": f"Copied {copied} item(s) to {target_branch.name}", "copied_items": copied}


@router.put("/items/reorder")
def reorder_menu_items(
    data: ReorderItemsRequest,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    for entry in data.items:
        item = (
            db.query(MenuItem)
            .filter(MenuItem.id == entry.id, MenuItem.tenant_id == current_user.tenant_id)
            .first()
        )
        if item:
            item.display_order = entry.display_order
            if entry.menu_id is not None:
                item.menu_id = entry.menu_id
            if entry.category_id is not None:
                item.category_id = entry.category_id
    db.commit()
    return {"message": f"Updated order for {len(data.items)} item(s)"}


@router.get("/items", response_model=List[MenuItemResponse])
def list_menu_items(
    menu_id: Optional[str] = None,
    cuisine_id: Optional[str] = None,
    food_type: Optional[str] = None,
    category_id: Optional[str] = None,
    order_channel: Optional[str] = None,
    is_combo: Optional[bool] = None,
    search: Optional[str] = None,
    available_only: bool = False,
    customer_site_only: bool = False,
    is_veg: Optional[bool] = None,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MenuItem).filter(
        MenuItem.tenant_id == current_user.tenant_id,
        _branch_filter(MenuItem, branch_id),
    )
    if menu_id:
        query = query.filter(MenuItem.menu_id == menu_id)
    if cuisine_id:
        query = query.filter(MenuItem.cuisine_id == cuisine_id)
    if food_type:
        query = query.filter(MenuItem.food_type == food_type)
    if category_id:
        sub_ids = [
            c.id
            for c in db.query(MenuCategory.id)
            .filter(
                MenuCategory.tenant_id == current_user.tenant_id,
                MenuCategory.parent_id == category_id,
            )
            .all()
        ]
        query = query.filter(MenuItem.category_id.in_([category_id, *sub_ids]))
    if is_combo is not None:
        query = query.filter(MenuItem.is_combo == is_combo)
    if search:
        query = query.filter(MenuItem.name.ilike(f"%{search}%"))
    if is_veg is not None:
        query = query.filter(MenuItem.is_veg == is_veg)

    items = query.order_by(MenuItem.display_order.asc(), MenuItem.name.asc()).all()
    serialized = []
    for it in items:
        data = _serialize_item(it, db, branch_id)
        if available_only and not data["is_available"]:
            continue
        if customer_site_only and not data["show_on_customer_site"]:
            continue
        if order_channel and order_channel not in (data["order_channels"] or []):
            continue
        serialized.append(data)
    return serialized


@router.post("/items", response_model=MenuItemResponse)
def create_menu_item(
    data: MenuItemCreate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(MenuCategory)
        .filter(MenuCategory.id == data.category_id, MenuCategory.tenant_id == current_user.tenant_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Item category not found")

    if data.cuisine_id:
        cuisine = (
            db.query(Cuisine)
            .filter(Cuisine.id == data.cuisine_id, Cuisine.tenant_id == current_user.tenant_id)
            .first()
        )
        if not cuisine:
            raise HTTPException(status_code=404, detail="Cuisine not found")

    ftype, veg_flag = _normalize_food_type(data.food_type, data.is_veg)
    resolved_branch_id = None if data.all_branches else (data.branch_id if data.branch_id is not None else branch_id)

    item = MenuItem(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=resolved_branch_id,
        menu_id=data.menu_id,
        cuisine_id=data.cuisine_id,
        category_id=data.category_id,
        name=data.name.strip(),
        sku=data.sku,
        description=data.description,
        image_url=data.image_url,
        base_price=data.base_price,
        cost_price=data.cost_price,
        tax_rate=data.tax_rate,
        preparation_time=data.preparation_time,
        display_order=data.display_order,
        is_available=data.is_available,
        show_on_customer_site=data.show_on_customer_site,
        food_type=ftype,
        is_veg=veg_flag,
        calories=data.calories,
        kitchen_station_id=data.kitchen_station_id,
        order_channels=data.order_channels or ["DineIn", "Takeaway", "Delivery", "QR"],
        spice_levels=data.spice_levels or [],
        is_combo=data.is_combo,
    )
    db.add(item)
    db.flush()

    for v in data.variants:
        db.add(
            ItemVariant(
                id=str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                item_id=item.id,
                name=v.name,
                price=v.price,
                sku=v.sku,
                is_available=v.is_available,
            )
        )

    for mg in data.modifier_groups:
        group = ItemModifierGroup(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            item_id=item.id,
            name=mg.name,
            min_selection=mg.min_selection,
            max_selection=mg.max_selection,
        )
        db.add(group)
        db.flush()

        for m in mg.modifiers:
            db.add(
                ItemModifier(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    group_id=group.id,
                    name=m.name,
                    price=m.price,
                    is_available=m.is_available,
                )
            )

    if data.branch_configs:
        _sync_branch_configs(db, current_user.tenant_id, item.id, data.branch_configs)

    if data.is_combo and data.combo_components:
        _sync_combo_components(db, current_user.tenant_id, item.id, data.combo_components)

    db.commit()
    db.refresh(item)
    return _serialize_item(item, db, branch_id)


@router.put("/items/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: str,
    data: MenuItemUpdate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id, MenuItem.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    updates = data.model_dump(exclude_unset=True)
    all_branches_flag = updates.pop("all_branches", None)
    variants_in = updates.pop("variants", None)
    branch_configs_in = updates.pop("branch_configs", None)
    combo_in = updates.pop("combo_components", None)

    if all_branches_flag is True:
        updates["branch_id"] = None
    elif all_branches_flag is False and "branch_id" not in updates and branch_id and item.branch_id is None:
        updates["branch_id"] = branch_id

    if "food_type" in updates or "is_veg" in updates:
        ftype, veg_flag = _normalize_food_type(
            updates.get("food_type"),
            updates.get("is_veg") if "food_type" not in updates else None,
        )
        updates["food_type"] = ftype
        updates["is_veg"] = veg_flag

    for field, val in updates.items():
        setattr(item, field, val)

    if variants_in is not None:
        db.query(ItemVariant).filter(
            ItemVariant.item_id == item.id,
            ItemVariant.tenant_id == current_user.tenant_id,
        ).delete()
        for v in data.variants or []:
            db.add(
                ItemVariant(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    item_id=item.id,
                    name=v.name,
                    price=v.price,
                    sku=v.sku,
                    is_available=v.is_available,
                )
            )

    if branch_configs_in is not None:
        _sync_branch_configs(db, current_user.tenant_id, item.id, data.branch_configs or [])

    if combo_in is not None:
        _sync_combo_components(db, current_user.tenant_id, item.id, data.combo_components or [])

    db.commit()
    db.refresh(item)
    return _serialize_item(item, db, branch_id)


@router.delete("/items/{item_id}")
def delete_menu_item(
    item_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id, MenuItem.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    name = item.name
    db.delete(item)
    db.commit()
    return {"message": f"Deleted menu item '{name}'"}


@router.patch("/items/{item_id}/toggle-availability")
def toggle_item_availability(
    item_id: str,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id, MenuItem.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if branch_id:
        cfg = (
            db.query(MenuItemBranchConfig)
            .filter(
                MenuItemBranchConfig.tenant_id == current_user.tenant_id,
                MenuItemBranchConfig.menu_item_id == item.id,
                MenuItemBranchConfig.branch_id == branch_id,
            )
            .first()
        )
        if cfg:
            cfg.is_available = not cfg.is_available
            if item.branch_id == branch_id or item.branch_id is None:
                item.is_available = cfg.is_available
            db.commit()
            return {"id": item.id, "name": item.name, "is_available": cfg.is_available}

    item.is_available = not item.is_available
    db.commit()
    return {"id": item.id, "name": item.name, "is_available": item.is_available}


@router.patch("/items/{item_id}/toggle-customer-site")
def toggle_item_customer_site(
    item_id: str,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id, MenuItem.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if branch_id:
        cfg = (
            db.query(MenuItemBranchConfig)
            .filter(
                MenuItemBranchConfig.tenant_id == current_user.tenant_id,
                MenuItemBranchConfig.menu_item_id == item.id,
                MenuItemBranchConfig.branch_id == branch_id,
            )
            .first()
        )
        if cfg:
            cfg.show_on_customer_site = not cfg.show_on_customer_site
            if item.branch_id == branch_id or item.branch_id is None:
                item.show_on_customer_site = cfg.show_on_customer_site
            db.commit()
            return {
                "id": item.id,
                "name": item.name,
                "show_on_customer_site": cfg.show_on_customer_site,
            }

    item.show_on_customer_site = not item.show_on_customer_site
    db.commit()
    return {
        "id": item.id,
        "name": item.name,
        "show_on_customer_site": item.show_on_customer_site,
    }


# ---------------------------------------------------------------------------
# Modifier Groups
# ---------------------------------------------------------------------------

@router.get("/modifier-groups", response_model=List[ItemModifierGroupResponse])
def list_modifier_groups(
    item_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ItemModifierGroup).filter(ItemModifierGroup.tenant_id == current_user.tenant_id)
    if item_id:
        query = query.filter(ItemModifierGroup.item_id == item_id)
    groups = query.order_by(ItemModifierGroup.name.asc()).all()
    return [
        {
            "id": g.id,
            "item_id": g.item_id,
            "item_name": g.item.name if g.item else None,
            "name": g.name,
            "min_selection": g.min_selection,
            "max_selection": g.max_selection,
            "modifiers": [
                {
                    "id": m.id,
                    "group_id": m.group_id,
                    "group_name": g.name,
                    "item_id": g.item_id,
                    "item_name": g.item.name if g.item else None,
                    "name": m.name,
                    "price": float(m.price),
                    "is_available": bool(m.is_available),
                }
                for m in (g.modifiers or [])
            ],
        }
        for g in groups
    ]


@router.post("/modifier-groups", response_model=ItemModifierGroupResponse)
def create_modifier_group(
    data: ModifierGroupStandaloneCreate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == data.item_id, MenuItem.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Target menu item not found")

    group = ItemModifierGroup(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        item_id=item.id,
        name=data.name,
        min_selection=data.min_selection,
        max_selection=data.max_selection,
    )
    db.add(group)
    db.flush()

    for m in data.modifiers:
        db.add(
            ItemModifier(
                id=str(uuid.uuid4()),
                tenant_id=current_user.tenant_id,
                group_id=group.id,
                name=m.name,
                price=m.price,
                is_available=m.is_available,
            )
        )

    db.commit()
    db.refresh(group)
    return {
        "id": group.id,
        "item_id": group.item_id,
        "item_name": item.name,
        "name": group.name,
        "min_selection": group.min_selection,
        "max_selection": group.max_selection,
        "modifiers": [
            {
                "id": m.id,
                "group_id": m.group_id,
                "group_name": group.name,
                "item_id": item.id,
                "item_name": item.name,
                "name": m.name,
                "price": float(m.price),
                "is_available": bool(m.is_available),
            }
            for m in (group.modifiers or [])
        ],
    }


@router.put("/modifier-groups/{group_id}", response_model=ItemModifierGroupResponse)
def update_modifier_group(
    group_id: str,
    data: ModifierGroupUpdate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    group = (
        db.query(ItemModifierGroup)
        .filter(ItemModifierGroup.id == group_id, ItemModifierGroup.tenant_id == current_user.tenant_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(group, field, val)
    db.commit()
    db.refresh(group)
    return {
        "id": group.id,
        "item_id": group.item_id,
        "item_name": group.item.name if group.item else None,
        "name": group.name,
        "min_selection": group.min_selection,
        "max_selection": group.max_selection,
        "modifiers": [
            {
                "id": m.id,
                "group_id": m.group_id,
                "group_name": group.name,
                "item_id": group.item_id,
                "item_name": group.item.name if group.item else None,
                "name": m.name,
                "price": float(m.price),
                "is_available": bool(m.is_available),
            }
            for m in (group.modifiers or [])
        ],
    }


@router.delete("/modifier-groups/{group_id}")
def delete_modifier_group(
    group_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    group = (
        db.query(ItemModifierGroup)
        .filter(ItemModifierGroup.id == group_id, ItemModifierGroup.tenant_id == current_user.tenant_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    name = group.name
    db.delete(group)
    db.commit()
    return {"message": f"Deleted modifier group '{name}'"}


# ---------------------------------------------------------------------------
# Item Modifiers
# ---------------------------------------------------------------------------

@router.get("/modifiers", response_model=List[ItemModifierResponse])
def list_modifiers(
    group_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ItemModifier).filter(ItemModifier.tenant_id == current_user.tenant_id)
    if group_id:
        query = query.filter(ItemModifier.group_id == group_id)
    mods = query.order_by(ItemModifier.name.asc()).all()
    return [
        {
            "id": m.id,
            "group_id": m.group_id,
            "group_name": m.group.name if m.group else None,
            "item_id": m.group.item_id if m.group else None,
            "item_name": m.group.item.name if (m.group and m.group.item) else None,
            "name": m.name,
            "price": float(m.price),
            "is_available": bool(m.is_available),
        }
        for m in mods
    ]


@router.post("/modifiers", response_model=ItemModifierResponse)
def create_modifier(
    data: ItemModifierStandaloneCreate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    group = (
        db.query(ItemModifierGroup)
        .filter(ItemModifierGroup.id == data.group_id, ItemModifierGroup.tenant_id == current_user.tenant_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")

    mod = ItemModifier(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        group_id=group.id,
        name=data.name,
        price=data.price,
        is_available=data.is_available,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return {
        "id": mod.id,
        "group_id": mod.group_id,
        "group_name": group.name,
        "item_id": group.item_id,
        "item_name": group.item.name if group.item else None,
        "name": mod.name,
        "price": float(mod.price),
        "is_available": bool(mod.is_available),
    }


@router.put("/modifiers/{modifier_id}", response_model=ItemModifierResponse)
def update_modifier(
    modifier_id: str,
    data: ItemModifierUpdate,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    mod = (
        db.query(ItemModifier)
        .filter(ItemModifier.id == modifier_id, ItemModifier.tenant_id == current_user.tenant_id)
        .first()
    )
    if not mod:
        raise HTTPException(status_code=404, detail="Item modifier not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(mod, field, val)
    db.commit()
    db.refresh(mod)
    return {
        "id": mod.id,
        "group_id": mod.group_id,
        "group_name": mod.group.name if mod.group else None,
        "item_id": mod.group.item_id if mod.group else None,
        "item_name": mod.group.item.name if (mod.group and mod.group.item) else None,
        "name": mod.name,
        "price": float(mod.price),
        "is_available": bool(mod.is_available),
    }


@router.patch("/modifiers/{modifier_id}/toggle-availability")
def toggle_modifier_availability(
    modifier_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    mod = (
        db.query(ItemModifier)
        .filter(ItemModifier.id == modifier_id, ItemModifier.tenant_id == current_user.tenant_id)
        .first()
    )
    if not mod:
        raise HTTPException(status_code=404, detail="Item modifier not found")
    mod.is_available = not mod.is_available
    db.commit()
    return {"id": mod.id, "name": mod.name, "is_available": mod.is_available}


@router.delete("/modifiers/{modifier_id}")
def delete_modifier(
    modifier_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    mod = (
        db.query(ItemModifier)
        .filter(ItemModifier.id == modifier_id, ItemModifier.tenant_id == current_user.tenant_id)
        .first()
    )
    if not mod:
        raise HTTPException(status_code=404, detail="Item modifier not found")
    name = mod.name
    db.delete(mod)
    db.commit()
    return {"message": f"Deleted item modifier '{name}'"}


# ---------------------------------------------------------------------------
# Menus Root & Dynamic ID Routes (MUST remain after static subpaths)
# ---------------------------------------------------------------------------

@router.get("", response_model=List[MenuSummaryResponse])
def list_menus(
    search: Optional[str] = None,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Menu).filter(
        Menu.tenant_id == current_user.tenant_id,
        Menu.is_active == True,
        _branch_filter(Menu, branch_id),
    )
    if search:
        query = query.filter(Menu.name.ilike(f"%{search}%"))
    menus = query.order_by(Menu.display_order.asc(), Menu.name.asc()).all()
    return [_serialize_menu(m, db, branch_id) for m in menus]


@router.post("", response_model=MenuSummaryResponse)
def create_menu(
    data: MenuCreate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    menu = Menu(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        branch_id=data.branch_id or branch_id,
        name=data.name.strip(),
        description=data.description,
        schedule_type=data.schedule_type,
        available_from=data.available_from,
        available_to=data.available_to,
        active_days=data.active_days,
        display_order=data.display_order,
        is_active=data.is_active,
    )
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return _serialize_menu(menu, db, branch_id)


@router.put("/{menu_id}", response_model=MenuSummaryResponse)
def update_menu(
    menu_id: str,
    data: MenuUpdate,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    menu = (
        db.query(Menu)
        .filter(Menu.id == menu_id, Menu.tenant_id == current_user.tenant_id)
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(menu, field, val)
    db.commit()
    db.refresh(menu)
    return _serialize_menu(menu, db, branch_id)


@router.delete("/{menu_id}")
def delete_menu(
    menu_id: str,
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    menu = (
        db.query(Menu)
        .filter(Menu.id == menu_id, Menu.tenant_id == current_user.tenant_id)
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    db.query(MenuItem).filter(
        MenuItem.tenant_id == current_user.tenant_id,
        MenuItem.menu_id == menu.id,
    ).update({"menu_id": None})
    db.query(RestaurantTable).filter(
        RestaurantTable.tenant_id == current_user.tenant_id,
        RestaurantTable.assigned_menu_id == menu.id,
    ).update({"assigned_menu_id": None})

    name = menu.name
    db.delete(menu)
    db.commit()
    return {"message": f"Deleted menu '{name}'"}


@router.post("/{menu_id}/assign-tables")
def assign_menu_to_tables(
    menu_id: str,
    data: AssignMenuTablesRequest,
    branch_id: Optional[str] = Depends(get_optional_branch_id),
    current_user=Depends(require_permission(Permission.MANAGE_MENU)),
    db: Session = Depends(get_db),
):
    menu = (
        db.query(Menu)
        .filter(Menu.id == menu_id, Menu.tenant_id == current_user.tenant_id)
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    tables_query = db.query(RestaurantTable).filter(RestaurantTable.tenant_id == current_user.tenant_id)
    if branch_id:
        tables_query = tables_query.filter(RestaurantTable.branch_id == branch_id)
    branch_tables = tables_query.all()

    selected_set = set(data.table_ids)
    assigned_count = 0
    for tbl in branch_tables:
        if tbl.id in selected_set:
            tbl.assigned_menu_id = menu.id
            assigned_count += 1
        elif tbl.assigned_menu_id == menu.id:
            tbl.assigned_menu_id = None

    db.commit()
    return {
        "message": f"Assigned '{menu.name}' to {assigned_count} table(s)",
        "menu_id": menu.id,
        "assigned_table_ids": [t.id for t in branch_tables if t.assigned_menu_id == menu.id],
    }
