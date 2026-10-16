
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="Karuthal API",
    description="Child-protection support prototype",
    version="0.2.0",
)


# Temporary storage for testing only.
# Reports will be lost when the server restarts.
demo_reports = {}


class ReportCreate(BaseModel):
    district: str = Field(min_length=2, max_length=100)
    panchayat: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=2000)


@app.get("/")
def home():
    return {
        "project": "Karuthal",
        "message": "Backend is running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/reports", status_code=201)
def create_report(report: ReportCreate):
    case_id = f"KAR-{uuid4().hex[:8].upper()}"

    new_report = {
        "case_id": case_id,
        "district": report.district,
        "panchayat": report.panchayat,
        "category": report.category,
        "description": report.description,
        "status": "Submitted",
    }

    demo_reports[case_id] = new_report

    return {
        "message": "Demo report submitted successfully",
        "report": new_report,
    }


@app.get("/api/reports")
def list_reports():
    return {
        "count": len(demo_reports),
        "reports": list(demo_reports.values()),
    }


@app.get("/api/reports/{case_id}")
def get_report(case_id: str):
    report = demo_reports.get(case_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report
