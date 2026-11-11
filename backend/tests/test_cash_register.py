import pytest
from decimal import Decimal
import uuid

from app.models.financial import CashRegister, CashRegisterSession

def test_cash_register_shift_lifecycle_and_variance(client, db, seed_two_tenants):
    tenant_a = seed_two_tenants["tenant_a"]
    branch_a = seed_two_tenants["branch_a"]
    token_a = seed_two_tenants["token_a"]

    headers = {"Authorization": f"Bearer {token_a}", "X-Branch-Id": branch_a.id}

    # 1. Setup Cash Register
    reg = CashRegister(
        id=str(uuid.uuid4()),
        tenant_id=tenant_a.id,
        branch_id=branch_a.id,
        name="Front Counter Register",
        status="Closed"
    )
    db.add(reg)
    db.commit()

    # 2. Open Register Session with Opening Float of 1,000.00
    open_payload = {
        "register_id": reg.id,
        "opening_float": 1000.00
    }
    res_open = client.post("/api/v1/cash-registers/open", json=open_payload, headers=headers)
    assert res_open.status_code == 200
    session_data = res_open.json()
    session_id = session_data["id"]
    assert session_data["status"] == "Open"
    assert session_data["opening_float"] == 1000.00
    assert session_data["expected_closing_cash"] == 1000.00

    # 3. Add CASH_IN (e.g. manager added petty change of 300.00)
    tx_in = client.post(
        f"/api/v1/cash-registers/sessions/{session_id}/transactions",
        json={"transaction_type": "CASH_IN", "amount": 300.00, "reason": "Additional change float"},
        headers=headers
    )
    assert tx_in.status_code == 200

    # 4. Add CASH_OUT (e.g. payout for ice delivery of 150.00)
    tx_out = client.post(
        f"/api/v1/cash-registers/sessions/{session_id}/transactions",
        json={"transaction_type": "CASH_OUT", "amount": 150.00, "reason": "Ice block purchase payout"},
        headers=headers
    )
    assert tx_out.status_code == 200

    # Expected at this point:
    # Opening: 1000 + Cash In: 300 - Cash Out: 150 = 1150.00
    res_active = client.get("/api/v1/cash-registers/active-session", headers=headers)
    assert res_active.status_code == 200
    assert res_active.json()["expected_closing_cash"] == 1150.00

    # 5. Close Register Session with Actual Cash counted = 1140.00 (Variance = -10.00)
    close_payload = {
        "actual_closing_cash": 1140.00,
        "notes": "Shortage of 10 units"
    }
    res_close = client.post(f"/api/v1/cash-registers/sessions/{session_id}/close", json=close_payload, headers=headers)
    assert res_close.status_code == 200
    closed_data = res_close.json()
    assert closed_data["status"] == "Closed"
    assert closed_data["expected_closing_cash"] == 1150.00
    assert closed_data["actual_closing_cash"] == 1140.00
    assert closed_data["variance"] == -10.00 # Formula: Actual - Expected
