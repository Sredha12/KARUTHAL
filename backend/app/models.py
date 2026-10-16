from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    officer_code = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="dcpu_officer", nullable=False)  # dcpu_officer, field_officer, admin
    district = Column(String(100), index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    reports_solved = relationship("Report", back_populates="solver", foreign_keys="Report.solved_by")
    calls_recorded = relationship("EmergencyCall", back_populates="recorder", foreign_keys="EmergencyCall.recorded_by")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(32), unique=True, index=True, nullable=False)  # KAR-XXXXXXXX
    district = Column(String(100), index=True, nullable=False)
    panchayat = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), index=True, default="Submitted", nullable=False)
    is_urgent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    solved_at = Column(DateTime(timezone=True), nullable=True)
    solved_by = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)

    solver = relationship("Officer", back_populates="reports_solved", foreign_keys=[solved_by])


class EmergencyCall(Base):
    __tablename__ = "emergency_calls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_ref = Column(String(50), unique=True, index=True, nullable=False)
    district = Column(String(100), index=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(500), default="", nullable=False)
    related_report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), index=True, default="Active", nullable=False)  # Active, Acknowledged, Resolved
    notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    recorded_by = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)

    recorder = relationship("Officer", back_populates="calls_recorded", foreign_keys=[recorded_by])


class CaseHistory(Base):
    __tablename__ = "case_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # "report", "emergency_call"
    entity_id = Column(Integer, index=True, nullable=False)
    action = Column(String(100), nullable=False)
    actor_officer_id = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Compound indexes for fast district and status querying
Index("ix_reports_district_status", Report.district, Report.status)
Index("ix_calls_district_status", EmergencyCall.district, EmergencyCall.status)
