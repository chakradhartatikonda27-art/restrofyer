from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_columns(engine: Engine) -> None:
    """
    Idempotently adds newly introduced columns when running against an existing
    local SQLite or PostgreSQL database without wiping previously seeded records.
    """
    is_pg = engine.dialect.name == "postgresql"
    bool_true = "TRUE" if is_pg else "1"
    bool_false = "FALSE" if is_pg else "0"

    migrations = [
        ("menus", "branch_id", "VARCHAR(36)"),
        ("menus", "display_order", "INTEGER DEFAULT 0"),
        ("menus", "schedule_type", "VARCHAR(40) DEFAULT 'AllDay' NOT NULL"),
        ("menus", "available_from", "VARCHAR(10)"),
        ("menus", "available_to", "VARCHAR(10)"),
        ("menus", "active_days", "TEXT"),
        ("menu_categories", "branch_id", "VARCHAR(36)"),
        ("menu_categories", "parent_id", "VARCHAR(36)"),
        ("menu_items", "menu_id", "VARCHAR(36)"),
        ("menu_items", "branch_id", "VARCHAR(36)"),
        ("menu_items", "cuisine_id", "VARCHAR(36)"),
        ("menu_items", "display_order", "INTEGER DEFAULT 0"),
        ("menu_items", "show_on_customer_site", f"BOOLEAN DEFAULT {bool_true} NOT NULL"),
        ("menu_items", "food_type", "VARCHAR(20) DEFAULT 'VEG' NOT NULL"),
        ("menu_items", "order_channels", "TEXT"),
        ("menu_items", "spice_levels", "TEXT"),
        ("menu_items", "is_combo", f"BOOLEAN DEFAULT {bool_false} NOT NULL"),
        ("restaurant_tables", "assigned_menu_id", "VARCHAR(36)"),
    ]

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table_name, col_name, col_def in migrations:
            if table_name not in existing_tables:
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"))

        # Backfill non-veg rows to food_type='NON_VEG' when legacy items exist
        if "menu_items" in existing_tables:
            conn.execute(
                text(
                    f"UPDATE menu_items SET food_type = 'NON_VEG' "
                    f"WHERE is_veg = {bool_false} AND (food_type IS NULL OR food_type = 'VEG')"
                )
            )
