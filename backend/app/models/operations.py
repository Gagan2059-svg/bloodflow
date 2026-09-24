"""
Missing domain models: Transfers, Alerts, Recommendations, Audit Logs, Forecasts, Demand.
"""
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
import uuid

from app.models.base import BaseModel


# ─── Transfers ────────────────────────────────────────────────────────────────

class TransferStatus(str, enum.Enum):
    PENDING   = "PENDING"
    APPROVED  = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED  = "REJECTED"


class Transfer(BaseModel):
    __tablename__ = "transfers"

    organization_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    source_facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), index=True)
    dest_facility_id:   Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), index=True)
    blood_group:        Mapped[str]        = mapped_column(String(8))
    component:          Mapped[str]        = mapped_column(String(32))
    quantity:           Mapped[int]        = mapped_column(Integer)
    status:             Mapped[TransferStatus] = mapped_column(SQLEnum(TransferStatus), default=TransferStatus.PENDING, index=True)
    transport_time_min: Mapped[int]        = mapped_column(Integer, nullable=True)
    notes:              Mapped[str]        = mapped_column(Text, nullable=True)
    initiated_by:       Mapped[uuid.UUID]  = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by:        Mapped[uuid.UUID]  = mapped_column(ForeignKey("users.id"), nullable=True)
    completed_at:       Mapped[datetime]   = mapped_column(DateTime, nullable=True)


# ─── Alerts ───────────────────────────────────────────────────────────────────

class AlertSeverity(str, enum.Enum):
    INFO     = "INFO"
    WARNING  = "WARNING"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    OPEN         = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED     = "RESOLVED"


class Alert(BaseModel):
    __tablename__ = "alerts"

    organization_id: Mapped[uuid.UUID]     = mapped_column(ForeignKey("organizations.id"), index=True)
    facility_id:     Mapped[uuid.UUID]     = mapped_column(ForeignKey("facilities.id"), nullable=True, index=True)
    alert_type:      Mapped[str]           = mapped_column(String(64), index=True)
    severity:        Mapped[AlertSeverity] = mapped_column(SQLEnum(AlertSeverity), index=True)
    title:           Mapped[str]           = mapped_column(String(256))
    description:     Mapped[str]           = mapped_column(Text)
    status:          Mapped[AlertStatus]   = mapped_column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, index=True)
    blood_group:     Mapped[str]           = mapped_column(String(8), nullable=True)
    component:       Mapped[str]           = mapped_column(String(32), nullable=True)
    acknowledged_by: Mapped[uuid.UUID]     = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime]      = mapped_column(DateTime, nullable=True)
    resolved_at:     Mapped[datetime]      = mapped_column(DateTime, nullable=True)
    metadata_json:   Mapped[dict]          = mapped_column(JSON, nullable=True)


# ─── Recommendations ──────────────────────────────────────────────────────────

class RecommendationType(str, enum.Enum):
    TRANSFER     = "TRANSFER"
    REPOSITION   = "REPOSITION"
    RESERVE      = "RESERVE"
    INVESTIGATE  = "INVESTIGATE"
    ALERT        = "ALERT"


class RecommendationStatus(str, enum.Enum):
    PENDING  = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED  = "EXPIRED"
    EXECUTED = "EXECUTED"


class Recommendation(BaseModel):
    __tablename__ = "recommendations"

    organization_id:      Mapped[uuid.UUID]            = mapped_column(ForeignKey("organizations.id"), index=True)
    rec_type:             Mapped[RecommendationType]   = mapped_column(SQLEnum(RecommendationType), index=True)
    priority:             Mapped[int]                  = mapped_column(Integer, default=2)  # 1=critical, 3=low
    source_facility_id:   Mapped[uuid.UUID]            = mapped_column(ForeignKey("facilities.id"), nullable=True)
    dest_facility_id:     Mapped[uuid.UUID]            = mapped_column(ForeignKey("facilities.id"), nullable=True)
    blood_group:          Mapped[str]                  = mapped_column(String(8), nullable=True)
    component:            Mapped[str]                  = mapped_column(String(32), nullable=True)
    quantity:             Mapped[int]                  = mapped_column(Integer, nullable=True)
    reason:               Mapped[str]                  = mapped_column(Text)
    evidence:             Mapped[dict]                 = mapped_column(JSON, nullable=True)
    confidence:           Mapped[float]                = mapped_column(Float, nullable=True)
    expected_impact_json: Mapped[dict]                 = mapped_column(JSON, nullable=True)
    status:               Mapped[RecommendationStatus] = mapped_column(SQLEnum(RecommendationStatus), default=RecommendationStatus.PENDING, index=True)
    expires_at:           Mapped[datetime]             = mapped_column(DateTime, nullable=True)
    reviewed_by:          Mapped[uuid.UUID]            = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at:          Mapped[datetime]             = mapped_column(DateTime, nullable=True)


# ─── Audit Logs ───────────────────────────────────────────────────────────────

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id:         Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action:          Mapped[str]       = mapped_column(String(128), index=True)
    entity_type:     Mapped[str]       = mapped_column(String(64), nullable=True)
    entity_id:       Mapped[str]       = mapped_column(String(64), nullable=True)
    description:     Mapped[str]       = mapped_column(Text, nullable=True)
    metadata_json:   Mapped[dict]      = mapped_column(JSON, nullable=True)
    ip_address:      Mapped[str]       = mapped_column(String(64), nullable=True)


# ─── Forecasts ────────────────────────────────────────────────────────────────

class Forecast(BaseModel):
    __tablename__ = "forecasts"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    facility_id:     Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), index=True)
    blood_group:     Mapped[str]       = mapped_column(String(8), index=True)
    component:       Mapped[str]       = mapped_column(String(32), index=True)
    horizon_days:    Mapped[int]       = mapped_column(Integer)
    model_name:      Mapped[str]       = mapped_column(String(64))
    model_version:   Mapped[str]       = mapped_column(String(32))
    predictions:     Mapped[dict]      = mapped_column(JSON)   # list of {date, value, ci_lower, ci_upper}
    mae:             Mapped[float]     = mapped_column(Float, nullable=True)
    rmse:            Mapped[float]     = mapped_column(Float, nullable=True)
    mape:            Mapped[float]     = mapped_column(Float, nullable=True)
    is_stale:        Mapped[bool]      = mapped_column(Boolean, default=False)
    generated_at:    Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)


# ─── Demand Records ───────────────────────────────────────────────────────────

class DemandRecord(BaseModel):
    __tablename__ = "demand_records"

    organization_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    facility_id:        Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), index=True)
    blood_group:        Mapped[str]       = mapped_column(String(8), index=True)
    component:          Mapped[str]       = mapped_column(String(32), index=True)
    requested_quantity: Mapped[int]       = mapped_column(Integer)
    fulfilled_quantity: Mapped[int]       = mapped_column(Integer, default=0)
    is_emergency:       Mapped[bool]      = mapped_column(Boolean, default=False)
    demand_source:      Mapped[str]       = mapped_column(String(64), nullable=True)
    recorded_at:        Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow, index=True)


# ─── Model Registry ───────────────────────────────────────────────────────────

class ModelRegistry(BaseModel):
    """Tracks trained ML model artifacts and their evaluation metrics."""
    __tablename__ = "model_registry"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    facility_id:     Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), nullable=True, index=True)
    name:            Mapped[str]       = mapped_column(String(128), index=True)  # e.g. "gradient_boosting"
    version:         Mapped[str]       = mapped_column(String(32))               # e.g. "1.0.0"
    blood_group:     Mapped[str]       = mapped_column(String(8), nullable=True)
    component:       Mapped[str]       = mapped_column(String(32), nullable=True)
    artifact_path:   Mapped[str]       = mapped_column(String(512))              # local path to .joblib file
    training_points: Mapped[int]       = mapped_column(Integer, default=0)
    mae:             Mapped[float]     = mapped_column(Float, nullable=True)
    rmse:            Mapped[float]     = mapped_column(Float, nullable=True)
    mape:            Mapped[float]     = mapped_column(Float, nullable=True)
    is_active:       Mapped[bool]      = mapped_column(Boolean, default=True)
    trained_at:      Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)

