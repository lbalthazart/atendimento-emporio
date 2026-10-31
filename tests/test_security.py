import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.security import create_access_token, decode_access_token, check_rate_limit
from src.config import settings

client = TestClient(app)

def test_jwt_generation_and_decoding():
    token = create_access_token(data={"sub": "client_123"})
    assert isinstance(token, str)
    
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "client_123"

def test_security_policies_endpoint():
    resp = client.get("/api/security/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lgpd_compliance"] is True
    assert data["data_retention_ttl_days"] == 7
    assert data["right_to_be_forgotten"] is True

def test_issue_token_endpoint():
    resp = client.post("/api/auth/token", json={"client_id": "bot_whatsapp_01"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_security_headers_present():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

def test_search_products_sorting():
    from src.database.queries import search_products
    # Ascending
    cheap = search_products(sort_by="price_asc", limit=3)
    assert cheap[0]["price_brl"] <= cheap[1]["price_brl"]
    
    # Descending (most expensive)
    expensive = search_products(sort_by="price_desc", limit=3)
    assert expensive[0]["price_brl"] >= expensive[1]["price_brl"]
    # Top item should be >= 18000 (Nord Synth or Gibson Les Paul)
    assert expensive[0]["price_brl"] > 10000
