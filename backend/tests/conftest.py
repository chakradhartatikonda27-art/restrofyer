import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from decimal import Decimal

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.saas import PlatformUser, Tenant, SubscriptionPlan, Subscription
from app.models.organization import Branch, User
from app.models.menu import MenuCategory, MenuItem
from app.models.table import DiningArea, RestaurantTable
from app.models.inventory import InventoryItem, Recipe, RecipeItem
from app.models.crm import Customer, LoyaltyAccount
from app.models.financial import CashRegister
from app.main import app

# In-memory test SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seed_two_tenants(db):
    # Setup Tenant A
    tenant_a = Tenant(
        id=str(uuid.uuid4()),
        name="Tenant A Restaurant",
        slug="tenant-a",
        contact_email="owner@tenanta.com",
        status="Active"
    )
    branch_a = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        name="Branch A1",
        code="A-01",
        address="100 Alpha St",
        tax_rate=Decimal("5.00"),
        is_active=True
    )
    user_a = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        email="owner@tenanta.com",
        password_hash=get_password_hash("PasswordA1!"),
        full_name="Owner A",
        role="TENANT_OWNER",
        branch_id=branch_a.id,
        is_active=True
    )

    # Setup Tenant B
    tenant_b = Tenant(
        id=str(uuid.uuid4()),
        name="Tenant B Restaurant",
        slug="tenant-b",
        contact_email="owner@tenantb.com",
        status="Active"
    )
    branch_b = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant_b.id,
        name="Branch B1",
        code="B-01",
        address="200 Beta St",
        tax_rate=Decimal("5.00"),
        is_active=True
    )
    user_b = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_b.id,
        email="owner@tenantb.com",
        password_hash=get_password_hash("PasswordB1!"),
        full_name="Owner B",
        role="TENANT_OWNER",
        branch_id=branch_b.id,
        is_active=True
    )

    db.add_all([tenant_a, branch_a, user_a, tenant_b, branch_b, user_b])
    db.commit()

    token_a = create_access_token(subject=user_a.id, tenant_id=tenant_a.id, role=user_a.role, branch_id=branch_a.id)
    token_b = create_access_token(subject=user_b.id, tenant_id=tenant_b.id, role=user_b.role, branch_id=branch_b.id)

    return {
        "tenant_a": tenant_a,
        "branch_a": branch_a,
        "user_a": user_a,
        "token_a": token_a,
        "tenant_b": tenant_b,
        "branch_b": branch_b,
        "user_b": user_b,
        "token_b": token_b
    }
