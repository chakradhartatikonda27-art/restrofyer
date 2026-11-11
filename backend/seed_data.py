import uuid
from datetime import datetime, timedelta
from decimal import Decimal
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
from app.models.financial import CashRegister, CashRegisterSession, Expense
from app.models.delivery import DeliveryExecutive, DeliveryOrder

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
            id=str(uuid.uuid4()),
            email="admin@restaurantsaas.com",
            password_hash=get_password_hash("SuperAdmin@2026!"),
            full_name="Platform Super Administrator",
            role="SUPER_ADMIN",
            is_active=True
        )
        db.add(super_admin)

        # 2. Subscription Plans
        plan_starter = SubscriptionPlan(
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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

        # 3. Tenant 1: Bella Napoli Trattoria (Flagship Multi-branch Italian)
        tenant_1 = Tenant(
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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
            id=str(uuid.uuid4()),
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

        # 4. Tenant 2: Spice Symphony Bistro (To prove multi-tenant isolation!)
        tenant_2 = Tenant(
            id=str(uuid.uuid4()),
            name="Spice Symphony Bistro",
            slug="spice-symphony",
            business_type="Modern Indian Bistro",
            status="Active",
            contact_email="owner@spicesymphony.com",
            contact_phone="+91 98111 22233",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
            onboarding_completed=True
        )
        db.add(tenant_2)
        db.flush()

        sub_2 = Subscription(
            id=str(uuid.uuid4()),
            tenant_id=tenant_2.id,
            plan_id=plan_growth.id,
            status="Active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(sub_2)

        branch_2 = Branch(
            id=str(uuid.uuid4()),
            tenant_id=tenant_2.id,
            name="hyderabad",
            code="SS-HYD-01",
            address="Road No 12, Banjara Hills",
            city="Hyderabad",
            state="Telangana",
            tax_rate=Decimal("5.00"),
            currency="INR",
            is_active=True
        )
        branch_2b = Branch(
            id=str(uuid.uuid4()),
            tenant_id=tenant_2.id,
            name="Hyderabad - Gachibowli",
            code="SS-HYD-02",
            address="Financial District",
            city="Hyderabad",
            state="Telangana",
            tax_rate=Decimal("5.00"),
            currency="INR",
            is_active=True
        )
        db.add_all([branch_2, branch_2b])
        db.flush()

        user_tenant2 = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_2.id,
            email="owner@spicesymphony.com",
            password_hash=get_password_hash("Owner@456"),
            full_name="Rajesh Verma",
            role="TENANT_OWNER",
            branch_id=branch_2.id,
            is_active=True
        )
        db.add(user_tenant2)
        db.flush()

        # Dining area & tables for Spice Symphony (for Assign Menu to Table demos)
        ss_area = DiningArea(id=str(uuid.uuid4()), tenant_id=tenant_2.id, branch_id=branch_2.id, name="Main Dining Hall", display_order=1)
        db.add(ss_area)
        db.flush()
        db.add_all([
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_2.id, branch_id=branch_2.id, area_id=ss_area.id, table_number="T-01", name="Andhra Courtyard 1", capacity=4, status="Available", qr_code_token="QR-SPICE-T01"),
            RestaurantTable(id=str(uuid.uuid4()), tenant_id=tenant_2.id, branch_id=branch_2.id, area_id=ss_area.id, table_number="T-02", name="Nizam Booth 2", capacity=6, status="Available", qr_code_token="QR-SPICE-T02"),
        ])

        # Rich Hyderabad Menu Hierarchy matching Restofyer screenshot
        seed_spice_symphony_menus(db, tenant_2.id, branch_2.id)

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


def upgrade_existing_menu_data():
    """Upgrades seeded tenants to pure Indian cuisines, Indian categories, and Indian dishes only."""
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
            b2 = db.query(Branch).filter(Branch.tenant_id == t2.id).order_by(Branch.created_at.asc()).first()
            if b2:
                b2.name = "hyderabad"
                if db.query(Branch).filter(Branch.tenant_id == t2.id).count() == 1:
                    db.add(
                        Branch(
                            id=str(uuid.uuid4()),
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
                    )
                    db.flush()
                if db.query(RestaurantTable).filter(RestaurantTable.tenant_id == t2.id).count() == 0:
                    area = DiningArea(id=str(uuid.uuid4()), tenant_id=t2.id, branch_id=b2.id, name="Main Dining Hall", display_order=1)
                    db.add(area)
                    db.flush()
                    db.add_all([
                        RestaurantTable(id=str(uuid.uuid4()), tenant_id=t2.id, branch_id=b2.id, area_id=area.id, table_number="T-01", name="Andhra Courtyard 1", capacity=4, status="Available", qr_code_token="QR-SPICE-T01"),
                        RestaurantTable(id=str(uuid.uuid4()), tenant_id=t2.id, branch_id=b2.id, area_id=area.id, table_number="T-02", name="Nizam Booth 2", capacity=6, status="Available", qr_code_token="QR-SPICE-T02"),
                    ])
                _purge_non_indian_and_legacy_records(db, t2.id)
                seed_spice_symphony_menus(db, t2.id, b2.id)
                _purge_non_indian_and_legacy_records(db, t2.id)

        db.commit()
        print("✅ All tenants upgraded to pure Indian dishes, categories & cuisines!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    upgrade_existing_menu_data()
