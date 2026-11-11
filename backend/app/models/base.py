import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_mixin, declared_attr
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

@declarative_mixin
class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

@declarative_mixin
class BranchMixin:
    @declared_attr
    def branch_id(cls):
        return Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
