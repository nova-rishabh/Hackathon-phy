import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ROLLWATCH_DATA", str(ROOT / "artifacts"))
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_webhook_secret_key"

from fastapi.testclient import TestClient
from api.main import app

def test_billing_flow():
    client = TestClient(app)

    # 1. Subscribe
    resp = client.post("/billing/subscribe", json={"plan": {"constituencies": 3, "whatsapp": True}, "org": "The Hindu"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    sub_id = data["subscription_id"]
    print("Subscribed successfully:", sub_id)

    # 2. Webhook simulation (signed HMAC-SHA256)
    payload = {
        "event": "subscription.activated",
        "id": "evt_test_123",
        "payload": {
            "subscription": {
                "entity": {
                    "id": sub_id,
                    "status": "active",
                    "current_start": time.time(),
                    "current_end": time.time() + 30 * 86400,
                    "paid_count": 1,
                }
            }
        },
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = hmac.new(b"test_webhook_secret_key", raw, hashlib.sha256).hexdigest()

    wh_resp = client.post(
        "/billing/webhook",
        json=payload,
        headers={"X-Razorpay-Signature": sig},
    )
    assert wh_resp.status_code == 200, wh_resp.text
    print("Signed webhook verified and recorded:", wh_resp.json())

    # 3. Check status & quotas
    sub_resp = client.get(f"/billing/subscriptions/{sub_id}")
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["subscription"]["status"] == "active"
    assert sub_data["quotas"]["whatsapp_enabled"] is True
    assert sub_data["quotas"]["constituencies_allowed"] == 3
    print("Subscription active with custom quotas:", sub_data["quotas"]["tier"])

    # 4. Check events audit list
    ev_resp = client.get("/billing/events")
    assert ev_resp.status_code == 200
    print("Persisted webhook events count:", len(ev_resp.json()["events"]))

    # 5. Cancel subscription
    cancel_resp = client.post(f"/billing/subscriptions/{sub_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Quota reverts
    q_resp = client.get(f"/billing/subscriptions/{sub_id}/quotas")
    assert q_resp.status_code == 200
    assert q_resp.json()["tier"] == "free"
    print("Cancelled subscription cleanly reverted to free tier")

    print("\n>>> ALL RAZORPAY WEBHOOK & LIFECYCLE CHECKS PASSED! <<<")


if __name__ == "__main__":
    test_billing_flow()
