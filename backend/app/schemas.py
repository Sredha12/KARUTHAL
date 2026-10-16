from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, computed_field


class ErrorResponse(BaseModel):
    message: str


class ReportCreate(BaseModel):
    district: str = Field(min_length=2, max_length=100)
    panchayat: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    is_urgent: bool = Field(default=False)


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


class ReportCreatedResponse(BaseModel):
    message: str
    report: dict
