from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.models.menu import Cuisine, Menu, MenuCategory, MenuItem

DEFAULT_CUISINES: List[Tuple[str, str]] = [
    ("South Indian", "Dosa, Idli, Vada, Uttapam & southern rice staples"),
    ("North Indian", "Makhani gravies, dal tadka, rotis & thalis"),
    ("Andhra Special", "Authentic spicy Andhra curries, pappu & mirchi specialties"),
    ("Telangana Special", "Hyderabadi dum biryanis, baghara baingan & regional fare"),
    ("Kerala Special", "Malabar curries, appams & coconut coastal dishes"),
    ("Tandoori", "Clay-oven kebabs, tikkas, naan & rotis"),
    ("Mughlai", "Rich royal kormas, biryanis & slow-braised gravies"),
    ("Chettinad", "Aromatic stone-ground spice pepper & roast specials"),
    ("Indo-Chinese", "Desi Gobi/Veg Manchurian, chilli paneer & noodles"),
    ("Indian Street Food", "Crisp chaat, samosa, pakoda, pav & evening snacks"),
]

DEFAULT_DISH_CATEGORIES: List[str] = [
    "Starters",
    "Soups",
    "Tiffins / Breakfast",
    "Main Course",
    "Meals / Thali",
    "Rice & Biryani",
    "Curries & Gravies",
    "Breads & Rotis",
    "Dosa & Idli",
    "Snacks",
    "Desserts",
    "Beverages",
    "Combos / Special Meals",
]

# Format: (name, description, price, cuisine_name, food_type, category_name, schedule_menu_name, tax_rate)
SAMPLE_INDIAN_CATALOG: List[Tuple[str, str, str, str, str, str, str, str]] = [
    # South Indian & Tiffins
    ("Idli (2 Pcs)", "Steamed soft rice cakes served with sambar and coconut-ginger chutney.", "60.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00"),
    ("Medu Vada", "Crispy spiced black lentil doughnuts with sambar and chutney.", "70.00", "South Indian", "VEGAN", "Tiffins / Breakfast", "Breakfast Menu", "5.00"),
    ("Plain Dosa", "Golden crispy fermented rice crepe with chutney and sambar.", "80.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00"),
    ("Masala Dosa", "Crisp dosa filled with turmeric tempered potato masala.", "110.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00"),
    ("Pesarattu", "Crispy Andhra green moong lentil crepe served with allam pachadi.", "115.00", "Andhra Special", "VEG", "Tiffins / Breakfast", "Breakfast Menu", "5.00"),
    ("Upma", "Warm roasted semolina tempered with mustard, curry leaves & cashews.", "75.00", "South Indian", "VEG", "Tiffins / Breakfast", "Breakfast Menu", "5.00"),
    ("Ghee Pongal", "Creamy rice and moong dal comfort bowl tempered with black pepper & ghee.", "95.00", "South Indian", "VEG", "Tiffins / Breakfast", "Breakfast Menu", "5.00"),
    ("Onion Uttapam", "Thick spongy rice pancake topped with diced onions, chillies & coriander.", "120.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00"),
    ("Rava Dosa", "Lacy crisp semolina crepe studded with cumin, pepper & onions.", "125.00", "South Indian", "VEG", "Dosa & Idli", "Breakfast Menu", "5.00"),
    # Meals & Thalis
    ("South Indian Meals", "Traditional banana-leaf vegetarian meals with rice, pappu, sambar, rasam, curries & sweet.", "180.00", "South Indian", "VEG", "Meals / Thali", "Lunch Menu", "5.00"),
    ("Andhra Meals", "Full Andhra vegetarian thali with pappu, gutti vankaya, gongura chutney, podi & ghee.", "210.00", "Andhra Special", "VEG", "Meals / Thali", "Lunch Menu", "5.00"),
    ("North Indian Thali", "Paneer curry, dal makhani, seasonal sabzi, jeera rice, 2 butter naans & gulab jamun.", "260.00", "North Indian", "VEG", "Meals / Thali", "Lunch Menu", "5.00"),
    ("Non-Veg Meals", "Steamed rice paired with Andhra chicken curry, fry piece, rasam & curd.", "290.00", "Andhra Special", "NON_VEG", "Meals / Thali", "Lunch Menu", "5.00"),
    # Starters (Veg / Non-Veg / Egg)
    ("Paneer Tikka", "Char-grilled cottage cheese cubes marinated in yogurt & tandoori spices.", "230.00", "Tandoori", "VEG", "Starters", "Dinner Menu", "5.00"),
    ("Gobi 65", "Crisp battered cauliflower florets tossed with curry leaves & garlic chilli.", "170.00", "South Indian", "VEG", "Starters", "All-Day Menu", "5.00"),
    ("Veg Manchurian", "Crispy vegetable dumplings glazed in tangy soy-ginger garlic sauce.", "160.00", "Indo-Chinese", "VEG", "Starters", "Dinner Menu", "5.00"),
    ("Chicken 65", "Signature spicy South Indian deep-fried boneless chicken tempered with curry leaves.", "220.00", "South Indian", "NON_VEG", "Starters", "Dinner Menu", "5.00"),
    ("Chicken Tikka", "Boneless smoky tandoori chicken morsels served with mint chutney.", "260.00", "Tandoori", "NON_VEG", "Starters", "Dinner Menu", "5.00"),
    ("Apollo Fish Fry", "Tawa-seared spiced coastal fish fillets finished with lemon & green chilli.", "290.00", "Andhra Special", "NON_VEG", "Starters", "Dinner Menu", "5.00"),
    ("Egg Pakoda", "Golden besan-crusted spiced egg fritters served hot with onion rings.", "140.00", "Indian Street Food", "EGG", "Starters", "All-Day Menu", "5.00"),
    # Curries & Gravies + North Indian Breads
    ("Paneer Butter Masala", "Silky tomato-cashew butter gravy simmered with soft paneer cubes.", "240.00", "North Indian", "VEG", "Curries & Gravies", "Dinner Menu", "5.00"),
    ("Dal Tadka", "Slow-cooked yellow toor & moong lentils with roasted cumin garlic tempering.", "150.00", "North Indian", "VEG", "Curries & Gravies", "All-Day Menu", "5.00"),
    ("Chole Masala", "Punjabi spiced Kabuli chickpeas simmered with ginger & amchur.", "165.00", "North Indian", "VEGAN", "Curries & Gravies", "Lunch Menu", "5.00"),
    ("Mixed Veg Curry", "Seasonal vegetables cooked in balanced onion-tomato homestyle gravy.", "175.00", "North Indian", "VEG", "Curries & Gravies", "All-Day Menu", "5.00"),
    ("Andhra Chicken Curry", "Fiery Andhra style bone-in chicken curry with ground whole spices.", "265.00", "Andhra Special", "NON_VEG", "Curries & Gravies", "Dinner Menu", "5.00"),
    ("Mutton Curry", "Slow-braised tender goat meat cooked in rich aromatic spiced gravy.", "360.00", "Telangana Special", "NON_VEG", "Curries & Gravies", "Dinner Menu", "5.00"),
    ("Egg Curry", "Hard-boiled eggs simmered in spiced onion-tomato coastal masala.", "165.00", "Kerala Special", "EGG", "Curries & Gravies", "All-Day Menu", "5.00"),
    ("Butter Naan", "Soft tandoor-baked leavened flatbread brushed with butter.", "55.00", "Tandoori", "VEG", "Breads & Rotis", "Dinner Menu", "5.00"),
    ("Tandoori Roti", "Whole-wheat clay oven flatbread.", "35.00", "Tandoori", "VEGAN", "Breads & Rotis", "Dinner Menu", "5.00"),
    ("Aloo Paratha", "Whole-wheat flatbread stuffed with spiced mashed potato, served with curd.", "85.00", "North Indian", "VEG", "Breads & Rotis", "Breakfast Menu", "5.00"),
    # Rice & Biryani
    ("Veg Biryani", "Fragrant saffron basmati rice layered with vegetables & whole spices.", "195.00", "Telangana Special", "VEG", "Rice & Biryani", "Lunch Menu", "5.00"),
    ("Paneer Biryani", "Hyderabadi dum biryani layered with marinated tandoori paneer.", "235.00", "Telangana Special", "VEG", "Rice & Biryani", "Dinner Menu", "5.00"),
    ("Hyderabadi Chicken Dum Biryani", "Classic kacchi dum basmati rice slow-cooked with spiced chicken & caramelized onions.", "280.00", "Telangana Special", "NON_VEG", "Rice & Biryani", "All-Day Menu", "5.00"),
    ("Mutton Dum Biryani", "Royal Hyderabadi mutton dum biryani served with mirchi ka salan & raita.", "360.00", "Mughlai", "NON_VEG", "Rice & Biryani", "Dinner Menu", "5.00"),
    ("Jeera Rice", "Fragrant basmati rice tempered with cumin seeds and ghee.", "120.00", "North Indian", "VEG", "Rice & Biryani", "All-Day Menu", "5.00"),
    ("Plain Steamed Rice", "Warm steamed sona masoori rice.", "80.00", "South Indian", "VEGAN", "Rice & Biryani", "All-Day Menu", "5.00"),
    # Snacks, Desserts & Beverages
    ("Punjabi Samosa (2 Pcs)", "Crisp flaky pastry filled with spiced potato & green peas, mint chutney.", "65.00", "Indian Street Food", "VEGAN", "Snacks", "All-Day Menu", "5.00"),
    ("Gulab Jamun (2 Pcs)", "Warm caramelized milk dumplings steeped in cardamom rose syrup.", "95.00", "North Indian", "VEG", "Desserts", "All-Day Menu", "5.00"),
    ("Madras Filter Coffee", "Traditional south Indian brass decoction frothy milk coffee.", "60.00", "South Indian", "VEG", "Beverages", "Breakfast Menu", "5.00"),
]


_DISH_IMAGE_RULES: List[Tuple[Tuple[str, ...], str]] = [
    (("biryani combo",), "/images/dishes/biryani-combo.jpg"),
    (("idli",), "/images/dishes/idli.jpg"),
    (("pesarattu",), "/images/dishes/pesarattu-upma.jpg"),
    (("ghee karam dosa", "karam dosa"), "/images/dishes/ghee-karam-dosa.jpg"),
    (("dosa", "uttapam"), "/images/dishes/masala-dosa.jpg"),
    (("medu vada", "vada", "pongal", "upma"), "/images/dishes/idli-vada.jpg"),
    (("gobi 65", "cauliflower"), "/images/dishes/gobi-65.jpg"),
    (("manchurian",), "/images/dishes/veg-manchurian.jpg"),
    (("paneer tikka",), "/images/dishes/paneer-tikka.jpg"),
    (("chicken tikka",), "/images/dishes/chicken-tikka.jpg"),
    (("chicken 65", "apollo fish", "fish fry", "kebab"), "/images/dishes/chicken-65.jpg"),
    (("egg pakoda", "egg bonda", "pakoda", "pakora"), "/images/dishes/egg-pakoda.jpg"),
    (("gutti vankaya",), "/images/dishes/gutti-vankaya.jpg"),
    (("pappu charu", "rasam", "sambar"), "/images/dishes/pappu-charu.jpg"),
    (("baghara baingan", "baingan"), "/images/dishes/baghara-baingan.jpg"),
    (("dal tadka", "dal fry", "dal makhani", "pappu"), "/images/dishes/dal-tadka.jpg"),
    (("chole", "chana"), "/images/dishes/chole-masala.jpg"),
    (("butter chicken",), "/images/dishes/butter-chicken.jpg"),
    (("andhra kodi", "chicken curry", "kodi kura"), "/images/dishes/andhra-chicken-curry.jpg"),
    (("gongura mutton", "mutton", "keema"), "/images/dishes/gongura-mutton.jpg"),
    (("egg curry", "egg roast", "egg masala", "omelette"), "/images/dishes/egg-curry.jpg"),
    (("paneer",), "/images/dishes/paneer-butter-masala.jpg"),
    (("butter naan", "naan", "kulcha"), "/images/dishes/butter-naan.jpg"),
    (("tandoori roti", "roti", "paratha", "chapati", "phulka"), "/images/dishes/tandoori-roti.jpg"),
    (("veg biryani", "vegetable biryani", "paneer biryani", "pulao", "jeera rice", "steamed rice"), "/images/dishes/veg-biryani.jpg"),
    (("biryani", "dum biryani"), "/images/dishes/chicken-biryani.jpg"),
    (("north indian thali", "north thali"), "/images/dishes/north-indian-thali.jpg"),
    (("andhra meals", "south indian meals", "meals", "thali"), "/images/dishes/south-indian-meals.jpg"),
    (("samosa", "chaat", "bhel", "pav bhaji"), "/images/dishes/samosa-snacks.jpg"),
    (("gulab jamun", "double ka meetha", "payasam", "halwa", "kheer"), "/images/dishes/gulab-jamun.jpg"),
    (("filter coffee", "coffee", "chai", "tea", "lassi", "buttermilk"), "/images/dishes/filter-coffee.jpg"),
]

_CATEGORY_IMAGE_FALLBACKS: List[Tuple[Tuple[str, ...], str]] = [
    (("combo",), "/images/dishes/biryani-combo.jpg"),
    (("dosa", "idli", "tiffin", "breakfast"), "/images/dishes/masala-dosa.jpg"),
    (("bread", "roti", "naan"), "/images/dishes/butter-naan.jpg"),
    (("biryani", "rice"), "/images/dishes/chicken-biryani.jpg"),
    (("meal", "thali"), "/images/dishes/south-indian-meals.jpg"),
    (("starter", "kebab", "soup"), "/images/dishes/paneer-tikka.jpg"),
    (("snack", "chaat"), "/images/dishes/samosa-snacks.jpg"),
    (("dessert", "sweet"), "/images/dishes/gulab-jamun.jpg"),
    (("beverage", "drink"), "/images/dishes/filter-coffee.jpg"),
]


def resolve_default_indian_dish_image(dish_name: str, category_name: str = "") -> str:
    """Maps an Indian dish name (with category fallback) to a curated studio dish photo."""
    name_low = (dish_name or "").lower()
    for keywords, photo_path in _DISH_IMAGE_RULES:
        if any(k in name_low for k in keywords):
            return photo_path

    cat_low = (category_name or "").lower()
    for keywords, photo_path in _CATEGORY_IMAGE_FALLBACKS:
        if any(k in cat_low for k in keywords):
            return photo_path

    return "/images/dishes/paneer-butter-masala.jpg"


def apply_indian_menu_template(
    db: Session,
    tenant_id: str,
    branch_id: Optional[str] = None,
    cuisines_filter: Optional[List[str]] = None,
    categories_filter: Optional[List[str]] = None,
    include_sample_dishes: bool = False,
    create_scheduled_menus: bool = True,
) -> Dict[str, int]:
    """
    Idempotently populates dynamic tenant-scoped Cuisines, Dish Categories,
    scheduled Menus (Breakfast / Lunch / Dinner / All-Day), and optional sample dishes.
    """
    # 1. Seed Cuisines
    target_cuisines = (
        [(n, d) for (n, d) in DEFAULT_CUISINES if n in cuisines_filter]
        if cuisines_filter is not None
        else DEFAULT_CUISINES
    )
    cuisine_map: Dict[str, Cuisine] = {
        c.name: c
        for c in db.query(Cuisine).filter(Cuisine.tenant_id == tenant_id).all()
    }
    created_cuisines = 0
    for idx, (cname, desc) in enumerate(target_cuisines):
        if cname not in cuisine_map:
            obj = Cuisine(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=cname,
                description=desc,
                display_order=idx + 1,
                is_active=True,
            )
            db.add(obj)
            db.flush()
            cuisine_map[cname] = obj
            created_cuisines += 1

    # 2. Seed Dish Categories
    target_categories = (
        [c for c in DEFAULT_DISH_CATEGORIES if c in categories_filter]
        if categories_filter is not None
        else DEFAULT_DISH_CATEGORIES
    )
    category_map: Dict[str, MenuCategory] = {
        c.name: c
        for c in db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id).all()
    }
    created_categories = 0
    for idx, cat_name in enumerate(target_categories):
        if cat_name not in category_map:
            cat_obj = MenuCategory(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                name=cat_name,
                display_order=idx + 1,
                is_active=True,
            )
            db.add(cat_obj)
            db.flush()
            category_map[cat_name] = cat_obj
            created_categories += 1

    # 3. Seed Scheduled Menus
    menu_map: Dict[str, Menu] = {
        m.name: m
        for m in db.query(Menu).filter(Menu.tenant_id == tenant_id).all()
    }
    created_menus = 0
    if create_scheduled_menus or include_sample_dishes:
        schedule_specs = [
            ("All-Day Menu", "Available all day across dining & online channels", "AllDay", "07:00", "23:30", 1),
            ("Breakfast Menu", "Morning South Indian tiffins, dosas & filter coffee", "Breakfast", "07:00", "11:30", 2),
            ("Lunch Menu", "Midday thalis, meals & dum biryanis", "Lunch", "11:30", "16:00", 3),
            ("Dinner Menu", "Evening starters, tandoor & signature curries", "Dinner", "18:00", "23:30", 4),
        ]
        for mname, mdesc, sched, t_from, t_to, order in schedule_specs:
            if mname not in menu_map:
                m_obj = Menu(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    name=mname,
                    description=mdesc,
                    schedule_type=sched,
                    available_from=t_from,
                    available_to=t_to,
                    display_order=order,
                    is_active=True,
                )
                db.add(m_obj)
                db.flush()
                menu_map[mname] = m_obj
                created_menus += 1

    # 4. Seed Sample Indian Catalog Items (optional)
    created_items = 0
    if include_sample_dishes:
        existing_items = {
            i.name
            for i in db.query(MenuItem).filter(MenuItem.tenant_id == tenant_id).all()
        }
        for idx, (iname, idesc, iprice, cname, ftype, cat_name, mname, tax) in enumerate(SAMPLE_INDIAN_CATALOG):
            if iname in existing_items:
                continue
            cuisine_obj = cuisine_map.get(cname)
            cat_obj = category_map.get(cat_name)
            if not cat_obj:
                cat_obj = MenuCategory(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    name=cat_name,
                    display_order=len(category_map) + 1,
                    is_active=True,
                )
                db.add(cat_obj)
                db.flush()
                category_map[cat_name] = cat_obj
            menu_obj = menu_map.get(mname)
            item = MenuItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                branch_id=branch_id,
                menu_id=menu_obj.id if menu_obj else None,
                cuisine_id=cuisine_obj.id if cuisine_obj else None,
                category_id=cat_obj.id,
                name=iname,
                description=idesc,
                image_url=resolve_default_indian_dish_image(iname, cat_name),
                base_price=Decimal(iprice),
                cost_price=Decimal(iprice) * Decimal("0.35"),
                tax_rate=Decimal(tax),
                preparation_time=15,
                display_order=idx + 1,
                is_available=True,
                show_on_customer_site=True,
                food_type=ftype,
                is_veg=ftype in ("VEG", "VEGAN"),
                order_channels=["DineIn", "Takeaway", "Delivery", "QR"],
                spice_levels=["Mild", "Medium", "Spicy"] if ftype in ("VEG", "NON_VEG") else [],
            )
            db.add(item)
            created_items += 1

    db.commit()
    return {
        "created_cuisines": created_cuisines,
        "created_categories": created_categories,
        "created_menus": created_menus,
        "created_items": created_items,
    }
