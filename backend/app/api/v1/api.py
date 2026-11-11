from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.platform import router as platform_router
from app.api.v1.branches import router as branches_router
from app.api.v1.users import router as users_router
from app.api.v1.menus import router as menus_router
from app.api.v1.tables import router as tables_router
from app.api.v1.reservations import router as reservations_router
from app.api.v1.orders import router as orders_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.kitchens import router as kitchens_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.recipes import router as recipes_router
from app.api.v1.procurement import router as procurement_router
from app.api.v1.crm import router as crm_router
from app.api.v1.loyalty import router as loyalty_router
from app.api.v1.cash_registers import router as cash_registers_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.reports import router as reports_router
from app.api.v1.customer_ordering import router as customer_ordering_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(platform_router, prefix="/platform", tags=["Platform Super Admin"])
api_router.include_router(branches_router, prefix="/branches", tags=["Branches"])
api_router.include_router(users_router, prefix="/users", tags=["Users & Staff"])
api_router.include_router(menus_router, prefix="/menus", tags=["Menus & Items"])
api_router.include_router(tables_router, prefix="/tables", tags=["Dining Tables & Areas"])
api_router.include_router(reservations_router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(orders_router, prefix="/orders", tags=["POS & Orders"])
api_router.include_router(invoices_router, prefix="/invoices", tags=["Billing & Invoices"])
api_router.include_router(kitchens_router, prefix="/kitchens", tags=["Kitchen KDS & KOT"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory Management"])
api_router.include_router(recipes_router, prefix="/recipes", tags=["Recipes & BOM"])
api_router.include_router(procurement_router, prefix="/procurement", tags=["Suppliers & Purchasing"])
api_router.include_router(crm_router, prefix="/crm", tags=["Customer CRM"])
api_router.include_router(loyalty_router, prefix="/loyalty", tags=["Loyalty Ledger"])
api_router.include_router(cash_registers_router, prefix="/cash-registers", tags=["Cash Registers & Shifts"])
api_router.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(delivery_router, prefix="/delivery", tags=["Delivery Management"])
api_router.include_router(reports_router, prefix="/reports", tags=["Analytics & Reports"])
api_router.include_router(customer_ordering_router, prefix="/public", tags=["Public Customer Ordering"])
