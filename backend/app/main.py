from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import time

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.schema_sync import ensure_schema_columns
from app.api.v1.api import api_router
import app.models  # Ensure all models are registered with Base

# Create tables if not present and apply non-destructive column additions
Base.metadata.create_all(bind=engine)
ensure_schema_columns(engine)

# Auto-seed Vercel /tmp demo SQLite database if empty on cold start
if os.getenv("VERCEL") or settings.DATABASE_URL.startswith("sqlite:////tmp"):
    try:
        from app.models.saas import Tenant
        db = SessionLocal()
        try:
            has_tenant = db.query(Tenant).first() is not None
        finally:
            db.close()
        if not has_tenant:
            from seed_data import seed_database, upgrade_existing_menu_data
            seed_database()
            upgrade_existing_menu_data()
    except Exception as exc:
        print(f"Auto-seed warning: {exc}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Tenant Restaurant CRM / ERP SaaS Backend with Row-Level Security",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Mount v1 router and uploaded dish assets
app.include_router(api_router, prefix=settings.API_V1_STR)

uploads_dir = (
    "/tmp/uploads"
    if os.getenv("VERCEL")
    else os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
)
os.makedirs(os.path.join(uploads_dir, "dishes"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "connected",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_STR}/docs",
    }
