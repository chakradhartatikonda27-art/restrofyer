import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.schema_sync import ensure_schema_columns
from app.core.security import get_password_hash
from app.models.saas import PlatformUser, Tenant, SubscriptionPlan, Subscription, SubscriptionInvoice, PlatformAuditLog
from app.models.organization import Branch, User, BranchMembership, AuditLog
from app.models.menu import (
    Cuisine,
    Menu,
    MenuCategory,
    MenuItem,
    ItemVariant,
    ItemModifierGroup,
    ItemModifier,
    MenuItemBranchConfig,
    ComboMealItem,
)
from app.services.menu_template_service import (
    apply_indian_menu_template,
    resolve_default_indian_dish_image,
)
from app.models.table import DiningArea, RestaurantTable, Reservation
from app.models.kitchen import Kitchen, KitchenStation, KOT, KOTItem
from app.models.order import Order, OrderItem, Invoice, Payment
from app.models.inventory import InventoryCategory, InventoryItem, StockMovement, Recipe, RecipeItem
from app.models.procurement import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt
from app.models.crm import Customer, CustomerAddress, LoyaltyAccount, LoyaltyTransaction
from app.models.financial import CashRegister, CashRegisterSession, CashTransaction, Expense
from app.models.delivery import DeliveryExecutive, DeliveryOrder


SEED_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _seed_id(key: str) -> str:
    """Deterministic UUIDv5 so serverless cold starts preserve stable seeded auth IDs."""
    return str(uuid.uuid5(SEED_NAMESPACE, key))


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(PlatformUser).filter(PlatformUser.email == "admin@restaurantsaas.com").first():
            print("Database already contains seed data. Skipping.")
            return

        print("--- Seeding SaaS Multi-Tenant Platform Data ---")

        # 1. Platform Super Admin
        super_admin = PlatformUser(
            id=_seed_id("platform:admin@restaurantsaas.com"),
            email="admin@restaurantsaas.com",
            password_hash=get_password_hash("SuperAdmin@2026!"),
            full_name="Platform Super Administrator",
            role="SUPER_ADMIN",
            is_active=True
        )
        db.add(super_admin)

        # 2. Subscription Plans
        plan_starter = SubscriptionPlan(
            id=_seed_id("plan:starter"),
            name="Starter Plan",
            code="starter",
            description="Essential POS, Menu, and Billing for single location restaurants and cafes.",
            monthly_price=Decimal("49.00"),
            annual_price=Decimal("490.00"),
            branch_limit=1,
            user_limit=5,
            pos_terminal_limit=2,
            features={"pos": True, "tables": True, "invoicing": True, "reports_basic": True}
        )
        plan_growth = SubscriptionPlan(
            id=_seed_id("plan:growth"),
            name="Growth Plan",
            code="growth",
            description="Complete restaurant operations with KDS, Inventory, and CRM for growing bistros.",
            monthly_price=Decimal("99.00"),
            annual_price=Decimal("990.00"),
            branch_limit=3,
            user_limit=15,
            pos_terminal_limit=6,
            features={"pos": True, "tables": True, "kds": True, "inventory": True, "crm": True, "reports_sales": True}
        )
        plan_pro = SubscriptionPlan(
            id=_seed_id("plan:pro"),
            name="Professional Plan",
            code="pro",
            description="Advanced multi-branch chain management with Recipe BOM, Loyalty Ledger, and QR Ordering.",
            monthly_price=Decimal("199.00"),
            annual_price=Decimal("1990.00"),
            branch_limit=10,
            user_limit=40,
            pos_terminal_limit=15,
            features={"pos": True, "tables": True, "kds": True, "inventory": True, "recipes": True, "loyalty": True, "qr_ordering": True, "delivery": True, "reports_financial": True}
        )
        plan_enterprise = SubscriptionPlan(
            id=_seed_id("plan:enterprise"),
            name="Enterprise Global",
            code="enterprise",
            description="Unlimited locations, custom integrations, API access, and dedicated support.",
            monthly_price=Decimal("399.00"),
            annual_price=Decimal("3990.00"),
            branch_limit=100,
            user_limit=500,
            pos_terminal_limit=100,
            features={"all": True}
        )
        db.add_all([plan_starter, plan_growth, plan_pro, plan_enterprise])
        db.flush()

        # 3. Tenant 1: Bella Napoli Trattoria (Flagship Multi-branch)
        tenant_1 = Tenant(
            id=_seed_id("tenant:bella-napoli"),
            name="Bella Napoli Trattoria",
            slug="bella-napoli",
            business_type="Fine Dining Italian",
            status="Active",
            contact_email="marco@bellanapoli.com",
            contact_phone="+91 98765 43210",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
            onboarding_completed=True,
            onboarding_step=5
        )
        db.add(tenant_1)
        db.flush()

        # Subscription for Tenant 1
        sub_1 = Subscription(
            id=_seed_id("sub:bella-napoli"),
            tenant_id=tenant_1.id,
            plan_id=plan_pro.id,
            status="Active",
            billing_cycle="monthly",
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15)
        )
        db.add(sub_1)

        # Branches for Tenant 1
        branch_1a = Branch(
            id=_seed_id("branch:bella-napoli:BN-JH-01"),
            tenant_id=tenant_1.id,
            name="Bella Napoli - Jubilee Hills",
            code="BN-JH-01",
            phone="+91 40 2355 1200",
            email="jubileehills@bellanapoli.com",
            address="Plot 42, Road No. 36, Jubilee Hills",
            city="Hyderabad",
            state="Telangana",
            postal_code="500033",
            tax_rate=Decimal("5.00"),
            service_charge_rate=Decimal("2.50"),
            currency="INR",
            is_active=True
        )
        branch_1b = Branch(
            id=_seed_id("branch:bella-napoli:BN-HC-02"),
            tenant_id=tenant_1.id,
            name="Bella Napoli - Hitec City",
            code="BN-HC-02",
            phone="+91 40 4850 7800",
            email="hiteccity@bellanapoli.com",
            address="Ground Floor, Cyber Towers, Hitec City",
            city="Hyderabad",
            state="Telangana",
            postal_code="500081",
            tax_rate=Decimal("5.00"),
            service_charge_rate=Decimal("0.00"),
            currency="INR",
            is_active=True
        )
        db.add_all([branch_1a, branch_1b])
        db.flush()

        # Users for Tenant 1
        user_owner = User(
            id=_seed_id("user:marco@bellanapoli.com"),
            tenant_id=tenant_1.id,
            email="marco@bellanapoli.com",
            password_hash=get_password_hash("Owner@123"),
            full_name="Marco Rossi",
            role="TENANT_OWNER",
            phone="+91 98765 43210",
            branch_id=branch_1a.id,
            is_active=True
        )
        user_manager = User(
            id=_seed_id("user:sophia@bellanapoli.com"),
            tenant_id=tenant_1.id,
            email="sophia@bellanapoli.com",
            password_hash=get_password_hash("Manager@123"),
            full_name="Sophia Bianchi",
            role="BRANCH_MANAGER",
            phone="+91 98765 43211",
            branch_id=branch_1a.id,
            is_active=True
        )
        user_cashier = User(
            id=_seed_id("user:lucas@bellanapoli.com"),
            tenant_id=tenant_1.id,
            email="lucas@bellanapoli.com",
            password_hash=get_password_hash("Cashier@123"),
            full_name="Lucas D'Souza",
            role="CASHIER",
            phone="+91 98765 43212",
            branch_id=branch_1a.id,
            is_active=True
        )
        user_waiter = User(
            id=_seed_id("user:giovanni@bellanapoli.com"),
            tenant_id=tenant_1.id,
            email="giovanni@bellanapoli.com",
            password_hash=get_password_hash("Waiter@123"),
            full_name="Giovanni Kumar",
            role="WAITER",
            phone="+91 98765 43213",
            branch_id=branch_1a.id,
            is_active=True
        )
        user_chef = User(
            id=_seed_id("user:mario@bellanapoli.com"),
            tenant_id=tenant_1.id,
            email="mario@bellanapoli.com",
            password_hash=get_password_hash("Chef@123"),
            full_name="Chef Mario Conti",
            role="KITCHEN_MANAGER",
            phone="+91 98765 43214",
            branch_id=branch_1a.id,
            is_active=True
        )
        db.add_all([user_owner, user_manager, user_cashier, user_waiter, user_chef])
        db.flush()

        # Dining Areas & Tables for Branch 1a
        area_indoor = DiningArea(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Main Dining Room", display_order=1)
        area_terrace = DiningArea(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Rooftop Terrace", display_order=2)
        area_vip = DiningArea(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="VIP Cantina", display_order=3)
        db.add_all([area_indoor, area_terrace, area_vip])
        db.flush()

        tables = [
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_indoor.id, table_number="T-01", name="Window 1", capacity=2, status="Available", pos_x=50, pos_y=50, qr_code_token="QR-BELLA-T01"),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_indoor.id, table_number="T-02", name="Window 2", capacity=4, status="Occupied", pos_x=200, pos_y=50, qr_code_token="QR-BELLA-T02", occupied_since=datetime.utcnow() - timedelta(minutes=35)),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_indoor.id, table_number="T-03", name="Center Booth", capacity=6, status="Occupied", pos_x=350, pos_y=50, qr_code_token="QR-BELLA-T03", occupied_since=datetime.utcnow() - timedelta(minutes=15)),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_indoor.id, table_number="T-04", name="Pillar Table", capacity=4, status="Reserved", pos_x=500, pos_y=50, qr_code_token="QR-BELLA-T04"),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_terrace.id, table_number="T-05", name="Terrace View 1", capacity=4, status="Available", pos_x=100, pos_y=150, qr_code_token="QR-BELLA-T05"),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_terrace.id, table_number="T-06", name="Terrace View 2", capacity=2, status="Cleaning", pos_x=250, pos_y=150, qr_code_token="QR-BELLA-T06"),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, area_id=area_vip.id, table_number="V-01", name="Presidential Suite", capacity=10, status="Available", pos_x=400, pos_y=150, qr_code_token="QR-BELLA-V01")
        ]
        db.add_all(tables)
        db.flush()

        # Kitchen & Stations
        kitchen_main = Kitchen(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Bella Cucina Main")
        db.add(kitchen_main)
        db.flush()

        station_pizza = KitchenStation(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, kitchen_id=kitchen_main.id, name="Woodfire Pizza Station", printer_ip="192.168.1.101")
        station_pasta = KitchenStation(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, kitchen_id=kitchen_main.id, name="Fresh Pasta & Grill", printer_ip="192.168.1.102")
        station_bar = KitchenStation(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, kitchen_id=kitchen_main.id, name="Bar & Beverage", printer_ip="192.168.1.103")
        db.add_all([station_pizza, station_pasta, station_bar])
        db.flush()

        # Cuisines for Bella Napoli
        cui_bn_italian = Cuisine(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Italian", description="Woodfired Neapolitan pizzas, fresh pasta & dolce", display_order=1, is_active=True)
        cui_bn_continental = Cuisine(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Continental", description="Artisanal starters & beverages", display_order=2, is_active=True)
        db.add_all([cui_bn_italian, cui_bn_continental])
        db.flush()

        # Menus for Bella Napoli (Branch 1a)
        menu_bn_pizza = Menu(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Woodfired Pizzas", description="450°C woodfired Neapolitan pies", schedule_type="AllDay", display_order=1, is_active=True)
        menu_bn_pasta = Menu(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Artisanal Pasta", description="Hand-rolled fresh Italian pasta", schedule_type="AllDay", display_order=2, is_active=True)
        menu_bn_antipasti = Menu(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Antipasti & Starters", description="Small plates & bruschetta", schedule_type="AllDay", display_order=3, is_active=True)
        menu_bn_dolci = Menu(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Dolci & Desserts", description="Traditional Italian sweets", schedule_type="AllDay", display_order=4, is_active=True)
        menu_bn_drinks = Menu(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Beverages & Wine", description="Mineral waters & craft spritz", schedule_type="AllDay", display_order=5, is_active=True)
        db.add_all([menu_bn_pizza, menu_bn_pasta, menu_bn_antipasti, menu_bn_dolci, menu_bn_drinks])
        db.flush()

        # Menu Categories
        cat_antipasti = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, menu_id=menu_bn_antipasti.id, name="Antipasti & Starters", display_order=1, icon="UtensilsCrossed")
        cat_pizza = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, menu_id=menu_bn_pizza.id, name="Woodfired Pizzas", display_order=2, icon="Flame")
        cat_pasta = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, menu_id=menu_bn_pasta.id, name="Artisanal Pasta", display_order=3, icon="Soup")
        cat_desserts = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, menu_id=menu_bn_dolci.id, name="Dolci & Desserts", display_order=4, icon="Cake")
        cat_drinks = MenuCategory(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, menu_id=menu_bn_drinks.id, name="Beverages & Wine", display_order=5, icon="GlassWater")
        db.add_all([cat_antipasti, cat_pizza, cat_pasta, cat_desserts, cat_drinks])
        db.flush()

        # Menu Items
        item_margherita = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_pizza.id,
            category_id=cat_pizza.id,
            cuisine_id=cui_bn_italian.id,
            food_type="VEG",
            name="Margherita D.O.P.",
            sku="PIZ-MARG-01",
            description="San Marzano tomato sauce, fresh buffalo mozzarella, fresh basil, organic olive oil.",
            base_price=Decimal("495.00"),
            cost_price=Decimal("135.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=12,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            spice_levels=["Mild"],
            kitchen_station_id=station_pizza.id
        )
        item_truffle = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_pizza.id,
            category_id=cat_pizza.id,
            cuisine_id=cui_bn_italian.id,
            food_type="VEG",
            name="Tartufo & Funghi Pizza",
            sku="PIZ-TRUF-02",
            description="Wild forest mushrooms, fior di latte, black truffle cream, thyme.",
            base_price=Decimal("695.00"),
            cost_price=Decimal("210.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=14,
            display_order=2,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            spice_levels=["Mild"],
            kitchen_station_id=station_pizza.id
        )
        item_alfredo = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_pasta.id,
            category_id=cat_pasta.id,
            cuisine_id=cui_bn_italian.id,
            food_type="VEG",
            name="Fettuccine ai Funghi",
            sku="PAS-FETT-01",
            description="Fresh egg pasta tossed with porcini mushrooms, parmesan cream, and cracked pepper.",
            base_price=Decimal("545.00"),
            cost_price=Decimal("140.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=15,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            spice_levels=["Mild"],
            kitchen_station_id=station_pasta.id
        )
        item_bruschetta = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_antipasti.id,
            category_id=cat_antipasti.id,
            cuisine_id=cui_bn_italian.id,
            food_type="VEGAN",
            name="Bruschetta Pomodoro",
            sku="ANT-BRUS-01",
            description="Toasted sourdough topped with heirloom tomatoes, garlic, extra virgin olive oil, and balsamic glaze.",
            base_price=Decimal("345.00"),
            cost_price=Decimal("75.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=8,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            spice_levels=["Mild"],
            kitchen_station_id=station_pasta.id
        )
        item_tiramisu = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_dolci.id,
            category_id=cat_desserts.id,
            cuisine_id=cui_bn_italian.id,
            food_type="VEG",
            name="Classic Tiramisù",
            sku="DES-TIRA-01",
            description="Savoiardi soaked in espresso, mascarpone mousse, dusted with Valrhona cocoa.",
            base_price=Decimal("385.00"),
            cost_price=Decimal("95.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=5,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            kitchen_station_id=station_bar.id
        )
        item_soda = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            menu_id=menu_bn_drinks.id,
            category_id=cat_drinks.id,
            cuisine_id=cui_bn_continental.id,
            food_type="VEGAN",
            name="San Pellegrino Sparkling 750ml",
            sku="DRK-PELLE-01",
            description="Sparkling natural Italian mineral water.",
            base_price=Decimal("295.00"),
            cost_price=Decimal("120.00"),
            tax_rate=Decimal("12.00"),
            preparation_time=2,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=True,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            kitchen_station_id=station_bar.id
        )
        db.add_all([item_margherita, item_truffle, item_alfredo, item_bruschetta, item_tiramisu, item_soda])
        db.flush()

        # Variants for Margherita
        var_reg = ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_1.id, item_id=item_margherita.id, name="Regular 10 inch", price=Decimal("495.00"), is_available=True)
        var_large = ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_1.id, item_id=item_margherita.id, name="Large 14 inch", price=Decimal("695.00"), is_available=True)
        db.add_all([var_reg, var_large])

        # Modifiers for Pizza
        mod_group = ItemModifierGroup(id=str(uuid.uuid4()), tenant_id=tenant_1.id, item_id=item_margherita.id, name="Extra Toppings", min_selection=0, max_selection=3)
        db.add(mod_group)
        db.flush()
        mod_cheese = ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_1.id, group_id=mod_group.id, name="Extra Buffalo Mozzarella", price=Decimal("80.00"), is_available=True)
        mod_jalapeno = ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_1.id, group_id=mod_group.id, name="Spicy Jalapeños", price=Decimal("40.00"), is_available=True)
        db.add_all([mod_cheese, mod_jalapeno])

        # Inventory Items (Raw Materials)
        inv_flour = InventoryItem(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Caputo '00' Pizza Flour", sku="INV-FLR-01", uom="kg", current_stock=Decimal("120.000"), minimum_stock=Decimal("30.000"), cost_per_unit=Decimal("95.00"), storage_location="Dry Pantry A1")
        inv_cheese = InventoryItem(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Fresh Buffalo Mozzarella", sku="INV-MOZZ-01", uom="kg", current_stock=Decimal("38.500"), minimum_stock=Decimal("15.000"), cost_per_unit=Decimal("420.00"), storage_location="Dairy Walk-in B")
        inv_tomatoes = InventoryItem(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="San Marzano Whole Peeled Tomatoes", sku="INV-TOM-01", uom="kg", current_stock=Decimal("45.000"), minimum_stock=Decimal("20.000"), cost_per_unit=Decimal("160.00"), storage_location="Dry Pantry A2")
        inv_oil = InventoryItem(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Extra Virgin Olive Oil", sku="INV-OIL-01", uom="l", current_stock=Decimal("28.000"), minimum_stock=Decimal("10.000"), cost_per_unit=Decimal("750.00"), storage_location="Dry Pantry A3")
        inv_truffle = InventoryItem(id=str(uuid.uuid4()), tenant_id=tenant_1.id, name="Black Truffle Pate", sku="INV-TRUF-01", uom="kg", current_stock=Decimal("3.200"), minimum_stock=Decimal("4.000"), cost_per_unit=Decimal("2400.00"), storage_location="Chilled Vault") # Low stock alert trigger!
        db.add_all([inv_flour, inv_cheese, inv_tomatoes, inv_oil, inv_truffle])
        db.flush()

        # Recipe BOM for Margherita D.O.P.
        recipe_marg = Recipe(id=str(uuid.uuid4()), tenant_id=tenant_1.id, menu_item_id=item_margherita.id, yield_portions=1, instructions="Stretch 250g dough, spread 120g sauce, top with 150g mozzarella and 15ml oil.")
        db.add(recipe_marg)
        db.flush()
        db.add_all([
            RecipeItem(id=str(uuid.uuid4()), recipe_id=recipe_marg.id, inventory_item_id=inv_flour.id, quantity=Decimal("0.250"), uom="kg"),
            RecipeItem(id=str(uuid.uuid4()), recipe_id=recipe_marg.id, inventory_item_id=inv_tomatoes.id, quantity=Decimal("0.120"), uom="kg"),
            RecipeItem(id=str(uuid.uuid4()), recipe_id=recipe_marg.id, inventory_item_id=inv_cheese.id, quantity=Decimal("0.150"), uom="kg"),
            RecipeItem(id=str(uuid.uuid4()), recipe_id=recipe_marg.id, inventory_item_id=inv_oil.id, quantity=Decimal("0.015"), uom="l"),
        ])

        # Suppliers
        sup_euro = Supplier(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            name="EuroFoods Artisanal Imports Ltd",
            contact_name="Stefano Rossi",
            email="orders@eurofoodsimports.com",
            phone="+91 91234 56789",
            address="Warehouse 14, Container Terminal, Mumbai",
            tax_number="27AAACE1234F1Z9",
            payment_terms="Net 30 Days"
        )
        sup_dairy = Supplier(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            name="Himalayan Artisanal Cheese Dairy",
            contact_name="Preeti Patel",
            email="sales@himalayanartisanal.com",
            phone="+91 99887 76655",
            address="Plot 8, Dairy Corridor, Pune",
            tax_number="27BBBCC2345G2Z8",
            payment_terms="Net 15 Days"
        )
        db.add_all([sup_euro, sup_dairy])
        db.flush()

        # Customers & Loyalty Accounts
        cust_vikram = Customer(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            name="Vikram Sharma",
            phone="+91 98490 11223",
            email="vikram.sharma@gmail.com",
            segment="VIP",
            total_spend=Decimal("12450.00"),
            total_visits=8,
            notes="Prefers corner window tables. Loves extra truffle drizzle."
        )
        cust_ananya = Customer(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            name="Ananya Rao",
            phone="+91 99590 33445",
            email="ananya.rao@outlook.com",
            segment="Returning",
            total_spend=Decimal("4200.00"),
            total_visits=3
        )
        db.add_all([cust_vikram, cust_ananya])
        db.flush()

        loyalty_vikram = LoyaltyAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            customer_id=cust_vikram.id,
            tier="Platinum",
            points_balance=1245
        )
        loyalty_ananya = LoyaltyAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            customer_id=cust_ananya.id,
            tier="Silver",
            points_balance=420
        )
        db.add_all([loyalty_vikram, loyalty_ananya])
        db.flush()

        # Cash Register & Open Shift Session
        register = CashRegister(id=str(uuid.uuid4()), tenant_id=tenant_1.id, branch_id=branch_1a.id, name="Front POS Register 01", status="Open")
        db.add(register)
        db.flush()

        session = CashRegisterSession(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            register_id=register.id,
            cashier_id=user_cashier.id,
            cashier_name=user_cashier.full_name,
            opening_float=Decimal("2000.00"),
            cash_sales=Decimal("3850.00"),
            cash_in=Decimal("500.00"),
            cash_out=Decimal("200.00"),
            cash_refunds=Decimal("0.00"),
            expected_closing_cash=Decimal("6150.00"),
            status="Open"
        )
        db.add(session)
        db.flush()

        # Sample Completed Order with Invoice & Payment
        order_prev = Order(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            order_number="ORD-261030-0001",
            order_type="DineIn",
            status="Completed",
            table_id=tables[1].id,
            table_number=tables[1].table_number,
            customer_id=cust_vikram.id,
            customer_name=cust_vikram.name,
            customer_phone=cust_vikram.phone,
            subtotal=Decimal("1735.00"),
            discount_amount=Decimal("100.00"),
            discount_reason="VIP Loyalty Discount",
            tax_amount=Decimal("81.75"),
            service_charge=Decimal("40.88"),
            total_amount=Decimal("1757.63"),
            cashier_id=user_cashier.id,
            cashier_name=user_cashier.full_name,
            waiter_id=user_waiter.id,
            waiter_name=user_waiter.full_name
        )
        db.add(order_prev)
        db.flush()

        oi_1 = OrderItem(id=str(uuid.uuid4()), order_id=order_prev.id, menu_item_id=item_margherita.id, item_name="Margherita D.O.P.", unit_price=Decimal("495.00"), quantity=2, subtotal=Decimal("990.00"))
        oi_2 = OrderItem(id=str(uuid.uuid4()), order_id=order_prev.id, menu_item_id=item_truffle.id, item_name="Tartufo & Funghi Pizza", unit_price=Decimal("695.00"), quantity=1, subtotal=Decimal("695.00"))
        oi_3 = OrderItem(id=str(uuid.uuid4()), order_id=order_prev.id, menu_item_id=item_soda.id, item_name="San Pellegrino Sparkling 750ml", unit_price=Decimal("295.00"), quantity=1, subtotal=Decimal("295.00"))
        db.add_all([oi_1, oi_2, oi_3])
        db.flush()

        inv_prev = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            order_id=order_prev.id,
            invoice_number="INV-261030-0001",
            subtotal=order_prev.subtotal,
            discount=order_prev.discount_amount,
            tax=order_prev.tax_amount,
            service_charge=order_prev.service_charge,
            total_amount=order_prev.total_amount,
            paid_amount=order_prev.total_amount,
            status="Paid"
        )
        db.add(inv_prev)
        db.flush()

        pay_prev = Payment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            invoice_id=inv_prev.id,
            order_id=order_prev.id,
            amount=inv_prev.total_amount,
            payment_method="Card",
            payment_reference="AUTH_VISA_9832",
            status="Success"
        )
        db.add(pay_prev)

        # Active Live Order in Kitchen for Table T-03
        order_live = Order(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            order_number="ORD-261030-0002",
            order_type="DineIn",
            status="InKitchen",
            table_id=tables[2].id,
            table_number=tables[2].table_number,
            customer_name="Walk-in Guest Table 3",
            subtotal=Decimal("1230.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("61.50"),
            service_charge=Decimal("30.75"),
            total_amount=Decimal("1322.25"),
            cashier_id=user_cashier.id,
            cashier_name=user_cashier.full_name,
            waiter_id=user_waiter.id,
            waiter_name=user_waiter.full_name
        )
        db.add(order_live)
        db.flush()

        oi_live1 = OrderItem(id=str(uuid.uuid4()), order_id=order_live.id, menu_item_id=item_truffle.id, item_name="Tartufo & Funghi Pizza", unit_price=Decimal("695.00"), quantity=1, subtotal=Decimal("695.00"), notes="Extra crispy crust")
        oi_live2 = OrderItem(id=str(uuid.uuid4()), order_id=order_live.id, menu_item_id=item_alfredo.id, item_name="Fettuccine ai Funghi", unit_price=Decimal("545.00"), quantity=1, subtotal=Decimal("545.00"))
        db.add_all([oi_live1, oi_live2])
        db.flush()

        # Active Live KOT for Station Pizza & Pasta
        kot_live = KOT(
            id=str(uuid.uuid4()),
            tenant_id=tenant_1.id,
            branch_id=branch_1a.id,
            order_id=order_live.id,
            kitchen_station_id=station_pizza.id,
            kot_number="KOT-1042",
            status="Preparing",
            waiter_name="Giovanni Kumar",
            started_preparing_at=datetime.utcnow() - timedelta(minutes=8),
            notes="Rush order — Table 3 anniversary"
        )
        db.add(kot_live)
        db.flush()

        db.add(KOTItem(id=str(uuid.uuid4()), kot_id=kot_live.id, order_item_id=oi_live1.id, item_name="Tartufo & Funghi Pizza", quantity=1, notes="Extra crispy crust", status="Preparing"))
        db.add(KOTItem(id=str(uuid.uuid4()), kot_id=kot_live.id, order_item_id=oi_live2.id, item_name="Fettuccine ai Funghi", quantity=1, status="Preparing"))

        # 4. Tenant 2: Spice Symphony Bistro (Full End-to-End Demo Restaurant)
        tenant_2 = Tenant(
            id=_seed_id("tenant:spice-symphony"),
            name="Spice Symphony Bistro",
            slug="spice-symphony",
            business_type="Modern Indian Bistro",
            status="Active",
            contact_email="owner@spicesymphony.com",
            contact_phone="+91 98111 22233",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
            onboarding_completed=True,
            onboarding_step=5,
        )
        db.add(tenant_2)
        db.flush()

        sub_2 = Subscription(
            id=_seed_id("sub:spice-symphony"),
            tenant_id=tenant_2.id,
            plan_id=plan_pro.id,
            status="Active",
            billing_cycle="monthly",
            current_period_start=datetime.utcnow() - timedelta(days=10),
            current_period_end=datetime.utcnow() + timedelta(days=20),
        )
        db.add(sub_2)

        branch_2 = Branch(
            id=_seed_id("branch:spice-symphony:SS-HYD-01"),
            tenant_id=tenant_2.id,
            name="hyderabad",
            code="SS-HYD-01",
            phone="+91 40 2335 8899",
            email="banjarahills@spicesymphony.com",
            address="Road No 12, Banjara Hills",
            city="Hyderabad",
            state="Telangana",
            postal_code="500034",
            tax_rate=Decimal("5.00"),
            service_charge_rate=Decimal("0.00"),
            currency="INR",
            is_active=True,
        )
        branch_2b = Branch(
            id=_seed_id("branch:spice-symphony:SS-HYD-02"),
            tenant_id=tenant_2.id,
            name="Hyderabad - Gachibowli",
            code="SS-HYD-02",
            phone="+91 40 4901 7766",
            email="gachibowli@spicesymphony.com",
            address="Financial District",
            city="Hyderabad",
            state="Telangana",
            postal_code="500032",
            tax_rate=Decimal("5.00"),
            service_charge_rate=Decimal("0.00"),
            currency="INR",
            is_active=True,
        )
        db.add_all([branch_2, branch_2b])
        db.flush()

        user_tenant2 = User(
            id=_seed_id("user:owner@spicesymphony.com"),
            tenant_id=tenant_2.id,
            email="owner@spicesymphony.com",
            password_hash=get_password_hash("Owner@456"),
            full_name="Rajesh Verma",
            role="TENANT_OWNER",
            phone="+91 98111 22233",
            branch_id=branch_2.id,
            is_active=True,
        )
        db.add(user_tenant2)
        db.flush()

        # Full Indian Menu Hierarchy + End-to-End Operational Data
        seed_spice_symphony_menus(db, tenant_2.id, branch_2.id)
        seed_spice_symphony_full_operations(db, tenant_2.id, branch_2.id, branch_2b.id, user_tenant2)

        db.commit()
        print("✅ Database successfully seeded with SaaS multi-tenant enterprise data!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

def _ensure_spice_symphony_kitchen_stations(db: Session, tenant_id: str, branch_id: str):
    """Ensures Kitchen + KOT stations exist for Spice Symphony so kitchen routing works."""
    stations = {
        s.name: s
        for s in db.query(KitchenStation).filter(KitchenStation.tenant_id == tenant_id).all()
    }
    if stations:
        return stations
    kitchen = db.query(Kitchen).filter(Kitchen.tenant_id == tenant_id).first()
    if not kitchen:
        kitchen = Kitchen(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            name="Spice Symphony Central Kitchen",
        )
        db.add(kitchen)
        db.flush()
    for sname in ["Curry & Biryani Station", "Tandoor & Grill", "Tiffin & Beverage Counter"]:
        st = KitchenStation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            kitchen_id=kitchen.id,
            name=sname,
        )
        db.add(st)
        stations[sname] = st
    db.flush()
    return stations


def seed_spice_symphony_menus(db: Session, tenant_id: str, branch_id: str):
    """
    Seeds & upgrades Spice Symphony into the 3-dimensional Restaurant ERP catalog:
    1. Independent Cuisines (10 Indian/global cuisines)
    2. Four Dietary Food Types (VEG, NON_VEG, EGG, VEGAN)
    3. Clean Dish Categories + Subcategories (without mixing Cuisine or Food Type)
    4. Scheduled Menus (Breakfast, Lunch, Dinner, All-Day), Half/Full variants, Combos & Branch overrides.
    """
    stations = _ensure_spice_symphony_kitchen_stations(db, tenant_id, branch_id)
    st_curry = stations.get("Curry & Biryani Station")
    st_tandoor = stations.get("Tandoor & Grill") or st_curry
    st_tiffin = stations.get("Tiffin & Beverage Counter") or st_curry

    apply_indian_menu_template(
        db,
        tenant_id=tenant_id,
        branch_id=branch_id,
        include_sample_dishes=False,
        create_scheduled_menus=True,
    )

    cui_map = {
        c.name: c
        for c in db.query(Cuisine).filter(Cuisine.tenant_id == tenant_id).all()
    }
    cat_map = {
        c.name: c
        for c in db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id).all()
    }
    menu_map = {
        m.name: m
        for m in db.query(Menu).filter(Menu.tenant_id == tenant_id).all()
    }

    # Add custom Subcategories cleanly under Dish Categories
    if "Curries & Gravies" in cat_map and "Andhra & Telangana Curries" not in cat_map:
        sub_andhra = MenuCategory(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            parent_id=cat_map["Curries & Gravies"].id,
            name="Andhra & Telangana Curries",
            display_order=15,
            is_active=True,
        )
        db.add(sub_andhra)
        db.flush()
        cat_map["Andhra & Telangana Curries"] = sub_andhra

    if "Starters" in cat_map and "Tandoori Kebabs" not in cat_map:
        sub_kebab = MenuCategory(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            parent_id=cat_map["Starters"].id,
            name="Tandoori Kebabs",
            display_order=16,
            is_active=True,
        )
        db.add(sub_kebab)
        db.flush()
        cat_map["Tandoori Kebabs"] = sub_kebab

    # Deactivate legacy mixed categories & menus so UI shows clean unmixed dimensions
    legacy_cat_names = {"Curries", "Telugu Dishes", "Veg", "Non-Veg", "Biryani", "South Indian Tiffins"}
    for legacy_name in legacy_cat_names:
        if legacy_name in cat_map:
            cat_map[legacy_name].is_active = False

    legacy_menu_names = {"Veg Curries", "Non-Veg Curries", "Biryanis", "Starters", "Morning Tiffins"}
    for lm_name in legacy_menu_names:
        if lm_name in menu_map:
            menu_map[lm_name].is_active = False

    # Format: (name, desc, price, cuisine_name, food_type, category_name, menu_name, tax_rate, station, spice_levels)
    catalog_specs = [
        # Breakfast / Tiffins
        ("Idli (2 Pcs)", "Steamed soft rice cakes served with sambar & coconut chutney.", "60.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00", st_tiffin, ["Mild"]),
        ("Medu Vada", "Crisp black lentil doughnuts tempered with curry leaves & pepper.", "75.00", "South Indian", "VEGAN", "Tiffins / Breakfast", "Breakfast Menu", "5.00", st_tiffin, ["Mild"]),
        ("Ghee Karam Dosa", "Crisp fermented crepe brushed with spicy Guntur chilli garlic paste & ghee.", "120.00", "Andhra Special", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00", st_tiffin, ["Medium", "Spicy"]),
        ("MLA Pesarattu Upma", "Green moong lentil crepe stuffed with ginger-jeera rava upma & ginger chutney.", "135.00", "Andhra Special", "VEG", "Tiffins / Breakfast", "Breakfast Menu", "5.00", st_tiffin, ["Mild", "Medium"]),
        ("Masala Dosa", "Golden rice crepe filled with tempered spiced potato masala.", "110.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00", st_tiffin, ["Mild", "Medium"]),
        # Starters (Veg / Non-Veg / Egg)
        ("Chicken 65", "Crisp spicy boneless chicken tossed with curry leaves, green chillies & garlic.", "220.00", "South Indian", "NON_VEG", "Starters", "Dinner Menu", "5.00", st_tandoor, ["Medium", "Spicy", "Extra Hot"]),
        ("Gobi 65", "Golden cauliflower florets tossed in South Indian red chilli masala.", "170.00", "South Indian", "VEG", "Starters", "All-Day Menu", "5.00", st_tandoor, ["Medium", "Spicy"]),
        ("Paneer Tikka", "Char-grilled tandoori cottage cheese marinated in hung curd & spices.", "235.00", "Tandoori", "VEG", "Tandoori Kebabs", "Dinner Menu", "5.00", st_tandoor, ["Mild", "Medium"]),
        ("Chicken Tikka", "Smoky boneless chicken morsels roasted in clay tandoor oven.", "265.00", "Tandoori", "NON_VEG", "Tandoori Kebabs", "Dinner Menu", "5.00", st_tandoor, ["Mild", "Medium", "Spicy"]),
        ("Veg Manchurian", "Crispy vegetable balls glazed in spicy Indo-Chinese soy garlic sauce.", "165.00", "Indo-Chinese", "VEGAN", "Starters", "Dinner Menu", "5.00", st_curry, ["Medium", "Spicy"]),
        ("Egg Pakoda", "Crispy besan-battered spiced halved eggs served hot with mint chutney.", "140.00", "Indian Street Food", "EGG", "Starters", "All-Day Menu", "5.00", st_tandoor, ["Medium", "Spicy"]),
        # Curries & Gravies (+ Subcategory Andhra & Telangana Curries)
        ("Gutti Vankaya", "Stuffed baby brinjals simmered in traditional spicy Andhra roasted masala.", "150.00", "Andhra Special", "VEG", "Andhra & Telangana Curries", "Lunch Menu", "5.00", st_curry, ["Medium", "Spicy", "Extra Hot"]),
        ("Pappu Charu", "Comforting Hyderabadi slow-simmered toor dal & tamarind soup tempered with garlic.", "90.00", "Telangana Special", "VEG", "Andhra & Telangana Curries", "Lunch Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Baghara Baingan", "Hyderabadi peanut, sesame & tamarind stuffed eggplant gravy.", "180.00", "Telangana Special", "VEGAN", "Andhra & Telangana Curries", "Lunch Menu", "5.00", st_curry, ["Medium", "Spicy"]),
        ("Paneer Butter Masala", "Cottage cheese cubes simmered in velvety tomato cashew makhani gravy.", "240.00", "North Indian", "VEG", "Curries & Gravies", "All-Day Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Dal Tadka", "Yellow lentils double-tempered with desi ghee, cumin & dried red chillies.", "150.00", "North Indian", "VEG", "Curries & Gravies", "All-Day Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Chole Masala", "Punjabi spiced chickpeas simmered in tangy onion-tomato masala.", "165.00", "North Indian", "VEGAN", "Curries & Gravies", "Lunch Menu", "5.00", st_curry, ["Medium", "Spicy"]),
        ("Butter Chicken", "Char-grilled chicken tikka simmered in rich creamy tomato butter makhani.", "320.00", "North Indian", "NON_VEG", "Curries & Gravies", "Dinner Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Andhra Kodi Kura", "Fiery homestyle Andhra chicken curry finished with fresh curry leaves.", "290.00", "Andhra Special", "NON_VEG", "Andhra & Telangana Curries", "Dinner Menu", "5.00", st_curry, ["Spicy", "Extra Hot"]),
        ("Gongura Mutton", "Tender bone-in goat slow-cooked with tangy red sorrel leaves.", "395.00", "Andhra Special", "NON_VEG", "Andhra & Telangana Curries", "Dinner Menu", "5.00", st_curry, ["Spicy", "Extra Hot"]),
        ("Egg Curry", "Hard-boiled eggs simmered in coastal spiced onion-tomato gravy.", "165.00", "Kerala Special", "EGG", "Curries & Gravies", "All-Day Menu", "5.00", st_curry, ["Medium", "Spicy"]),
        # Breads, Biryani, Meals, Desserts & Beverages
        ("Butter Naan", "Clay-oven leavened flatbread brushed with cultured butter.", "55.00", "Tandoori", "VEG", "Breads & Rotis", "Dinner Menu", "5.00", st_tandoor, ["Mild"]),
        ("Tandoori Roti", "Whole-wheat crisp tandoori flatbread.", "35.00", "Tandoori", "VEGAN", "Breads & Rotis", "Dinner Menu", "5.00", st_tandoor, ["Mild"]),
        ("Hyderabadi Chicken Dum Biryani", "Aged basmati rice sealed over marinated chicken with saffron, birista & mint.", "340.00", "Telangana Special", "NON_VEG", "Rice & Biryani", "All-Day Menu", "5.00", st_curry, ["Medium", "Spicy", "Extra Hot"]),
        ("Veg Biryani", "Fragrant saffron basmati rice cooked dum-style with seasonal vegetables.", "210.00", "Telangana Special", "VEG", "Rice & Biryani", "Lunch Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Andhra Meals", "Full banana-leaf Andhra vegetarian meals with pappu, vankaya, gongura, rasam & curd.", "220.00", "Andhra Special", "VEG", "Meals / Thali", "Lunch Menu", "5.00", st_curry, ["Medium"]),
        ("North Indian Thali", "Paneer butter masala, dal tadka, jeera rice, 2 butter naans, raita & sweet.", "270.00", "North Indian", "VEG", "Meals / Thali", "Lunch Menu", "5.00", st_curry, ["Mild", "Medium"]),
        ("Gulab Jamun (2 Pcs)", "Warm milk-solid dumplings steeped in rose cardamom sugar syrup.", "95.00", "North Indian", "VEG", "Desserts", "All-Day Menu", "5.00", st_tiffin, ["Mild"]),
        ("Madras Filter Coffee", "Traditional brass-decoction South Indian frothy coffee.", "65.00", "South Indian", "VEG", "Beverages", "Breakfast Menu", "5.00", st_tiffin, ["Mild"]),
    ]

    existing_items = {
        it.name: it
        for it in db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id).all()
    }
    created_or_updated = {}
    for idx, (name, desc, price, cui_name, ftype, cat_name, menu_name, tax_r, station, spices) in enumerate(catalog_specs):
        cui_obj = cui_map.get(cui_name)
        cat_obj = cat_map.get(cat_name) or cat_map.get("Main Course")
        menu_obj = menu_map.get(menu_name) or menu_map.get("All-Day Menu")
        is_veg_flag = ftype in ("VEG", "VEGAN")

        if name in existing_items:
            it = existing_items[name]
            it.description = desc
            it.base_price = Decimal(price)
            it.cuisine_id = cui_obj.id if cui_obj else it.cuisine_id
            it.food_type = ftype
            it.is_veg = is_veg_flag
            it.category_id = cat_obj.id if cat_obj else it.category_id
            it.menu_id = menu_obj.id if menu_obj else it.menu_id
            it.tax_rate = Decimal(tax_r)
            it.kitchen_station_id = station.id if station else it.kitchen_station_id
            it.spice_levels = spices
            it.order_channels = ["DineIn", "Takeaway", "Delivery", "QR"]
            if not it.image_url or it.image_url.endswith(".png"):
                it.image_url = resolve_default_indian_dish_image(name, cat_name)
            created_or_updated[name] = it
        else:
            it = MenuItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                menu_id=menu_obj.id if menu_obj else None,
                category_id=cat_obj.id if cat_obj else None,
                cuisine_id=cui_obj.id if cui_obj else None,
                food_type=ftype,
                name=name,
                description=desc,
                image_url=resolve_default_indian_dish_image(name, cat_name),
                base_price=Decimal(price),
                cost_price=Decimal(price) * Decimal("0.35"),
                tax_rate=Decimal(tax_r),
                preparation_time=15,
                display_order=idx + 1,
                is_available=True,
                show_on_customer_site=True,
                is_veg=is_veg_flag,
                kitchen_station_id=station.id if station else None,
                order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
                spice_levels=spices,
            )
            db.add(it)
            db.flush()
            created_or_updated[name] = it

    # Map any remaining legacy items on tenant that weren't in catalog_specs
    fallback_cui = cui_map.get("Andhra Special") or next(iter(cui_map.values()), None)
    fallback_cat = cat_map.get("Curries & Gravies") or next(iter(cat_map.values()), None)
    for it in db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id).all():
        if not it.cuisine_id and fallback_cui:
            it.cuisine_id = fallback_cui.id
        if not it.food_type:
            it.food_type = "VEG" if it.is_veg else "NON_VEG"
        if not it.image_url:
            it.image_url = resolve_default_indian_dish_image(it.name, it.category.name if it.category else "")
        if it.category_id and any(it.category_id == cat_map[ln].id for ln in legacy_cat_names if ln in cat_map):
            if fallback_cat:
                it.category_id = fallback_cat.id
        if it.menu_id and any(it.menu_id == menu_map[lm].id for lm in legacy_menu_names if lm in menu_map):
            if "All-Day Menu" in menu_map:
                it.menu_id = menu_map["All-Day Menu"].id

    # Ensure all seeded Indian menus/categories/items work across every branch of the tenant
    for m in db.query(Menu).filter(Menu.tenant_id == tenant_id).all():
        m.branch_id = None
    for cat in db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id).all():
        cat.branch_id = None
    for it in db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id).all():
        it.branch_id = None

    # Variants (Half / Full) on Biryani & Paneer Butter Masala if none exist
    biryani_item = created_or_updated.get("Hyderabadi Chicken Dum Biryani")
    if biryani_item and db.query(ItemVariant).filter(ItemVariant.item_id == biryani_item.id).count() == 0:
        db.add_all([
            ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=biryani_item.id, name="Half", price=Decimal("195.00"), is_available=True),
            ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=biryani_item.id, name="Full", price=Decimal("340.00"), is_available=True),
            ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=biryani_item.id, name="Family Pack", price=Decimal("640.00"), is_available=True),
        ])

    pbm_item = created_or_updated.get("Paneer Butter Masala")
    if pbm_item and db.query(ItemVariant).filter(ItemVariant.item_id == pbm_item.id).count() == 0:
        db.add_all([
            ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=pbm_item.id, name="Half", price=Decimal("145.00"), is_available=True),
            ItemVariant(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=pbm_item.id, name="Full", price=Decimal("240.00"), is_available=True),
        ])

    # Combo Meal: Hyderabad Biryani Combo
    combo_name = "Hyderabad Biryani Combo"
    if combo_name not in existing_items and biryani_item and "Chicken 65" in created_or_updated:
        combo_cat = cat_map.get("Combos / Special Meals") or fallback_cat
        combo_menu = menu_map.get("All-Day Menu")
        combo_item = MenuItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            menu_id=combo_menu.id if combo_menu else None,
            category_id=combo_cat.id if combo_cat else None,
            cuisine_id=cui_map["Telangana Special"].id if "Telangana Special" in cui_map else None,
            food_type="NON_VEG",
            name=combo_name,
            description="1x Hyderabadi Chicken Dum Biryani + 1x Chicken 65 (Half) + 1x Gulab Jamun.",
            image_url="/images/dishes/chicken-biryani.jpg",
            base_price=Decimal("499.00"),
            cost_price=Decimal("180.00"),
            tax_rate=Decimal("5.00"),
            preparation_time=25,
            display_order=1,
            is_available=True,
            show_on_customer_site=True,
            is_veg=False,
            is_combo=True,
            kitchen_station_id=st_curry.id if st_curry else None,
            order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
            spice_levels=["Medium", "Spicy"],
        )
        db.add(combo_item)
        db.flush()
        db.add_all([
            ComboMealItem(id=str(uuid.uuid4()), tenant_id=tenant_id, combo_item_id=combo_item.id, component_item_id=biryani_item.id, quantity=1),
            ComboMealItem(id=str(uuid.uuid4()), tenant_id=tenant_id, combo_item_id=combo_item.id, component_item_id=created_or_updated["Chicken 65"].id, quantity=1),
        ])

    # Multi-branch pricing override demo on Gachibowli branch if present
    gachibowli = db.query(Branch).filter(Branch.tenant_id == tenant_id, Branch.code == "SS-HYD-02").first()
    if gachibowli and biryani_item:
        existing_cfg = db.query(MenuItemBranchConfig).filter(
            MenuItemBranchConfig.tenant_id == tenant_id,
            MenuItemBranchConfig.menu_item_id == biryani_item.id,
            MenuItemBranchConfig.branch_id == gachibowli.id,
        ).first()
        if not existing_cfg:
            db.add(MenuItemBranchConfig(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                menu_item_id=biryani_item.id,
                branch_id=gachibowli.id,
                branch_price=Decimal("365.00"),
                is_available=True,
                show_on_customer_site=True,
            ))

    # Modifier groups on Gutti Vankaya & Biryani if missing
    gv_item = created_or_updated.get("Gutti Vankaya")
    if gv_item and db.query(ItemModifierGroup).filter(ItemModifierGroup.item_id == gv_item.id).count() == 0:
        mg_spice = ItemModifierGroup(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=gv_item.id, name="Spice Level", min_selection=1, max_selection=1)
        mg_addons = ItemModifierGroup(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=gv_item.id, name="Extra Toppings & Sides", min_selection=0, max_selection=3)
        db.add_all([mg_spice, mg_addons])
        db.flush()
        db.add_all([
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_spice.id, name="Mild Spice", price=Decimal("0.00"), is_available=True),
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_spice.id, name="Medium Andhra", price=Decimal("0.00"), is_available=True),
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_spice.id, name="Extra Guntur Spicy", price=Decimal("15.00"), is_available=True),
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_addons.id, name="Pure Cow Ghee Drizzle", price=Decimal("25.00"), is_available=True),
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_addons.id, name="Roasted Cashew Garnish", price=Decimal("40.00"), is_available=True),
        ])

    if biryani_item and db.query(ItemModifierGroup).filter(ItemModifierGroup.item_id == biryani_item.id).count() == 0:
        mg_biryani = ItemModifierGroup(id=str(uuid.uuid4()), tenant_id=tenant_id, item_id=biryani_item.id, name="Biryani Accompaniments", min_selection=0, max_selection=3)
        db.add(mg_biryani)
        db.flush()
        db.add_all([
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_biryani.id, name="Extra Mirchi Ka Salan", price=Decimal("30.00"), is_available=True),
            ItemModifier(id=str(uuid.uuid4()), tenant_id=tenant_id, group_id=mg_biryani.id, name="Extra Double Boiled Egg", price=Decimal("35.00"), is_available=True),
        ])


NON_INDIAN_CUISINES = {"Italian", "Continental", "Chinese", "Other Regional"}
LEGACY_OR_NON_INDIAN_CATEGORIES = {
    "Antipasti & Starters",
    "Woodfired Pizzas",
    "Artisanal Pasta",
    "Dolci & Desserts",
    "Beverages & Wine",
    "Curries",
    "Telugu Dishes",
    "Veg",
    "Non-Veg",
    "Biryani",
    "South Indian Tiffins",
}
LEGACY_OR_NON_INDIAN_MENUS = {
    "Antipasti & Starters",
    "Woodfired Pizzas",
    "Artisanal Pasta",
    "Dolci & Desserts",
    "Beverages & Wine",
    "Veg Curries",
    "Non-Veg Curries",
    "Biryanis",
    "Starters",
    "Morning Tiffins",
}
NON_INDIAN_ITEMS = {
    "Margherita D.O.P.",
    "Tartufo & Funghi Pizza",
    "Fettuccine ai Funghi",
    "Bruschetta Pomodoro",
    "Classic Tiramisù",
    "San Pellegrino Sparkling 750ml",
}


def _purge_non_indian_and_legacy_records(db: Session, tenant_id: str):
    """Removes non-Indian cuisines/categories/menus/dishes and obsolete mixed records."""
    # Unassign tables referencing non-Indian/legacy menus
    legacy_menus = (
        db.query(Menu)
        .filter(Menu.tenant_id == tenant_id, Menu.name.in_(LEGACY_OR_NON_INDIAN_MENUS))
        .all()
    )
    legacy_menu_ids = [m.id for m in legacy_menus]
    if legacy_menu_ids:
        db.query(RestaurantTable).filter(
            RestaurantTable.tenant_id == tenant_id,
            RestaurantTable.assigned_menu_id.in_(legacy_menu_ids),
        ).update({"assigned_menu_id": None}, synchronize_session=False)

    # Delete non-Indian menu items cleanly (cascade deletes variants/modifiers/branch_configs/recipes)
    for it in (
        db.query(MenuItem)
        .filter(MenuItem.tenant_id == tenant_id, MenuItem.name.in_(NON_INDIAN_ITEMS))
        .all()
    ):
        db.query(ComboMealItem).filter(
            ComboMealItem.tenant_id == tenant_id,
            (ComboMealItem.combo_item_id == it.id) | (ComboMealItem.component_item_id == it.id),
        ).delete(synchronize_session=False)
        db.delete(it)
    db.flush()

    # After seeding clean Indian categories, any old empty legacy/non-Indian categories can be removed safely
    for cat in (
        db.query(MenuCategory)
        .filter(MenuCategory.tenant_id == tenant_id, MenuCategory.name.in_(LEGACY_OR_NON_INDIAN_CATEGORIES))
        .all()
    ):
        if len(cat.items or []) == 0:
            db.delete(cat)

    for m in legacy_menus:
        db.delete(m)

    for cu in (
        db.query(Cuisine)
        .filter(Cuisine.tenant_id == tenant_id, Cuisine.name.in_(NON_INDIAN_CUISINES))
        .all()
    ):
        db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id, MenuItem.cuisine_id == cu.id).update(
            {"cuisine_id": None}, synchronize_session=False
        )
        db.delete(cu)
    db.flush()


def _ss_find_dish(menu_items: list, *keywords: str) -> MenuItem:
    """Finds the best matching seeded MenuItem by partial name match, falling back cleanly."""
    for kw in keywords:
        kw_low = kw.lower()
        for item in menu_items:
            if kw_low in item.name.lower():
                return item
    return menu_items[0]


def _ensure_ss_staff(
    db: Session,
    tenant_id: str,
    branch_1_id: str,
    branch_2_id: Optional[str],
    owner_user: Optional[User],
) -> tuple[User, User, User]:
    """Ensures Spice Symphony staff accounts and multi-branch memberships exist."""
    staff_specs = [
        ("manager@spicesymphony.com", "Manager@456", "Anitha Reddy", "BRANCH_MANAGER", "+91 98111 22234", branch_1_id),
        ("cashier@spicesymphony.com", "Cashier@456", "Karthik Nair", "CASHIER", "+91 98111 22235", branch_1_id),
        ("waiter@spicesymphony.com", "Waiter@456", "Suresh Goud", "WAITER", "+91 98111 22236", branch_1_id),
        ("chef@spicesymphony.com", "Chef@456", "Chef Ramesh Babu", "KITCHEN_MANAGER", "+91 98111 22237", branch_1_id),
    ]
    if branch_2_id:
        staff_specs.append(
            ("gachibowli.cashier@spicesymphony.com", "Cashier@456", "Deepika Rao", "CASHIER", "+91 98111 22238", branch_2_id)
        )

    staff_by_email: dict[str, User] = {}
    for email, raw_pw, full_name, role, phone, assigned_branch_id in staff_specs:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            staff_by_email[email] = existing
            continue
        user_obj = User(
            id=_seed_id(f"ss-op:{tenant_id}:user:{email}"),
            tenant_id=tenant_id,
            email=email,
            password_hash=get_password_hash(raw_pw),
            full_name=full_name,
            role=role,
            phone=phone,
            branch_id=assigned_branch_id,
            is_active=True,
        )
        db.add(user_obj)
        staff_by_email[email] = user_obj
    db.flush()

    all_branches = [b for b in [branch_1_id, branch_2_id] if b]
    multi_branch_users = [u for u in [owner_user, staff_by_email.get("manager@spicesymphony.com")] if u]
    for u in multi_branch_users:
        for b_id in all_branches:
            has_membership = db.query(BranchMembership).filter(
                BranchMembership.user_id == u.id,
                BranchMembership.branch_id == b_id,
            ).first()
            if not has_membership:
                db.add(
                    BranchMembership(
                        id=_seed_id(f"ss-op:{tenant_id}:member:{u.id}:{b_id}"),
                        tenant_id=tenant_id,
                        user_id=u.id,
                        branch_id=b_id,
                        role=u.role,
                    )
                )
    db.flush()

    cashier_b1 = staff_by_email.get("cashier@spicesymphony.com") or owner_user
    waiter_b1 = staff_by_email.get("waiter@spicesymphony.com") or owner_user
    cashier_b2 = staff_by_email.get("gachibowli.cashier@spicesymphony.com") or cashier_b1
    return cashier_b1, waiter_b1, cashier_b2


def _ensure_ss_tables_and_reservations(
    db: Session,
    tenant_id: str,
    branch_1_id: str,
    branch_2_id: Optional[str],
    default_menu_id: Optional[str],
) -> tuple[dict[str, RestaurantTable], dict[str, RestaurantTable]]:
    """Ensures dining areas, floor tables across both branches, and reservations exist."""
    now = datetime.utcnow()

    def _get_or_create_area(b_id: str, name: str, display_order: int) -> DiningArea:
        area = db.query(DiningArea).filter(
            DiningArea.tenant_id == tenant_id,
            DiningArea.branch_id == b_id,
            DiningArea.name == name,
        ).first()
        if area:
            return area
        area = DiningArea(
            id=_seed_id(f"ss-op:{tenant_id}:area:{b_id}:{name}"),
            tenant_id=tenant_id,
            branch_id=b_id,
            name=name,
            display_order=display_order,
        )
        db.add(area)
        db.flush()
        return area

    area_main = _get_or_create_area(branch_1_id, "Main Dining Hall", 1)
    area_court = _get_or_create_area(branch_1_id, "Deccan Courtyard", 2)
    area_vip = _get_or_create_area(branch_1_id, "Nizam Private Lounge", 3)

    b1_specs = [
        ("T-01", "Andhra Courtyard 1", 4, area_main.id, "Available", 40, 40, "QR-SPICE-T01", None),
        ("T-02", "Nizam Booth 2", 6, area_main.id, "Occupied", 200, 40, "QR-SPICE-T02", now - timedelta(minutes=28)),
        ("T-03", "Banjara Corner 3", 4, area_main.id, "Occupied", 360, 40, "QR-SS-HYD-T03", now - timedelta(minutes=14)),
        ("T-04", "Charminar Family 4", 6, area_court.id, "Reserved", 40, 170, "QR-SS-HYD-T04", None),
        ("T-05", "Golconda Terrace 5", 2, area_court.id, "Cleaning", 200, 170, "QR-SS-HYD-T05", None),
        ("T-06", "Royal Diwan 6", 8, area_vip.id, "Available", 360, 170, "QR-SS-HYD-T06", None),
    ]

    b1_tables: dict[str, RestaurantTable] = {}
    for tbl_no, name, cap, area_id, status_val, px, py, qr_tok, occ_since in b1_specs:
        tbl = db.query(RestaurantTable).filter(
            RestaurantTable.tenant_id == tenant_id,
            RestaurantTable.branch_id == branch_1_id,
            RestaurantTable.table_number == tbl_no,
        ).first()
        if tbl:
            tbl.pos_x = px
            tbl.pos_y = py
            if not tbl.assigned_menu_id and default_menu_id:
                tbl.assigned_menu_id = default_menu_id
            b1_tables[tbl_no] = tbl
            continue
        safe_qr = qr_tok if not db.query(RestaurantTable).filter(RestaurantTable.qr_code_token == qr_tok).first() else f"QR-{tenant_id[:6]}-{branch_1_id[:4]}-{tbl_no}"
        tbl = RestaurantTable(
            id=_seed_id(f"ss-op:{tenant_id}:table:{branch_1_id}:{tbl_no}"),
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            area_id=area_id,
            assigned_menu_id=default_menu_id,
            table_number=tbl_no,
            name=name,
            capacity=cap,
            status=status_val,
            pos_x=px,
            pos_y=py,
            qr_code_token=safe_qr,
            occupied_since=occ_since,
        )
        db.add(tbl)
        b1_tables[tbl_no] = tbl
    db.flush()

    if db.query(Reservation).filter(Reservation.tenant_id == tenant_id, Reservation.branch_id == branch_1_id).count() == 0:
        db.add_all([
            Reservation(
                id=_seed_id(f"ss-op:{tenant_id}:res:1"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                table_id=b1_tables["T-04"].id,
                customer_name="Srinivasulu Raju",
                customer_phone="+91 98480 44551",
                customer_email="srinivas.raju@gmail.com",
                party_size=6,
                reservation_time=now + timedelta(hours=2),
                status="Confirmed",
                special_requests="Birthday dinner — keep T-04 decorated with candles",
            ),
            Reservation(
                id=_seed_id(f"ss-op:{tenant_id}:res:2"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                table_id=b1_tables["T-02"].id,
                customer_name="Priya Deshmukh",
                customer_phone="+91 98492 77112",
                customer_email="priya.deshmukh@outlook.com",
                party_size=4,
                reservation_time=now - timedelta(minutes=30),
                status="CheckedIn",
                special_requests="Medium spice Hyderabadi dum biryani requested",
            ),
            Reservation(
                id=_seed_id(f"ss-op:{tenant_id}:res:3"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                table_id=b1_tables["T-06"].id,
                customer_name="Arjun Malhotra",
                customer_phone="+91 90005 33221",
                customer_email="arjun.m@techcorp.in",
                party_size=8,
                reservation_time=now + timedelta(days=1, hours=4),
                status="Confirmed",
                special_requests="Corporate lunch — arrange Royal Diwan table",
            ),
            Reservation(
                id=_seed_id(f"ss-op:{tenant_id}:res:4"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                table_id=None,
                customer_name="Kavitha Menon",
                customer_phone="+91 99851 66440",
                customer_email="kavitha.menon@gmail.com",
                party_size=2,
                reservation_time=now + timedelta(hours=5),
                status="Pending",
                special_requests="Quiet courtyard seating preferred",
            ),
        ])

    b2_tables: dict[str, RestaurantTable] = {}
    if branch_2_id:
        area_gcb = _get_or_create_area(branch_2_id, "Gachibowli Bistro Hall", 1)
        b2_specs = [
            ("T-01", "Cyber Lounge 1", 4, "Available", 60, 60, "QR-SS-GCB-T01", None),
            ("T-02", "Financial Booth 2", 6, "Occupied", 240, 60, "QR-SS-GCB-T02", now - timedelta(minutes=18)),
        ]
        for tbl_no, name, cap, status_val, px, py, qr_tok, occ_since in b2_specs:
            tbl = db.query(RestaurantTable).filter(
                RestaurantTable.tenant_id == tenant_id,
                RestaurantTable.branch_id == branch_2_id,
                RestaurantTable.table_number == tbl_no,
            ).first()
            if not tbl:
                safe_qr = qr_tok if not db.query(RestaurantTable).filter(RestaurantTable.qr_code_token == qr_tok).first() else f"QR-{tenant_id[:6]}-GCB-{tbl_no}"
                tbl = RestaurantTable(
                    id=_seed_id(f"ss-op:{tenant_id}:table:{branch_2_id}:{tbl_no}"),
                    tenant_id=tenant_id,
                    branch_id=branch_2_id,
                    area_id=area_gcb.id,
                    assigned_menu_id=default_menu_id,
                    table_number=tbl_no,
                    name=name,
                    capacity=cap,
                    status=status_val,
                    pos_x=px,
                    pos_y=py,
                    qr_code_token=safe_qr,
                    occupied_since=occ_since,
                )
                db.add(tbl)
            b2_tables[tbl_no] = tbl
        db.flush()

        if db.query(Reservation).filter(Reservation.tenant_id == tenant_id, Reservation.branch_id == branch_2_id).count() == 0:
            db.add(
                Reservation(
                    id=_seed_id(f"ss-op:{tenant_id}:res:gcb-1"),
                    tenant_id=tenant_id,
                    branch_id=branch_2_id,
                    table_id=b2_tables["T-01"].id,
                    customer_name="Vikramaditya Rao",
                    customer_phone="+91 98490 88211",
                    customer_email="vikram.rao@finhub.in",
                    party_size=4,
                    reservation_time=now + timedelta(hours=3),
                    status="Confirmed",
                    special_requests="Team dinner near charging outlet",
                )
            )
    db.flush()
    return b1_tables, b2_tables


def _ensure_ss_inventory_and_recipes(
    db: Session,
    tenant_id: str,
    branch_1_id: str,
    menu_items: list[MenuItem],
    owner_name: str,
) -> dict[str, InventoryItem]:
    """Seeds realistic Indian kitchen inventory (including 2 low-stock triggers) and recipe BOMs."""
    cat_names = [
        "Grains & Pulses",
        "Meat & Poultry",
        "Dairy & Ghee",
        "Spices & Masalas",
        "Fresh Produce & Beverage",
    ]
    cats: dict[str, InventoryCategory] = {}
    for cname in cat_names:
        cat = db.query(InventoryCategory).filter(
            InventoryCategory.tenant_id == tenant_id,
            InventoryCategory.name == cname,
        ).first()
        if not cat:
            cat = InventoryCategory(
                id=_seed_id(f"ss-op:{tenant_id}:invcat:{cname}"),
                tenant_id=tenant_id,
                name=cname,
            )
            db.add(cat)
        cats[cname] = cat
    db.flush()

    inv_specs = [
        ("SS-INV-BASM", "Royal Aged Basmati Rice", "Grains & Pulses", "kg", Decimal("95.000"), Decimal("25.000"), Decimal("125.00"), "Dry Store Rack A1"),
        ("SS-INV-CHKN", "Fresh Curry Cut Chicken", "Meat & Poultry", "kg", Decimal("42.000"), Decimal("15.000"), Decimal("235.00"), "Cold Room Zone A"),
        ("SS-INV-PANEER", "Fresh Malai Paneer Block", "Dairy & Ghee", "kg", Decimal("18.500"), Decimal("8.000"), Decimal("360.00"), "Dairy Chiller B1"),
        ("SS-INV-GHEE", "Pure Cow Ghee", "Dairy & Ghee", "l", Decimal("3.500"), Decimal("5.000"), Decimal("640.00"), "Dry Pantry B2"),
        ("SS-INV-SAFF", "Kashmiri Mongra Saffron", "Spices & Masalas", "kg", Decimal("0.080"), Decimal("0.150"), Decimal("18500.00"), "Spice Vault C1"),
        ("SS-INV-URAD", "Split Black Urad Dal & Batter", "Grains & Pulses", "kg", Decimal("34.000"), Decimal("10.000"), Decimal("92.00"), "Tiffin Cold Prep"),
        ("SS-INV-TMT", "Farm Fresh Tomatoes", "Fresh Produce & Beverage", "kg", Decimal("28.000"), Decimal("10.000"), Decimal("44.00"), "Produce Walk-In"),
        ("SS-INV-ONION", "Red Onions (Birista Cut)", "Fresh Produce & Beverage", "kg", Decimal("36.000"), Decimal("12.000"), Decimal("38.00"), "Produce Walk-In"),
        ("SS-INV-MASALA", "Hyderabadi Shahi Garam Masala", "Spices & Masalas", "kg", Decimal("6.500"), Decimal("2.000"), Decimal("580.00"), "Spice Rack C2"),
        ("SS-INV-COFFEE", "Chikmagalur Filter Coffee Powder", "Fresh Produce & Beverage", "kg", Decimal("9.200"), Decimal("3.000"), Decimal("490.00"), "Beverage Counter"),
        ("SS-INV-ATTA", "Chakki Whole Wheat Atta", "Grains & Pulses", "kg", Decimal("55.000"), Decimal("15.000"), Decimal("52.00"), "Dry Store Rack A2"),
    ]

    inv_by_sku: dict[str, InventoryItem] = {}
    for sku, name, cat_name, uom, stock, min_stock, cost, loc in inv_specs:
        inv = db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.sku == sku,
        ).first()
        if not inv:
            inv = InventoryItem(
                id=_seed_id(f"ss-op:{tenant_id}:inv:{sku}"),
                tenant_id=tenant_id,
                category_id=cats[cat_name].id,
                name=name,
                sku=sku,
                uom=uom,
                current_stock=stock,
                minimum_stock=min_stock,
                cost_per_unit=cost,
                storage_location=loc,
            )
            db.add(inv)
            db.flush()
            db.add(
                StockMovement(
                    id=_seed_id(f"ss-op:{tenant_id}:invmov-init:{sku}"),
                    tenant_id=tenant_id,
                    branch_id=branch_1_id,
                    inventory_item_id=inv.id,
                    movement_type="PURCHASE_RECEIPT",
                    quantity=stock,
                    unit_cost=cost,
                    reference_id="OPENING-SS-2026",
                    notes=f"Initial stock receipt: {name}",
                    created_by=owner_name,
                )
            )
        inv_by_sku[sku] = inv
    db.flush()

    recipe_templates: list[tuple[MenuItem, str, list[tuple[str, Decimal]]]] = [
        (
            _ss_find_dish(menu_items, "Hyderabadi Chicken Dum Biryani", "Chicken Biryani", "Biryani"),
            "Marinate chicken with curd, birista & garam masala; layer with aged basmati, saffron milk & cow ghee on slow dum.",
            [
                ("SS-INV-BASM", Decimal("0.180")),
                ("SS-INV-CHKN", Decimal("0.240")),
                ("SS-INV-ONION", Decimal("0.080")),
                ("SS-INV-GHEE", Decimal("0.025")),
                ("SS-INV-MASALA", Decimal("0.015")),
                ("SS-INV-SAFF", Decimal("0.001")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Chicken 65"),
            "Crisp-fry boneless chicken cubes marinated in ginger-garlic, red chilli paste & temper with curry leaves.",
            [
                ("SS-INV-CHKN", Decimal("0.220")),
                ("SS-INV-ONION", Decimal("0.040")),
                ("SS-INV-MASALA", Decimal("0.015")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Paneer Butter Masala", "Paneer"),
            "Simmer fresh tomatoes & cashews into makhani gravy finished with cow ghee and soft malai paneer cubes.",
            [
                ("SS-INV-PANEER", Decimal("0.180")),
                ("SS-INV-TMT", Decimal("0.160")),
                ("SS-INV-ONION", Decimal("0.070")),
                ("SS-INV-GHEE", Decimal("0.030")),
                ("SS-INV-MASALA", Decimal("0.012")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Masala Dosa", "Dosa"),
            "Crisp fermented dosa roast smeared with cow ghee and filled with tempered potato-onion palya.",
            [
                ("SS-INV-URAD", Decimal("0.220")),
                ("SS-INV-ONION", Decimal("0.050")),
                ("SS-INV-GHEE", Decimal("0.020")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Idli Sambar", "Idli", "Vada"),
            "Steam fluffy fermented rice-urad cakes and serve hot with aromatic drumstick sambar.",
            [
                ("SS-INV-URAD", Decimal("0.200")),
                ("SS-INV-TMT", Decimal("0.060")),
                ("SS-INV-ONION", Decimal("0.040")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Butter Naan", "Roti", "Paratha"),
            "Hand-stretched tandoor dough baked crisp and brushed generously with melted cow ghee.",
            [
                ("SS-INV-ATTA", Decimal("0.140")),
                ("SS-INV-GHEE", Decimal("0.018")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Madras Filter Coffee", "Filter Coffee", "Chai"),
            "Brew slow-dripped Chikmagalur decoction and froth with rich boiled milk in brass davara.",
            [
                ("SS-INV-COFFEE", Decimal("0.022")),
            ],
        ),
        (
            _ss_find_dish(menu_items, "Andhra Meals", "Meals", "Thali"),
            "Traditional full banana-leaf thali with steamed rice, dal pappu, vegetable fry, sambar, curd & sweet.",
            [
                ("SS-INV-BASM", Decimal("0.200")),
                ("SS-INV-TMT", Decimal("0.090")),
                ("SS-INV-ONION", Decimal("0.060")),
                ("SS-INV-GHEE", Decimal("0.020")),
                ("SS-INV-MASALA", Decimal("0.010")),
            ],
        ),
    ]

    # Ensure first menu item(s) displayed on Recipes page always have a BOM linked
    seen_recipe_menu_ids = {mi.id for mi, _, _ in recipe_templates}
    for first_item in sorted(menu_items, key=lambda x: (x.display_order, x.name.lower()))[:3]:
        if first_item.id not in seen_recipe_menu_ids:
            recipe_templates.append(
                (
                    first_item,
                    f"Standard house preparation BOM for {first_item.name}.",
                    [
                        ("SS-INV-ONION", Decimal("0.050")),
                        ("SS-INV-TMT", Decimal("0.060")),
                        ("SS-INV-GHEE", Decimal("0.015")),
                        ("SS-INV-MASALA", Decimal("0.010")),
                    ],
                )
            )
            seen_recipe_menu_ids.add(first_item.id)

    for dish, instructions, ingredients in recipe_templates:
        if db.query(Recipe).filter(Recipe.menu_item_id == dish.id).first():
            continue
        recipe = Recipe(
            id=_seed_id(f"ss-op:{tenant_id}:recipe:{dish.id}"),
            tenant_id=tenant_id,
            menu_item_id=dish.id,
            yield_portions=1,
            preparation_loss_percent=Decimal("3.00"),
            instructions=instructions,
        )
        db.add(recipe)
        db.flush()
        bom_cost = Decimal("0.00")
        for sku, qty in ingredients:
            inv_item = inv_by_sku[sku]
            db.add(
                RecipeItem(
                    id=_seed_id(f"ss-op:{tenant_id}:recitem:{dish.id}:{sku}"),
                    recipe_id=recipe.id,
                    inventory_item_id=inv_item.id,
                    quantity=qty,
                    uom=inv_item.uom,
                )
            )
            bom_cost += qty * Decimal(str(inv_item.cost_per_unit))
        if bom_cost > Decimal("0.00"):
            dish.cost_price = round(bom_cost, 2)

    db.flush()
    return inv_by_sku


def _ensure_ss_procurement(
    db: Session,
    tenant_id: str,
    branch_1_id: str,
    inv_by_sku: dict[str, InventoryItem],
    receiver_name: str,
) -> None:
    """Seeds Indian suppliers, Purchase Orders (Received & Approved), and Goods Receipt Note."""
    now = datetime.utcnow()
    sup_specs = [
        (
            "Deccan Spice & Grain Co.",
            "Venkatesh Naidu",
            "orders@deccanspice.in",
            "+91 40 2781 4400",
            "Begum Bazar Spice Market, Hyderabad",
            "36AAACD4421H1Z4",
            "Net 15 Days",
        ),
        (
            "Telangana Fresh Farm Dairy",
            "Lakshmi Narayana",
            "supply@telanganadairy.in",
            "+91 40 2401 8820",
            "Shamirpet Dairy Cluster, Medchal",
            "36BBBCT9912K1Z8",
            "Net 7 Days",
        ),
        (
            "Coastal Poultry & Meat House",
            "Syed Kareem",
            "dispatch@coastalpoultry.in",
            "+91 98481 55090",
            "Gachibowli Cold Chain Hub, Hyderabad",
            "36CCCCP3189L1Z2",
            "Cash on Delivery",
        ),
    ]
    suppliers: dict[str, Supplier] = {}
    for name, contact, email, phone, addr, gst, terms in sup_specs:
        sup = db.query(Supplier).filter(Supplier.tenant_id == tenant_id, Supplier.name == name).first()
        if not sup:
            sup = Supplier(
                id=_seed_id(f"ss-op:{tenant_id}:sup:{name}"),
                tenant_id=tenant_id,
                name=name,
                contact_name=contact,
                email=email,
                phone=phone,
                address=addr,
                tax_number=gst,
                payment_terms=terms,
            )
            db.add(sup)
        suppliers[name] = sup
    db.flush()

    if db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.branch_id == branch_1_id).count() > 0:
        return

    po1 = PurchaseOrder(
        id=_seed_id(f"ss-op:{tenant_id}:po:1"),
        tenant_id=tenant_id,
        branch_id=branch_1_id,
        supplier_id=suppliers["Deccan Spice & Grain Co."].id,
        po_number="PO-SS-2026-001",
        status="Received",
        total_amount=Decimal("11230.00"),
        expected_delivery_date=now - timedelta(days=3),
        notes="Monthly dry grains & aromatic whole spices replenishment",
        created_at=now - timedelta(days=4),
    )
    po2 = PurchaseOrder(
        id=_seed_id(f"ss-op:{tenant_id}:po:2"),
        tenant_id=tenant_id,
        branch_id=branch_1_id,
        supplier_id=suppliers["Telangana Fresh Farm Dairy"].id,
        po_number="PO-SS-2026-002",
        status="Approved",
        total_amount=Decimal("16800.00"),
        expected_delivery_date=now + timedelta(days=1),
        notes="Urgent replenishment for Cow Ghee (low stock) and Malai Paneer",
        created_at=now - timedelta(hours=5),
    )
    db.add_all([po1, po2])
    db.flush()

    po_items = [
        (po1.id, inv_by_sku["SS-INV-BASM"], Decimal("50.000"), Decimal("125.00")),
        (po1.id, inv_by_sku["SS-INV-MASALA"], Decimal("5.000"), Decimal("580.00")),
        (po1.id, inv_by_sku["SS-INV-ATTA"], Decimal("40.000"), Decimal("52.00")),
        (po2.id, inv_by_sku["SS-INV-GHEE"], Decimal("15.000"), Decimal("640.00")),
        (po2.id, inv_by_sku["SS-INV-PANEER"], Decimal("20.000"), Decimal("360.00")),
    ]
    for idx, (po_id, inv_item, qty, unit_price) in enumerate(po_items, start=1):
        db.add(
            PurchaseOrderItem(
                id=_seed_id(f"ss-op:{tenant_id}:poitem:{idx}"),
                po_id=po_id,
                inventory_item_id=inv_item.id,
                item_name=inv_item.name,
                quantity=qty,
                unit_price=unit_price,
                total_price=round(qty * unit_price, 2),
            )
        )

    db.add(
        GoodsReceipt(
            id=_seed_id(f"ss-op:{tenant_id}:grn:1"),
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            po_id=po1.id,
            grn_number="GRN-SS-2026-001",
            received_date=now - timedelta(days=3),
            received_by=receiver_name,
            notes="Verified seal & quality grade; stored in Dry Store Rack A1",
        )
    )
    db.flush()


def _ensure_ss_crm(db: Session, tenant_id: str) -> dict[str, tuple[Customer, LoyaltyAccount]]:
    """Seeds Hyderabad CRM customers, delivery addresses, and loyalty accounts."""
    now = datetime.utcnow()
    specs = [
        (
            "Rohan Kulkarni",
            "+91 98480 12345",
            "rohan.kulkarni@gmail.com",
            "VIP",
            Decimal("6420.00"),
            6,
            "Loves extra mirchi ka salan with Hyderabadi Dum Biryani.",
            ("Home", "Flat 402, My Home Bhooja, Hitec City", "Near Ikea", "Hyderabad", "500081"),
            "Platinum",
            642,
        ),
        (
            "Meenakshi Iyer",
            "+91 98491 54321",
            "meenakshi.iyer@yahoo.in",
            "VIP",
            Decimal("5280.00"),
            5,
            "Regular morning tiffins & filter coffee patron.",
            ("Office", "Tower B, DLF Cyber City, Gachibowli", "Opp IIIT Gate", "Hyderabad", "500032"),
            "Gold",
            528,
        ),
        (
            "Siddharth Reddy",
            "+91 90001 77889",
            "siddharth.reddy@gmail.com",
            "Returning",
            Decimal("2890.00"),
            3,
            "Prefers coastal Andhra spicy specials.",
            ("Home", "Villa 18, Jubilee Hills Road No 45", "Near Peddamma Temple", "Hyderabad", "500033"),
            "Gold",
            289,
        ),
        (
            "Farhan Ali",
            "+91 99890 66554",
            "farhan.ali@deccan.io",
            "Returning",
            Decimal("1950.00"),
            2,
            "Weekend family dine-in guest.",
            ("Home", "H.No 8-2-293, Banjara Hills Road 12", "Near KBR Park", "Hyderabad", "500034"),
            "Silver",
            195,
        ),
        (
            "Neha Joshi",
            "+91 97012 34567",
            "neha.joshi@gmail.com",
            "New",
            Decimal("780.00"),
            1,
            "Ordered Paneer Butter Masala combo online.",
            ("Home", "Plot 21, Madhapur Kavuri Hills", "Near Metro Pillar", "Hyderabad", "500081"),
            "Silver",
            78,
        ),
    ]

    result: dict[str, tuple[Customer, LoyaltyAccount]] = {}
    for idx, (name, phone, email, segment, spend, visits, notes, addr_tuple, tier, pts) in enumerate(specs, start=1):
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.phone == phone).first()
        if not cust:
            cust = Customer(
                id=_seed_id(f"ss-op:{tenant_id}:cust:{phone}"),
                tenant_id=tenant_id,
                name=name,
                phone=phone,
                email=email,
                segment=segment,
                total_spend=spend,
                total_visits=visits,
                notes=notes,
                first_visit_at=now - timedelta(days=30 - idx * 3),
                last_visit_at=now - timedelta(days=max(0, 6 - idx)),
            )
            db.add(cust)
            db.flush()
            label, address, landmark, city, postal = addr_tuple
            db.add(
                CustomerAddress(
                    id=_seed_id(f"ss-op:{tenant_id}:addr:{phone}"),
                    customer_id=cust.id,
                    label=label,
                    address=address,
                    landmark=landmark,
                    city=city,
                    postal_code=postal,
                )
            )
        acct = db.query(LoyaltyAccount).filter(LoyaltyAccount.customer_id == cust.id).first()
        if not acct:
            acct = LoyaltyAccount(
                id=_seed_id(f"ss-op:{tenant_id}:loyalty:{phone}"),
                tenant_id=tenant_id,
                customer_id=cust.id,
                tier=tier,
                points_balance=pts,
            )
            db.add(acct)
            db.flush()
        result[name] = (cust, acct)

    db.flush()
    return result


def _create_ss_order_bundle(
    db: Session,
    tenant_id: str,
    branch_id: str,
    order_key: str,
    order_number: str,
    order_type: str,
    status_val: str,
    created_at: datetime,
    cashier: User,
    waiter: Optional[User],
    customer: Optional[Customer],
    loyalty_acct: Optional[LoyaltyAccount],
    table: Optional[RestaurantTable],
    items_with_qty: list[tuple[MenuItem, int, Optional[str]]],
    stations: list[KitchenStation],
    payment_method: Optional[str] = None,
    payment_ref: Optional[str] = None,
    invoice_number: Optional[str] = None,
    cash_session_id: Optional[str] = None,
    kot_status: str = "New",
    kot_number_prefix: str = "KOT-SS",
    notes: Optional[str] = None,
) -> Order:
    """Creates a realistic Order + OrderItems and optionally Invoice/Payment/Loyalty or Active KOTs."""
    subtotal = Decimal("0.00")
    tax_amount = Decimal("0.00")
    prepared_items: list[tuple[MenuItem, int, Optional[str], Decimal, Decimal]] = []

    for dish, qty, item_notes in items_with_qty:
        unit_price = Decimal(str(dish.base_price))
        line_sub = unit_price * qty
        rate = Decimal(str(dish.tax_rate or Decimal("5.00")))
        line_tax = round((line_sub * rate) / Decimal("100.00"), 2)
        subtotal += line_sub
        tax_amount += line_tax
        prepared_items.append((dish, qty, item_notes, unit_price, line_sub))

    total_amount = subtotal + tax_amount
    order = Order(
        id=_seed_id(f"ss-op:{tenant_id}:order:{order_key}"),
        tenant_id=tenant_id,
        branch_id=branch_id,
        order_number=order_number,
        order_type=order_type,
        status=status_val,
        table_id=table.id if table else None,
        table_number=table.table_number if table else None,
        customer_id=customer.id if customer else None,
        customer_name=customer.name if customer else "Walk-in Guest",
        customer_phone=customer.phone if customer else None,
        subtotal=subtotal,
        discount_amount=Decimal("0.00"),
        tax_amount=tax_amount,
        service_charge=Decimal("0.00"),
        total_amount=total_amount,
        cashier_id=cashier.id,
        cashier_name=cashier.full_name,
        waiter_id=waiter.id if waiter else None,
        waiter_name=waiter.full_name if waiter else None,
        notes=notes,
        created_at=created_at,
    )
    db.add(order)
    db.flush()

    created_ois: list[tuple[MenuItem, OrderItem]] = []
    for idx, (dish, qty, item_notes, unit_price, line_sub) in enumerate(prepared_items, start=1):
        oi = OrderItem(
            id=_seed_id(f"ss-op:{tenant_id}:oi:{order_key}:{idx}"),
            order_id=order.id,
            menu_item_id=dish.id,
            item_name=dish.name,
            unit_price=unit_price,
            cost_price=Decimal(str(dish.cost_price or (unit_price * Decimal("0.38")))),
            quantity=qty,
            subtotal=line_sub,
            tax_rate=Decimal(str(dish.tax_rate or Decimal("5.00"))),
            modifiers=[],
            notes=item_notes,
        )
        db.add(oi)
        created_ois.append((dish, oi))
    db.flush()

    if status_val == "Completed" and invoice_number and payment_method:
        inv = Invoice(
            id=_seed_id(f"ss-op:{tenant_id}:inv:{order_key}"),
            tenant_id=tenant_id,
            branch_id=branch_id,
            order_id=order.id,
            invoice_number=invoice_number,
            subtotal=subtotal,
            discount=Decimal("0.00"),
            tax=tax_amount,
            service_charge=Decimal("0.00"),
            total_amount=total_amount,
            paid_amount=total_amount,
            status="Paid",
            created_at=created_at,
        )
        db.add(inv)
        db.flush()
        db.add(
            Payment(
                id=_seed_id(f"ss-op:{tenant_id}:pay:{order_key}"),
                tenant_id=tenant_id,
                branch_id=branch_id,
                invoice_id=inv.id,
                order_id=order.id,
                amount=total_amount,
                payment_method=payment_method,
                payment_reference=payment_ref,
                status="Success",
                cash_register_session_id=cash_session_id if payment_method == "Cash" else None,
                created_at=created_at,
            )
        )
        if loyalty_acct:
            earned = max(1, int(total_amount // Decimal("10.00")))
            db.add(
                LoyaltyTransaction(
                    id=_seed_id(f"ss-op:{tenant_id}:ltx:{order_key}"),
                    tenant_id=tenant_id,
                    account_id=loyalty_acct.id,
                    transaction_type="EARN",
                    points=earned,
                    running_balance=loyalty_acct.points_balance,
                    order_id=order.id,
                    reason=f"Earned on Order {order_number}",
                    created_at=created_at,
                )
            )
    elif status_val == "InKitchen" and stations:
        station_groups: dict[str, list[OrderItem]] = {}
        fallback_station_id = stations[0].id
        valid_station_ids = {s.id for s in stations}
        for dish, oi in created_ois:
            st_id = dish.kitchen_station_id if dish.kitchen_station_id in valid_station_ids else fallback_station_id
            station_groups.setdefault(st_id, []).append(oi)

        for s_idx, (st_id, ois) in enumerate(station_groups.items(), start=1):
            kot = KOT(
                id=_seed_id(f"ss-op:{tenant_id}:kot:{order_key}:{s_idx}"),
                tenant_id=tenant_id,
                branch_id=branch_id,
                order_id=order.id,
                kitchen_station_id=st_id,
                kot_number=f"{kot_number_prefix}-{s_idx}",
                status=kot_status,
                waiter_name=waiter.full_name if waiter else cashier.full_name,
                notes=notes,
                created_at=created_at,
                started_preparing_at=(created_at + timedelta(minutes=2)) if kot_status in ("Preparing", "Ready") else None,
                ready_at=(created_at + timedelta(minutes=9)) if kot_status == "Ready" else None,
            )
            db.add(kot)
            db.flush()
            for k_idx, oi in enumerate(ois, start=1):
                db.add(
                    KOTItem(
                        id=_seed_id(f"ss-op:{tenant_id}:kotitem:{order_key}:{s_idx}:{k_idx}"),
                        kot_id=kot.id,
                        order_item_id=oi.id,
                        item_name=oi.item_name,
                        variant_name=oi.variant_name,
                        modifiers_summary=None,
                        quantity=oi.quantity,
                        notes=oi.notes,
                        status=kot_status,
                    )
                )
        if table:
            table.status = "Occupied"
            table.active_order_id = order.id
            if not table.occupied_since:
                table.occupied_since = created_at

    return order


def _ensure_branch_stations(db: Session, tenant_id: str, branch_id: str) -> list[KitchenStation]:
    """Ensures every branch has a Kitchen and KOT routing stations for KDS and POS."""
    _ensure_spice_symphony_kitchen_stations(db, tenant_id, branch_id)
    stations = db.query(KitchenStation).filter(
        KitchenStation.tenant_id == tenant_id,
        KitchenStation.branch_id == branch_id,
    ).all()
    if stations:
        return stations

    kitchen = db.query(Kitchen).filter(
        Kitchen.tenant_id == tenant_id,
        Kitchen.branch_id == branch_id,
    ).first()
    if not kitchen:
        kitchen = Kitchen(
            id=_seed_id(f"ss-op:{tenant_id}:kitchen:{branch_id}"),
            tenant_id=tenant_id,
            branch_id=branch_id,
            name="Main Kitchen",
        )
        db.add(kitchen)
        db.flush()

    station_defs = [
        ("Curry & Biryani Station", "192.168.1.51"),
        ("Tandoor & Grill", "192.168.1.52"),
        ("Tiffin & Beverage Counter", "192.168.1.53"),
    ]
    created: list[KitchenStation] = []
    for st_name, printer_ip in station_defs:
        st = KitchenStation(
            id=_seed_id(f"ss-op:{tenant_id}:station:{branch_id}:{st_name}"),
            tenant_id=tenant_id,
            branch_id=branch_id,
            kitchen_id=kitchen.id,
            name=st_name,
            printer_ip=printer_ip,
        )
        db.add(st)
        created.append(st)
    db.flush()
    return created


def seed_spice_symphony_full_operations(
    db: Session,
    tenant_id: str,
    branch_1_id: str,
    branch_2_id: Optional[str],
    owner_user: Optional[User],
) -> None:
    """
    Idempotently seeds complete end-to-end Indian restaurant operational data for Spice Symphony
    across staff, tables, reservations, inventory/low-stock alerts, recipes, suppliers/POs/GRNs,
    CRM/loyalty, open cash registers, expenses, 7-day sales orders, active KOTs, and delivery dispatch.
    """
    if not owner_user:
        owner_user = (
            db.query(User).filter(User.tenant_id == tenant_id, User.role == "TENANT_OWNER").first()
            or db.query(User).filter(User.tenant_id == tenant_id).first()
        )
    owner_name = owner_user.full_name if owner_user else "Rajesh Verma"

    stations_b1 = _ensure_branch_stations(db, tenant_id, branch_1_id)
    stations_b2 = _ensure_branch_stations(db, tenant_id, branch_2_id) if branch_2_id else []

    menu_items = db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id).order_by(MenuItem.display_order.asc(), MenuItem.name.asc()).all()
    if not menu_items:
        return

    default_menu = db.query(Menu).filter(Menu.tenant_id == tenant_id).order_by(Menu.display_order.asc()).first()
    cashier_b1, waiter_b1, cashier_b2 = _ensure_ss_staff(db, tenant_id, branch_1_id, branch_2_id, owner_user)
    b1_tables, b2_tables = _ensure_ss_tables_and_reservations(
        db,
        tenant_id,
        branch_1_id,
        branch_2_id,
        default_menu.id if default_menu else None,
    )
    inv_by_sku = _ensure_ss_inventory_and_recipes(db, tenant_id, branch_1_id, menu_items, owner_name)
    _ensure_ss_procurement(db, tenant_id, branch_1_id, inv_by_sku, "Anitha Reddy")
    crm_map = _ensure_ss_crm(db, tenant_id)

    now = datetime.utcnow()

    # Open Cash Register & Shift Session for Branch 1 (hyderabad)
    reg_b1 = db.query(CashRegister).filter(
        CashRegister.tenant_id == tenant_id,
        CashRegister.branch_id == branch_1_id,
    ).first()
    if not reg_b1:
        reg_b1 = CashRegister(
            id=_seed_id(f"ss-op:{tenant_id}:reg:{branch_1_id}"),
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            name="Counter POS 01",
            status="Open",
        )
        db.add(reg_b1)
        db.flush()

    sess_b1 = db.query(CashRegisterSession).filter(
        CashRegisterSession.tenant_id == tenant_id,
        CashRegisterSession.branch_id == branch_1_id,
        CashRegisterSession.status == "Open",
    ).first()
    if not sess_b1:
        sess_b1 = CashRegisterSession(
            id=_seed_id(f"ss-op:{tenant_id}:sess:{branch_1_id}"),
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            register_id=reg_b1.id,
            cashier_id=cashier_b1.id,
            cashier_name=cashier_b1.full_name,
            opened_at=now - timedelta(hours=5),
            opening_float=Decimal("3000.00"),
            cash_sales=Decimal("0.00"),
            cash_in=Decimal("2000.00"),
            cash_out=Decimal("450.00"),
            cash_refunds=Decimal("0.00"),
            expected_closing_cash=Decimal("4550.00"),
            status="Open",
            notes="Morning shift — Banjara Hills Flagship",
        )
        db.add(sess_b1)
        db.flush()
        db.add_all([
            CashTransaction(
                id=_seed_id(f"ss-op:{tenant_id}:cashtx:in"),
                session_id=sess_b1.id,
                transaction_type="CASH_IN",
                amount=Decimal("2000.00"),
                reason="Added ₹100 & ₹50 change float from branch safe",
                authorized_by="Anitha Reddy",
            ),
            CashTransaction(
                id=_seed_id(f"ss-op:{tenant_id}:cashtx:out"),
                session_id=sess_b1.id,
                transaction_type="CASH_OUT",
                amount=Decimal("450.00"),
                reason="Petty cash: fresh curry leaves, mint & lemons",
                authorized_by="Anitha Reddy",
            ),
        ])
        db.flush()

    # Expenses for P&L reporting on Branch 1
    if db.query(Expense).filter(Expense.tenant_id == tenant_id, Expense.branch_id == branch_1_id).count() == 0:
        db.add_all([
            Expense(
                id=_seed_id(f"ss-op:{tenant_id}:exp:1"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                category="Utilities",
                amount=Decimal("4250.00"),
                payment_method="Bank Transfer",
                payee="TSPDCL & Commercial LPG",
                expense_date=now - timedelta(days=4),
                notes="Kitchen commercial gas cylinders & power bill",
            ),
            Expense(
                id=_seed_id(f"ss-op:{tenant_id}:exp:2"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                category="Supplies & Packaging",
                amount=Decimal("2150.00"),
                payment_method="UPI",
                payee="EcoPack Containers Hyderabad",
                expense_date=now - timedelta(days=2),
                notes="Leak-proof biryani handi tubs & banana leaf liners",
            ),
            Expense(
                id=_seed_id(f"ss-op:{tenant_id}:exp:3"),
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                category="Staff Welfare",
                amount=Decimal("1600.00"),
                payment_method="Cash",
                payee="Kitchen Staff Mess",
                expense_date=now - timedelta(days=1),
                notes="Weekly staff meals & aprons",
            ),
        ])

    # Signature Indian dishes for orders
    biryani = _ss_find_dish(menu_items, "Hyderabadi Chicken Dum Biryani", "Chicken Biryani", "Biryani")
    chicken65 = _ss_find_dish(menu_items, "Chicken 65")
    paneer_bm = _ss_find_dish(menu_items, "Paneer Butter Masala", "Paneer")
    masala_dosa = _ss_find_dish(menu_items, "Masala Dosa", "Dosa")
    idli = _ss_find_dish(menu_items, "Idli Sambar", "Idli")
    naan = _ss_find_dish(menu_items, "Butter Naan", "Roti")
    andhra_meals = _ss_find_dish(menu_items, "Andhra Meals", "Meals", "Thali")
    egg_curry = _ss_find_dish(menu_items, "Andhra Egg Curry", "Egg Curry")
    samosa = _ss_find_dish(menu_items, "Aloo Samosa", "Samosa")
    coffee = _ss_find_dish(menu_items, "Madras Filter Coffee", "Coffee")
    gulab = _ss_find_dish(menu_items, "Double Ka Meetha", "Gulab Jamun")

    rohan_c, rohan_l = crm_map["Rohan Kulkarni"]
    meenakshi_c, meenakshi_l = crm_map["Meenakshi Iyer"]
    sid_c, sid_l = crm_map["Siddharth Reddy"]
    farhan_c, farhan_l = crm_map["Farhan Ali"]
    neha_c, neha_l = crm_map["Neha Joshi"]

    # Seed 8 Completed orders across 7 days + 2 Live InKitchen orders on Branch 1
    if db.query(Order).filter(Order.tenant_id == tenant_id, Order.branch_id == branch_1_id).count() == 0:
        completed_specs = [
            ("hyd-1", "ORD-SS-1001", "INV-SS-1001", "DineIn", now - timedelta(days=6, hours=3), rohan_c, rohan_l, b1_tables["T-01"], "UPI", "UPI-4091283", [(biryani, 3, None), (chicken65, 2, "Extra crispy"), (coffee, 2, None)]),
            ("hyd-2", "ORD-SS-1002", "INV-SS-1002", "Takeaway", now - timedelta(days=5, hours=2), meenakshi_c, meenakshi_l, None, "Card", "CARD-991042", [(masala_dosa, 4, "Crispy roast"), (idli, 4, None), (coffee, 4, None)]),
            ("hyd-3", "ORD-SS-1003", "INV-SS-1003", "DineIn", now - timedelta(days=4, hours=4), sid_c, sid_l, b1_tables["T-06"], "UPI", "UPI-5523190", [(andhra_meals, 4, None), (egg_curry, 2, "Spicy"), (gulab, 3, None)]),
            ("hyd-4", "ORD-SS-1004", "INV-SS-1004", "QR", now - timedelta(days=3, hours=1), farhan_c, farhan_l, b1_tables["T-01"], "UPI", "UPI-6731104", [(paneer_bm, 2, None), (naan, 6, None), (samosa, 3, None)]),
            ("hyd-5", "ORD-SS-1005", "INV-SS-1005", "Delivery", now - timedelta(days=2, hours=2), rohan_c, rohan_l, None, "UPI", "UPI-7190023", [(biryani, 4, "Send raita & salan"), (chicken65, 2, None)]),
            ("hyd-6", "ORD-SS-1006", "INV-SS-1006", "DineIn", now - timedelta(days=1, hours=3), meenakshi_c, meenakshi_l, b1_tables["T-06"], "Cash", None, [(paneer_bm, 2, None), (naan, 4, None), (masala_dosa, 2, None), (coffee, 2, None)]),
            ("hyd-7", "ORD-SS-1007", "INV-SS-1007", "Delivery", now - timedelta(hours=3), neha_c, neha_l, None, "Card", "CARD-118904", [(biryani, 2, "Leave at lobby"), (paneer_bm, 1, None), (naan, 3, None)]),
            ("hyd-8", "ORD-SS-1008", "INV-SS-1008", "DineIn", now - timedelta(hours=1, minutes=20), sid_c, sid_l, b1_tables["T-01"], "Cash", None, [(andhra_meals, 2, None), (chicken65, 2, None), (gulab, 2, None)]),
        ]

        created_orders: dict[str, Order] = {}
        today_cash_sales = Decimal("0.00")
        for key, ord_no, inv_no, otype, ts, cust, loy, tbl, pay_m, pay_ref, line_items in completed_specs:
            ord_obj = _create_ss_order_bundle(
                db=db,
                tenant_id=tenant_id,
                branch_id=branch_1_id,
                order_key=key,
                order_number=ord_no,
                order_type=otype,
                status_val="Completed",
                created_at=ts,
                cashier=cashier_b1,
                waiter=waiter_b1 if otype in ("DineIn", "QR") else None,
                customer=cust,
                loyalty_acct=loy,
                table=tbl,
                items_with_qty=line_items,
                stations=stations_b1,
                payment_method=pay_m,
                payment_ref=pay_ref,
                invoice_number=inv_no,
                cash_session_id=sess_b1.id,
            )
            created_orders[key] = ord_obj
            if pay_m == "Cash" and ts.date() == now.date():
                today_cash_sales += Decimal(str(ord_obj.total_amount))

        sess_b1.cash_sales = today_cash_sales
        sess_b1.expected_closing_cash = (
            sess_b1.opening_float
            + sess_b1.cash_sales
            + sess_b1.cash_in
            - sess_b1.cash_out
            - sess_b1.cash_refunds
        )

        # Delivery order 9 (Live InKitchen order with OutForDelivery rider)
        live_deliv_order = _create_ss_order_bundle(
            db=db,
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            order_key="hyd-9",
            order_number="ORD-SS-1009",
            order_type="Delivery",
            status_val="InKitchen",
            created_at=now - timedelta(minutes=22),
            cashier=cashier_b1,
            waiter=None,
            customer=rohan_c,
            loyalty_acct=rohan_l,
            table=None,
            items_with_qty=[(biryani, 2, "Extra double masala"), (chicken65, 1, None)],
            stations=stations_b1,
            kot_status="Ready",
            kot_number_prefix="KOT-SS-101",
            notes="Online prepaid delivery — pack hot thermal bag",
        )
        created_orders["hyd-9"] = live_deliv_order

        # Live Dine-In Order 10 on Table T-02
        _create_ss_order_bundle(
            db=db,
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            order_key="hyd-10",
            order_number="ORD-SS-1010",
            order_type="DineIn",
            status_val="InKitchen",
            created_at=now - timedelta(minutes=14),
            cashier=cashier_b1,
            waiter=waiter_b1,
            customer=meenakshi_c,
            loyalty_acct=meenakshi_l,
            table=b1_tables["T-02"],
            items_with_qty=[(paneer_bm, 2, "Medium spice"), (naan, 4, None), (biryani, 1, None)],
            stations=stations_b1,
            kot_status="Preparing",
            kot_number_prefix="KOT-SS-102",
            notes="Table T-02 family dinner — serve starters first",
        )

        # Live Dine-In Order 11 on Table T-03
        _create_ss_order_bundle(
            db=db,
            tenant_id=tenant_id,
            branch_id=branch_1_id,
            order_key="hyd-11",
            order_number="ORD-SS-1011",
            order_type="DineIn",
            status_val="InKitchen",
            created_at=now - timedelta(minutes=5),
            cashier=cashier_b1,
            waiter=waiter_b1,
            customer=farhan_c,
            loyalty_acct=farhan_l,
            table=b1_tables["T-03"],
            items_with_qty=[(masala_dosa, 2, "Ghee roast"), (samosa, 2, None), (coffee, 2, "Strong")],
            stations=stations_b1,
            kot_status="New",
            kot_number_prefix="KOT-SS-103",
            notes="Table T-03 evening tiffins",
        )

        # Delivery Executives & Delivery Dispatch Orders for Branch 1
        if db.query(DeliveryExecutive).filter(DeliveryExecutive.tenant_id == tenant_id, DeliveryExecutive.branch_id == branch_1_id).count() == 0:
            r1 = DeliveryExecutive(id=_seed_id(f"ss-op:{tenant_id}:rider:1"), tenant_id=tenant_id, branch_id=branch_1_id, name="Mahesh Babu K", phone="+91 98485 11101", vehicle_number="TS-09-EV-4421", is_available=False)
            r2 = DeliveryExecutive(id=_seed_id(f"ss-op:{tenant_id}:rider:2"), tenant_id=tenant_id, branch_id=branch_1_id, name="Imran Sheikh", phone="+91 98485 11102", vehicle_number="TS-09-EV-8812", is_available=True)
            r3 = DeliveryExecutive(id=_seed_id(f"ss-op:{tenant_id}:rider:3"), tenant_id=tenant_id, branch_id=branch_1_id, name="Venkat Rao", phone="+91 98485 11103", vehicle_number="TS-09-UC-3094", is_available=True)
            db.add_all([r1, r2, r3])
            db.flush()

            db.add_all([
                DeliveryOrder(
                    id=_seed_id(f"ss-op:{tenant_id}:deliv:1"),
                    tenant_id=tenant_id,
                    branch_id=branch_1_id,
                    order_id=created_orders["hyd-9"].id,
                    customer_name=rohan_c.name,
                    customer_phone=rohan_c.phone,
                    delivery_address="Flat 402, My Home Bhooja, Hitec City, Hyderabad",
                    delivery_fee=Decimal("45.00"),
                    status="OutForDelivery",
                    rider_id=r1.id,
                    rider_name=r1.name,
                    dispatched_at=now - timedelta(minutes=8),
                    created_at=now - timedelta(minutes=22),
                ),
                DeliveryOrder(
                    id=_seed_id(f"ss-op:{tenant_id}:deliv:2"),
                    tenant_id=tenant_id,
                    branch_id=branch_1_id,
                    order_id=created_orders["hyd-7"].id,
                    customer_name=neha_c.name,
                    customer_phone=neha_c.phone,
                    delivery_address="Plot 21, Madhapur Kavuri Hills, Hyderabad",
                    delivery_fee=Decimal("35.00"),
                    status="Assigned",
                    rider_id=r2.id,
                    rider_name=r2.name,
                    created_at=now - timedelta(hours=3),
                ),
                DeliveryOrder(
                    id=_seed_id(f"ss-op:{tenant_id}:deliv:3"),
                    tenant_id=tenant_id,
                    branch_id=branch_1_id,
                    order_id=created_orders["hyd-5"].id,
                    customer_name=rohan_c.name,
                    customer_phone=rohan_c.phone,
                    delivery_address="Flat 402, My Home Bhooja, Hitec City, Hyderabad",
                    delivery_fee=Decimal("45.00"),
                    status="Delivered",
                    rider_id=r3.id,
                    rider_name=r3.name,
                    dispatched_at=now - timedelta(days=2, hours=1, minutes=40),
                    delivered_at=now - timedelta(days=2, hours=1, minutes=12),
                    created_at=now - timedelta(days=2, hours=2),
                ),
            ])

    # Branch 2 (Hyderabad - Gachibowli) Register + Sample Orders
    if branch_2_id:
        reg_b2 = db.query(CashRegister).filter(
            CashRegister.tenant_id == tenant_id,
            CashRegister.branch_id == branch_2_id,
        ).first()
        if not reg_b2:
            reg_b2 = CashRegister(
                id=_seed_id(f"ss-op:{tenant_id}:reg:{branch_2_id}"),
                tenant_id=tenant_id,
                branch_id=branch_2_id,
                name="Gachibowli POS 01",
                status="Open",
            )
            db.add(reg_b2)
            db.flush()

        sess_b2 = db.query(CashRegisterSession).filter(
            CashRegisterSession.tenant_id == tenant_id,
            CashRegisterSession.branch_id == branch_2_id,
            CashRegisterSession.status == "Open",
        ).first()
        if not sess_b2:
            sess_b2 = CashRegisterSession(
                id=_seed_id(f"ss-op:{tenant_id}:sess:{branch_2_id}"),
                tenant_id=tenant_id,
                branch_id=branch_2_id,
                register_id=reg_b2.id,
                cashier_id=cashier_b2.id,
                cashier_name=cashier_b2.full_name,
                opened_at=now - timedelta(hours=4),
                opening_float=Decimal("2500.00"),
                cash_sales=Decimal("0.00"),
                cash_in=Decimal("0.00"),
                cash_out=Decimal("0.00"),
                cash_refunds=Decimal("0.00"),
                expected_closing_cash=Decimal("2500.00"),
                status="Open",
                notes="Gachibowli Financial District POS Shift",
            )
            db.add(sess_b2)
            db.flush()

        if db.query(Order).filter(Order.tenant_id == tenant_id, Order.branch_id == branch_2_id).count() == 0:
            _create_ss_order_bundle(
                db=db,
                tenant_id=tenant_id,
                branch_id=branch_2_id,
                order_key="gcb-1",
                order_number="ORD-SS-GCB-001",
                order_type="DineIn",
                status_val="Completed",
                created_at=now - timedelta(days=1, hours=2),
                cashier=cashier_b2,
                waiter=cashier_b2,
                customer=meenakshi_c,
                loyalty_acct=meenakshi_l,
                table=b2_tables.get("T-01"),
                items_with_qty=[(biryani, 2, None), (coffee, 2, None)],
                stations=stations_b2,
                payment_method="UPI",
                payment_ref="UPI-GCB-8812",
                invoice_number="INV-SS-GCB-001",
                cash_session_id=sess_b2.id,
            )
            gcb_cash_ord = _create_ss_order_bundle(
                db=db,
                tenant_id=tenant_id,
                branch_id=branch_2_id,
                order_key="gcb-2",
                order_number="ORD-SS-GCB-002",
                order_type="Takeaway",
                status_val="Completed",
                created_at=now - timedelta(hours=2),
                cashier=cashier_b2,
                waiter=None,
                customer=sid_c,
                loyalty_acct=sid_l,
                table=None,
                items_with_qty=[(masala_dosa, 2, None), (idli, 2, None)],
                stations=stations_b2,
                payment_method="Cash",
                invoice_number="INV-SS-GCB-002",
                cash_session_id=sess_b2.id,
            )
            sess_b2.cash_sales = Decimal(str(gcb_cash_ord.total_amount))
            sess_b2.expected_closing_cash = sess_b2.opening_float + sess_b2.cash_sales

            _create_ss_order_bundle(
                db=db,
                tenant_id=tenant_id,
                branch_id=branch_2_id,
                order_key="gcb-3",
                order_number="ORD-SS-GCB-003",
                order_type="DineIn",
                status_val="InKitchen",
                created_at=now - timedelta(minutes=11),
                cashier=cashier_b2,
                waiter=cashier_b2,
                customer=rohan_c,
                loyalty_acct=rohan_l,
                table=b2_tables.get("T-02"),
                items_with_qty=[(paneer_bm, 2, None), (naan, 4, None)],
                stations=stations_b2,
                kot_status="Preparing",
                kot_number_prefix="KOT-SS-GCB-101",
                notes="Gachibowli Table T-02 lunch",
            )

    db.flush()


def upgrade_existing_menu_data():
    """Upgrades seeded tenants to pure Indian menus and ensures Spice Symphony full operational data."""
    Base.metadata.create_all(bind=engine)
    ensure_schema_columns(engine)
    db: Session = SessionLocal()
    try:
        t1 = db.query(Tenant).filter(Tenant.slug == "bella-napoli").first()
        if t1:
            b1 = db.query(Branch).filter(Branch.tenant_id == t1.id).order_by(Branch.created_at.asc()).first()
            if b1:
                _purge_non_indian_and_legacy_records(db, t1.id)
                seed_spice_symphony_menus(db, t1.id, b1.id)
                _purge_non_indian_and_legacy_records(db, t1.id)

        t2 = db.query(Tenant).filter(Tenant.slug == "spice-symphony").first()
        if t2:
            plan_pro = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == "pro").first()
            if plan_pro and t2.subscription and t2.subscription.plan_id != plan_pro.id:
                t2.subscription.plan_id = plan_pro.id

            branches = db.query(Branch).filter(Branch.tenant_id == t2.id).order_by(Branch.created_at.asc()).all()
            b2 = branches[0] if len(branches) >= 1 else None
            b2b = branches[1] if len(branches) >= 2 else None
            if b2:
                b2.name = "hyderabad"
                if not b2b:
                    b2b = Branch(
                        id=_seed_id(f"ss-op:{t2.id}:branch:SS-HYD-02"),
                        tenant_id=t2.id,
                        name="Hyderabad - Gachibowli",
                        code="SS-HYD-02",
                        address="Financial District",
                        city="Hyderabad",
                        state="Telangana",
                        tax_rate=Decimal("5.00"),
                        currency="INR",
                        is_active=True,
                    )
                    db.add(b2b)
                    db.flush()
                _purge_non_indian_and_legacy_records(db, t2.id)
                seed_spice_symphony_menus(db, t2.id, b2.id)
                _purge_non_indian_and_legacy_records(db, t2.id)
                owner = db.query(User).filter(User.tenant_id == t2.id, User.role == "TENANT_OWNER").first()
                seed_spice_symphony_full_operations(db, t2.id, b2.id, b2b.id, owner)

        db.commit()
        print("✅ All tenants upgraded with Indian menus & full Spice Symphony operational data!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    upgrade_existing_menu_data()
