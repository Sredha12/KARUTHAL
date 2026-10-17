from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, computed_field


class ErrorResponse(BaseModel):
    message: str


# --- Location Schemas ---

class DistrictRead(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class PanchayatRead(BaseModel):
    id: int
    district_id: int
    name: str
    is_sample: bool

    model_config = ConfigDict(from_attributes=True)


# --- Public Report Schemas ---

class ReportCreate(BaseModel):
    district: str = Field(min_length=2, max_length=100)
    panchayat: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    is_urgent: bool = Field(default=False)

    # Stage 11: Optional Reporter Location Fields
    location_text: str | None = Field(default=None, max_length=200)
    ward: str | None = Field(default=None, max_length=50)
    approx_lat: float | None = None
    approx_lng: float | None = None
    location_consent: bool = Field(default=False)
    location_source: str | None = Field(default=None, max_length=20)  # typed, device, map_pick


class ReportRead(BaseModel):
    id: int
    case_id: str
    report_id: str
    district: str
    panchayat: str
    category: str
    description: str
    status: str
    is_urgent: bool
    created_at: datetime
    updated_at: datetime
    solved_at: datetime | None = None
    routed_district: str | None = None
    has_location: bool = False

    # Dual compatibility fields for UI flexibility
    @computed_field
    @property
    def abuse_type(self) -> str:
        return self.category

    @computed_field
    @property
    def location(self) -> str:
        return self.panchayat

    model_config = ConfigDict(from_attributes=True)


class PublicReportRead(BaseModel):
    case_id: str
    report_id: str
    district: str
    status: str
    created_at: datetime
    privacy_notice: str = "Public view restricted to status verification only. No personal details are stored or disclosed."


class ReportCreatedResponse(BaseModel):
    message: str
    report: dict
    reporter_token: str | None = None


# --- Stage 11: Case Location & GeoJSON Schemas ---

class CaseLocationResponse(BaseModel):
    case_id: str
    district: str
    panchayat: str
    ward: str | None = None
    location_text: str | None = None
    approx_lat: float | None = None
    approx_lng: float | None = None
    location_consent: bool
    location_source: str | None = None
    routed_district: str
    simulated: bool = True
    notice: str = "SIMULATED PROTOTYPE. Coordinates are rounded to ~1km for privacy."


class GeoJsonPointGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude]


class GeoJsonFeatureProperties(BaseModel):
    report_id: str
    status: str
    is_urgent: bool
    panchayat: str


class GeoJsonFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJsonPointGeometry
    properties: GeoJsonFeatureProperties


class GeoJsonFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJsonFeature]


# --- Auth Schemas ---

class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=255)


class LoginResponse(BaseModel):
    token: str
    name: str
    district: str


class OfficerProfile(BaseModel):
    id: int
    officer_code: str
    email: str
    name: str
    role: str
    district: str

    model_config = ConfigDict(from_attributes=True)


# --- Case Workflow Schemas ---

class CaseStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=50)


class CaseAssignRequest(BaseModel):
    field_officer_id: int
    notes: str = Field(default="", max_length=1000)


class AssignmentRead(BaseModel):
    id: int
    report_id: int
    assigned_to_id: int
    assigned_to_name: str
    assigned_by_id: int
    assigned_by_name: str
    notes: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Field Visit Schemas ---

class FieldVisitCreate(BaseModel):
    visit_at: datetime
    outcome: str = Field(min_length=2, max_length=100)
    notes: str = Field(default="", max_length=2000)


class FieldVisitRead(BaseModel):
    id: int
    report_id: int
    field_officer_id: int
    field_officer_name: str
    visit_at: datetime
    outcome: str
    notes: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Referral Schemas ---

class ReferralCreate(BaseModel):
    urgency: str = Field(default="Standard", max_length=50)
    concern_category: str = Field(default="General Care", max_length=100)
    next_action: str = Field(default="", max_length=255)
    follow_up_due: datetime | None = None
    service: str = Field(default="Child Welfare Committee (CWC)", max_length=100)
    notes: str = Field(default="", max_length=500)


class ReferralUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    urgency: str | None = Field(default=None, max_length=50)
    next_action: str | None = Field(default=None, max_length=255)
    follow_up_due: datetime | None = None
    service: str | None = Field(default=None, max_length=100)
    service_state: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=500)


class ReferralServiceLinkage(BaseModel):
    service: str
    state: str


class ReferralHistoryItem(BaseModel):
    at: str
    role: str
    event: str


class ReferralDcpuView(BaseModel):
    id: int
    caseRef: str
    district: str
    concernCategory: str
    receivedAt: str
    urgency: str
    status: str
    nextAction: str
    followUpDue: str | None
    serviceLinkage: ReferralServiceLinkage
    history: list[ReferralHistoryItem]


class ReferralMutationResponse(BaseModel):
    referral: dict
    confirmed: bool = False
    disclaimer: str = "Prototype record only. Creating or updating this referral does NOT contact external agencies or services."


# --- Emergency Call Schemas ---

class EmergencyCallCreate(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    district: str = Field(min_length=2, max_length=100)
    related_case_id: str | None = None


class EmergencyCallPatch(BaseModel):
    status: str = Field(min_length=2, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)


class EmergencyCallRead(BaseModel):
    id: int
    call_id: str
    call_ref: str
    district: str
    category: str
    description: str
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime
    related_report_id: int | None = None
    disclaimer: str = "Prototype record only. Recording an emergency event does NOT contact police, DCPU, 112, 1098, or emergency services."

    model_config = ConfigDict(from_attributes=True)


# --- Case History Schemas ---

class CaseHistoryRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    details: str
    actor_officer_id: int | None = None
    actor_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Dashboard Schemas ---

class OfficerDashboardResponse(BaseModel):
    total: int
    solved: int
    pending: int
    urgent: int
    reports: list[dict]
    calls: list[dict]


class DcpuOverview(BaseModel):
    newReferrals: int
    pendingReview: int
    urgentCases: int
    followUpDue: int


class DcpuDashboardResponse(BaseModel):
    overview: DcpuOverview
    referrals: list[dict]


# --- AI Summary Schemas ---

class TimelineEvent(BaseModel):
    timestamp: str
    event: str


class RelatedCaseHint(BaseModel):
    category: str
    district: str
    similar_cases_count: int
    note: str


class AiSummaryResponse(BaseModel):
    ai_generated: bool = True
    verified: bool = False
    human_review_required: bool = True
    disclaimer: str = (
        "AI-assisted prototype summary for authorized human decision-making only. "
        "Reported details are unverified allegations. This system does NOT determine abuse, "
        "guilt, or risk, and CANNOT automatically close, reject, or escalate cases."
    )
    case_id: str
    structured_summary: str
    missing_information: list[str]
    tentative_timeline: list[TimelineEvent]
    related_case_hints: list[RelatedCaseHint]


# --- Stage 12: VoIP Call Session Schemas ---

class OfficerStartCallRequest(BaseModel):
    override_solved: bool = Field(default=False, description="Explicit officer override to call on a resolved case")


class CallSessionRead(BaseModel):
    id: int
    case_id: int
    report_id: str
    requested_by: str
    officer_id: int | None = None
    officer_name: str | None = None
    status: str
    created_at: datetime
    ringing_at: datetime | None = None
    connected_at: datetime | None = None
    ended_at: datetime | None = None
    end_reason: str | None = None
    duration_seconds: int | None = None
    mode: str
    simulated: bool = True
    notice: str = "Simulated prototype call. No real helpline or authority is contacted."

    model_config = ConfigDict(from_attributes=True)


class WsTicketResponse(BaseModel):
    ticket: str
    expires_in: int = 60
    simulated: bool = True


class IceConfigResponse(BaseModel):
    ice_servers: list[dict]
    mode: str
    simulated: bool = True
