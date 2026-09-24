import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "CREATE_TRANSFER", "APPROVE_EMERGENCY"
    entity_type = Column(String(100), nullable=False) # e.g., "Transfer", "Facility"
    entity_id = Column(String(255), nullable=True) # UUID of the entity acted upon
    metadata_info = Column(JSONB, nullable=True) # JSON containing diffs or additional context
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
