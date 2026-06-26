from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
import uuid

client = TestClient(app)


def test_register_and_login_and_customer_lifecycle():
    init_db()
    
    # Use unique username and customer ID
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    customer_id = f"C{uuid.uuid4().hex[:4].upper()}"  # "C" + 4 hex chars = 5 chars total
    # Register a user
    response = client.post("/api/auth/register", json={"username": username, "password": "secret", "role": "loan_officer"})
    print(f"Register response: {response.status_code}")
    print(f"Register body: {response.text}")
    assert response.status_code == 200, f"Register failed: {response.text}"
    data = response.json()
    assert data["username"] == username

    # Login
    response = client.post("/api/auth/login", data={"username": username, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # Create customer
    response = client.post(
        "/api/customers/",
        json={
            "customer_id": customer_id,
            "full_name": "Jane Doe",
            "date_of_birth": "1990-01-01",
            "pan": "ABCDE1234F",
            "aadhaar": "123412341234",
            "salary": 100000.00,
            "address": "123 Main St",
        },
        headers=headers,
    )
    print(f"Create customer response: {response.status_code}")
    print(f"Create customer body: {response.text}")
    assert response.status_code == 200, f"Create customer failed: {response.text}"
    cust_data = response.json()
    assert cust_data["customer_id"] == customer_id

    # Lookup customer
    response = client.get(f"/api/customers/lookup/{customer_id}", headers=headers)
    print(f"Lookup customer response: {response.status_code}")
    print(f"Lookup customer body: {response.text}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Doe"

    # Create application
    response = client.post("/api/applications/", params={"customer_id": customer_id}, headers=headers)
    print(f"Create application response: {response.status_code}")
    print(f"Create application body: {response.text}")
    assert response.status_code == 200
    app_id = response.json()["application_id"]

    # Score application
    response = client.post(f"/api/applications/{app_id}/score", headers=headers)
    print(f"Score application response: {response.status_code}")
    print(f"Score application body: {response.text}")
    assert response.status_code == 200
    score_data = response.json()
    assert score_data["decision"] in {"approved", "review", "rejected"}

    # Retrieve application
    response = client.get(f"/api/applications/{app_id}", headers=headers)
    print(f"Get application response: {response.status_code}")
    print(f"Get application body: {response.text}")
    assert response.status_code == 200
    app_data = response.json()
    assert app_data["risk_score"] == score_data["risk_score"]
    assert len(app_data["audits"]) >= 2

    # List fraud flags for the application
    response = client.get(f"/api/fraud/flags/?application_id={app_id}", headers=headers)
    print(f"List fraud flags response: {response.status_code}")
    print(f"List fraud flags body: {response.text}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    if response.json():
        flag_id = response.json()[0]["id"]
        response = client.get(f"/api/fraud/flags/{flag_id}", headers=headers)
        assert response.status_code == 200


if __name__ == "__main__":
    test_register_and_login_and_customer_lifecycle()
    print("OK")
