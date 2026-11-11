from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine
import contextvars
from app.core.config import settings

# Thread/async safe context variable for the active tenant ID
current_tenant_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("current_tenant_id", default="")
is_super_admin_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar("is_super_admin", default=False)

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

# SQLite Foreign Key Support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    tenant_id = current_tenant_id_ctx.get()
    is_admin = is_super_admin_ctx.get()
    
    # If using PostgreSQL, inject the tenant context into the local database session
    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            if tenant_id:
                db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": tenant_id})
            if is_admin:
                db.execute(text("SET LOCAL app.is_super_admin = 'true'"))
            else:
                db.execute(text("SET LOCAL app.is_super_admin = 'false'"))
        except Exception:
            pass

    try:
        yield db
    finally:
        db.close()
