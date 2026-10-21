from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)

    panchayats = relationship("Panchayat", back_populates="district_rel", cascade="all, delete-orphan")


class Panchayat(Base):
    __tablename__ = "panchayats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_sample = Column(Boolean, default=True, nullable=False)  # Explicitly marks demo/fictional records

    district_rel = relationship("District", back_populates="panchayats")

    __table_args__ = (
        Index("ix_panchayats_district_name", "district_id", "name"),
    )


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
    assignments_received = relationship("Assignment", back_populates="assigned_to", foreign_keys="Assignment.assigned_to_id")
    assignments_created = relationship("Assignment", back_populates="assigned_by", foreign_keys="Assignment.assigned_by_id")
    field_visits = relationship("FieldVisit", back_populates="officer")
    call_sessions = relationship("CallSession", back_populates="officer")


class Report(Base):
    """
    Represents child-protection reports and cases.
    A case IS a row in reports; no redundant case table is created.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(32), unique=True, index=True, nullable=False)  # KAR-XXXXXXXX
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=True, index=True)
    panchayat_id = Column(Integer, ForeignKey("panchayats.id", ondelete="SET NULL"), nullable=True, index=True)
    district = Column(String(100), index=True, nullable=False)
    panchayat = Column(String(100), nullable=True, default="")
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), index=True, default="Submitted", nullable=False)
    is_urgent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    solved_at = Column(DateTime(timezone=True), nullable=True)
    solved_by = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)

    # Stage 11 Location routing additions
    location_text = Column(String(200), nullable=True)
    ward = Column(String(50), nullable=True)
    approx_lat = Column(Float, nullable=True)
    approx_lng = Column(Float, nullable=True)
    location_consent = Column(Boolean, default=False, nullable=False)
    location_source = Column(String(20), nullable=True)  # typed, device, map_pick
    routed_district = Column(String(100), index=True, nullable=True)

    # Stage 12 Reporter token hash (never stored in plain text)
    reporter_token_hash = Column(String(255), nullable=True)

    solver = relationship("Officer", back_populates="reports_solved", foreign_keys=[solved_by])
    assignments = relationship("Assignment", back_populates="report", cascade="all, delete-orphan")
    field_visits = relationship("FieldVisit", back_populates="report", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="report", cascade="all, delete-orphan")
    emergency_calls = relationship("EmergencyCall", back_populates="report")
    history = relationship("CaseHistory", back_populates="report", cascade="all, delete-orphan")
    call_sessions = relationship("CallSession", back_populates="report", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey("officers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("officers.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, default="", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("Report", back_populates="assignments")
    assigned_to = relationship("Officer", back_populates="assignments_received", foreign_keys=[assigned_to_id])
    assigned_by = relationship("Officer", back_populates="assignments_created", foreign_keys=[assigned_by_id])


class FieldVisit(Base):
    __tablename__ = "field_visits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    field_officer_id = Column(Integer, ForeignKey("officers.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_at = Column(DateTime(timezone=True), nullable=False)
    outcome = Column(String(100), nullable=False)
    notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("Report", back_populates="field_visits")
    officer = relationship("Officer", back_populates="field_visits")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    district = Column(String(100), index=True, nullable=False)
    concern_category = Column(String(100), nullable=False)
    urgency = Column(String(50), default="Standard", nullable=False)
    status = Column(String(50), index=True, default="New", nullable=False)  # New, Pending review, Under review, Follow-up due, Closed
    next_action = Column(String(255), default="", nullable=False)
    follow_up_due = Column(DateTime(timezone=True), nullable=True)
    service = Column(String(100), default="Child Welfare Committee (CWC)", nullable=False)
    service_state = Column(String(50), default="Referred", nullable=False)  # Draft, Referred, Engaged, Completed
    notes = Column(Text, default="", nullable=False)
    created_by_id = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    report = relationship("Report", back_populates="referrals")


class EmergencyCall(Base):
    __tablename__ = "emergency_calls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_ref = Column(String(50), unique=True, index=True, nullable=False)  # CALL-XXXXXXXX
    district = Column(String(100), index=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(500), default="", nullable=False)
    related_report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), index=True, default="Active", nullable=False)  # Active, Acknowledged, Resolved
    notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    recorded_by = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)

    recorder = relationship("Officer", back_populates="calls_recorded", foreign_keys=[recorded_by])
    report = relationship("Report", back_populates="emergency_calls", foreign_keys=[related_report_id])


class CaseHistory(Base):
    __tablename__ = "case_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # "report", "case", "emergency_call", "referral", "call_session"
    entity_id = Column(Integer, index=True, nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(String(255), default="", nullable=False)
    actor_officer_id = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("Report", back_populates="history", foreign_keys=[report_id])


class CallSession(Base):
    """
    Represents an in-app voice call session between a case officer and an anonymous reporter.
    No audio, transcripts, or telephone numbers are ever recorded or stored.
    """
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String(20), nullable=False)  # "reporter" | "officer"
    officer_id = Column(Integer, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="requested", nullable=False, index=True)
    # Status lifecycle: requested -> ringing -> connected -> ended; exits: declined, missed, cancelled
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ringing_at = Column(DateTime(timezone=True), nullable=True)
    connected_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    end_reason = Column(String(50), nullable=True)  # "normal", "declined", "ring_timeout", "cancelled"
    duration_seconds = Column(Integer, nullable=True)
    mode = Column(String(20), default="simulated", nullable=False)  # "simulated" | "webrtc"
    simulated = Column(Boolean, default=True, nullable=False)

    report = relationship("Report", back_populates="call_sessions")
    officer = relationship("Officer", back_populates="call_sessions")


# Compound indexes for fast district and status querying
Index("ix_reports_district_status", Report.district, Report.status)
Index("ix_calls_district_status", EmergencyCall.district, EmergencyCall.status)
Index("ix_call_sessions_case_status", CallSession.case_id, CallSession.status)
