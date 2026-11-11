from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.inventory import Recipe, RecipeItem, InventoryItem
from app.models.menu import MenuItem
from app.schemas.inventory import RecipeCreate, RecipeResponse

router = APIRouter()

@router.get("/{menu_item_id}", response_model=RecipeResponse)
def get_recipe_for_item(
    menu_item_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipe = db.query(Recipe).filter(
        Recipe.menu_item_id == menu_item_id,
        Recipe.tenant_id == current_user.tenant_id
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found for this menu item")

    items_data = []
    for ri in recipe.items:
        inv = db.query(InventoryItem).filter(InventoryItem.id == ri.inventory_item_id).first()
        items_data.append({
            "id": ri.id,
            "inventory_item_id": ri.inventory_item_id,
            "item_name": inv.name if inv else "Unknown",
            "quantity": float(ri.quantity),
            "uom": ri.uom
        })

    return RecipeResponse(
        id=recipe.id,
        menu_item_id=recipe.menu_item_id,
        yield_portions=recipe.yield_portions,
        preparation_loss_percent=float(recipe.preparation_loss_percent),
        instructions=recipe.instructions,
        items=items_data
    )

@router.post("", response_model=RecipeResponse)
def create_or_update_recipe(
    data: RecipeCreate,
    current_user = Depends(require_permission(Permission.MANAGE_RECIPES)),
    db: Session = Depends(get_db)
):
    menu_item = db.query(MenuItem).filter(
        MenuItem.id == data.menu_item_id,
        MenuItem.tenant_id == current_user.tenant_id
    ).first()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    recipe = db.query(Recipe).filter(Recipe.menu_item_id == data.menu_item_id).first()
    if not recipe:
        recipe = Recipe(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            menu_item_id=data.menu_item_id,
            yield_portions=data.yield_portions,
            preparation_loss_percent=Decimal(str(data.preparation_loss_percent)),
            instructions=data.instructions
        )
        db.add(recipe)
        db.flush()
    else:
        recipe.yield_portions = data.yield_portions
        recipe.preparation_loss_percent = Decimal(str(data.preparation_loss_percent))
        recipe.instructions = data.instructions
        # Clear existing items
        db.query(RecipeItem).filter(RecipeItem.recipe_id == recipe.id).delete()

    calculated_cost = Decimal("0.00")
    items_data = []
    for ri in data.items:
        inv = db.query(InventoryItem).filter(InventoryItem.id == ri.inventory_item_id).first()
        if not inv:
            continue
            
        recipe_item = RecipeItem(
            id=str(uuid.uuid4()),
            recipe_id=recipe.id,
            inventory_item_id=ri.inventory_item_id,
            quantity=Decimal(str(ri.quantity)),
            uom=ri.uom
        )
        db.add(recipe_item)
        
        # Approximate cost calculation
        calculated_cost += Decimal(str(ri.quantity)) * Decimal(str(inv.cost_per_unit))
        items_data.append({
            "id": recipe_item.id,
            "inventory_item_id": ri.inventory_item_id,
            "item_name": inv.name,
            "quantity": ri.quantity,
            "uom": ri.uom
        })

    # Update menu item cost price snapshot for profit margin calculations
    menu_item.cost_price = calculated_cost / Decimal(str(data.yield_portions or 1))
    db.commit()
    db.refresh(recipe)

    return RecipeResponse(
        id=recipe.id,
        menu_item_id=recipe.menu_item_id,
        yield_portions=recipe.yield_portions,
        preparation_loss_percent=float(recipe.preparation_loss_percent),
        instructions=recipe.instructions,
        items=items_data
    )
