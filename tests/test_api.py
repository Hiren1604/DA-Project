"""
Integration tests for CreditLens FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_api_metadata():
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert data["source"]["source_name"] == "Reserve Bank of India (RBI)"
    assert data["reporting_bounds"]["total_months"] == 90


def test_api_summary_latest():
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["reporting_month"] == "2026-06"
    assert data["total_credit_cr"] > 4000000
    assert data["hhi_index"] > 1000
    assert data["largest_sector"] == "Infrastructure"


def test_api_sectors():
    response = client.get("/api/sectors")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 43

    resp_l1 = client.get("/api/sectors?level=sector_total")
    assert resp_l1.status_code == 200
    assert resp_l1.json()["count"] == 19


def test_api_credit_trends():
    response = client.get("/api/credit/trends?sector_code=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 90


def test_api_credit_comparison():
    response = client.get("/api/credit/comparison")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 19
    top1 = data["comparison"][0]
    assert top1["sector_name"] == "Infrastructure"


def test_api_data_quality():
    response = client.get("/api/data-quality")
    assert response.status_code == 200
    data = response.json()
    assert "validation_checks" in data
