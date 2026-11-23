from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
res1 = client.post("/api/v1/manual-entry/drafts", json={
    "plant_code": "PLANT-MUMBAI-01",
    "recipe_code": "M40_VW_UT_ISOLATED",
    "production_date": "2026-08-09",
    "shift": "DAY"
})
print("POST /drafts status:", res1.status_code)
d_id = res1.json()["draft_id"]
print("Draft ID:", d_id)

res2 = client.get(f"/api/v1/manual-entry/drafts/{d_id}/final-review")
print("GET /final-review status:", res2.status_code)
if res2.status_code != 200:
    print(res2.text)

res3 = client.post(f"/api/v1/manual-entry/drafts/{d_id}/submit")
print("POST /submit status:", res3.status_code)
if res3.status_code != 200:
    print(res3.text)
