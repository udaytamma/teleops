"""ORM models for TeleOps."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_tenant_id", "tenant_id"),
        Index("ix_alerts_timestamp", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_system: Mapped[str] = mapped_column(String(64))
    host: Mapped[str] = mapped_column(String(128))
    service: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(16))
    alert_type: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    tags: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid4()))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24))
    related_alert_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    suspected_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_scope: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="system")
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RCAArtifact(Base):
    __tablename__ = "rca_artifacts"
    __table_args__ = (
        Index("ix_rca_incident_id", "incident_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(String(128), ForeignKey("incidents.id"))
    hypotheses: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence_scores: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    llm_model: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_ms: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(String(24), nullable=True, default="pending_review")
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
