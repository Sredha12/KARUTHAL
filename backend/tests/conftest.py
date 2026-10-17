import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required test env vars before importing application code
os.environ["JWT_SECRET"] = "pytest_test_secret_key_at_least_32_chars_long_12345"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENFORCE_DISTRICT_SCOPE"] = "true"
os.environ["DEMO_OFFICER_PASSWORD"] = "DemoTestPass123"

from app.database import Base, get_db
from app.init_db import init_locations
from app.models import Officer, Report, Assignment, FieldVisit, Referral, EmergencyCall, CaseHistory
from app.security import hash_password, create_access_token

# Isolated in-memory test database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as session:
        init_locations(session)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def demo_dcpu_tvm(db_session):
    """Fixture providing a DCPU officer for Thiruvananthapuram."""
    officer = Officer(
        officer_code="DCPU-TVM-01",
        email="dcpu.tvm@karuthal.demo",
        name="Anjali Nair",
        password_hash=hash_password("DemoTestPass123"),
        role="dcpu_officer",
        district="Thiruvananthapuram",
        is_active=True,
    )
    db_session.add(officer)
    db_session.commit()
    db_session.refresh(officer)
    return officer


@pytest.fixture
def dcpu_tvm_token(demo_dcpu_tvm):
    return create_access_token({
        "id": demo_dcpu_tvm.id,
        "officer_code": demo_dcpu_tvm.officer_code,
        "email": demo_dcpu_tvm.email,
        "name": demo_dcpu_tvm.name,
        "role": demo_dcpu_tvm.role,
        "district": demo_dcpu_tvm.district,
    })


@pytest.fixture
def dcpu_tvm_headers(dcpu_tvm_token):
    return {"Authorization": f"Bearer {dcpu_tvm_token}"}


@pytest.fixture
def demo_field_tvm(db_session):
    """Fixture providing a Field Officer for Thiruvananthapuram."""
    officer = Officer(
        officer_code="FO-TVM-01",
        email="fo.tvm@karuthal.demo",
        name="Rahul Varma",
        password_hash=hash_password("DemoTestPass123"),
        role="field_officer",
        district="Thiruvananthapuram",
        is_active=True,
    )
    db_session.add(officer)
    db_session.commit()
    db_session.refresh(officer)
    return officer


@pytest.fixture
def field_tvm_token(demo_field_tvm):
    return create_access_token({
        "id": demo_field_tvm.id,
        "officer_code": demo_field_tvm.officer_code,
        "email": demo_field_tvm.email,
        "name": demo_field_tvm.name,
        "role": demo_field_tvm.role,
        "district": demo_field_tvm.district,
    })


@pytest.fixture
def field_tvm_headers(field_tvm_token):
    return {"Authorization": f"Bearer {field_tvm_token}"}


@pytest.fixture
def demo_dcpu_kollam(db_session):
    """Fixture providing a DCPU officer for Kollam."""
    officer = Officer(
        officer_code="DCPU-KLM-01",
        email="dcpu.klm@karuthal.demo",
        name="Suresh Kumar",
        password_hash=hash_password("DemoTestPass123"),
        role="dcpu_officer",
        district="Kollam",
        is_active=True,
    )
    db_session.add(officer)
    db_session.commit()
    db_session.refresh(officer)
    return officer


@pytest.fixture
def dcpu_klm_token(demo_dcpu_kollam):
    return create_access_token({
        "id": demo_dcpu_kollam.id,
        "officer_code": demo_dcpu_kollam.officer_code,
        "email": demo_dcpu_kollam.email,
        "name": demo_dcpu_kollam.name,
        "role": demo_dcpu_kollam.role,
        "district": demo_dcpu_kollam.district,
    })


@pytest.fixture
def dcpu_klm_headers(dcpu_klm_token):
    return {"Authorization": f"Bearer {dcpu_klm_token}"}
