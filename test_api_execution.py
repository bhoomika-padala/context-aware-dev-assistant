import asyncio
from fastapi.testclient import TestClient
from main import app

def test_backend_execution():
    client = TestClient(app)
    response = client.post("/api/execute", json={"task": "Verify mock setup"})
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    data = response.json()
    assert data["status"] == "success"
    assert "summary_report" in data
    assert "execution_trace" in data
    print("\n[SUCCESS] Backend API returned status 200 and valid JSON schema.")

if __name__ == "__main__":
    test_backend_execution()
