from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_columns(engine: Engine) -> None:
    """
    Idempotently adds newly introduced columns when running against an existing
    local SQLite or PostgreSQL database without wiping previously seeded records.
    """
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
        ("menu_items", "show_on_customer_site", "BOOLEAN DEFAULT 1 NOT NULL"),
        ("menu_items", "food_type", "VARCHAR(20) DEFAULT 'VEG' NOT NULL"),
        ("menu_items", "order_channels", "TEXT"),
        ("menu_items", "spice_levels", "TEXT"),
        ("menu_items", "is_combo", "BOOLEAN DEFAULT 0 NOT NULL"),
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
                    "UPDATE menu_items SET food_type = 'NON_VEG' "
                    "WHERE is_veg = 0 AND (food_type IS NULL OR food_type = 'VEG')"
                )
            )
