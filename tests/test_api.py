import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Isolated in-memory SQLite database using StaticPool to maintain state across test sessions
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_and_health_endpoints(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_shorten_url_auto_generated(client):
    payload = {"original_url": "https://fastapi.tiangolo.com/tutorial/"}
    response = client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == payload["original_url"]
    assert "short_code" in data
    assert len(data["short_code"]) >= 6
    assert data["click_count"] == 0
    assert data["is_active"] is True


def test_shorten_url_custom_alias(client):
    payload = {
        "original_url": "https://github.com/piyush1008-cyber",
        "custom_code": "my-portfolio"
    }
    response = client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "my-portfolio"


def test_shorten_url_duplicate_custom_alias(client):
    payload = {
        "original_url": "https://example.com/first",
        "custom_code": "duplicate-code"
    }
    res1 = client.post("/api/v1/shorten", json=payload)
    assert res1.status_code == 201

    # Second creation with identical alias must return 409 Conflict
    res2 = client.post("/api/v1/shorten", json=payload)
    assert res2.status_code == 409
    assert "already in use" in res2.json()["detail"]


def test_shorten_url_invalid_scheme(client):
    payload = {"original_url": "ftp://not-a-web-url.com"}
    response = client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 422


def test_redirection_and_analytics_tracking(client):
    # 1. Shorten
    target_url = "https://news.ycombinator.com"
    shorten_res = client.post(
        "/api/v1/shorten",
        json={"original_url": target_url, "custom_code": "hn-link"}
    )
    assert shorten_res.status_code == 201

    # 2. Redirect
    redirect_res = client.get(
        "/hn-link",
        headers={"referer": "https://google.com", "user-agent": "pytest-agent"},
        follow_redirects=False
    )
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == target_url

    # 3. Analytics
    analytics_res = client.get("/api/v1/analytics/hn-link")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_clicks"] == 1
    assert "https://google.com" in analytics_data["top_referrers"]


def test_redirect_not_found(client):
    response = client.get("/non-existent-code", follow_redirects=False)
    assert response.status_code == 404


def test_deactivate_link(client):
    payload = {"original_url": "https://python.org", "custom_code": "python-docs"}
    client.post("/api/v1/shorten", json=payload)

    # Deactivate
    del_res = client.delete("/api/v1/links/python-docs")
    assert del_res.status_code == 200

    # Ensure redirect returns 404 after deactivation
    red_res = client.get("/python-docs", follow_redirects=False)
    assert red_res.status_code == 404
