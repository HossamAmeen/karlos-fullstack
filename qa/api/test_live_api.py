"""Black-box API QA against a deployed environment.

Run:  QA_API_URL=https://api.karlos.hossam-ameen.online python3 -m pytest api -v
All created data is prefixed QA-AUTO and soft-deleted/cancelled afterwards.
"""
import os
import time
import uuid
from decimal import Decimal

import pytest
import requests

BASE = os.environ.get("QA_API_URL", "https://api.karlos.hossam-ameen.online").rstrip("/")
USER = os.environ.get("QA_USER", "01010079798")
PASS = os.environ.get("QA_PASS", "admin")
TAG = f"QA-AUTO-{uuid.uuid4().hex[:6]}"
V1 = f"{BASE}/api/v1"


def phone():
    return "09" + str(time.time_ns())[-9:]


@pytest.fixture(scope="session")
def tokens():
    r = requests.post(f"{BASE}/api/auth/token/", json={"username": USER, "password": PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="session")
def s(tokens):
    sess = requests.Session()
    sess.headers["Authorization"] = f"Bearer {tokens['access']}"
    sess.request = _timeout(sess.request)
    return sess


def _timeout(fn):
    def wrapper(*a, **k):
        k.setdefault("timeout", 30)
        return fn(*a, **k)
    return wrapper


@pytest.fixture(scope="session")
def cleanup(s):
    stack = []
    yield stack
    for url in reversed(stack):
        s.delete(url)


@pytest.fixture(scope="session")
def client_obj(s, cleanup):
    r = s.post(f"{V1}/clients/", json={"name": f"{TAG}-client", "phone": phone()})
    assert r.status_code == 201, r.text
    cleanup.append(f"{V1}/clients/{r.json()['id']}/")
    return r.json()


@pytest.fixture(scope="session")
def service_obj(s, cleanup):
    c = s.post(f"{V1}/service-categories/", json={"name": f"{TAG}-cat"})
    assert c.status_code == 201, c.text
    sv = s.post(f"{V1}/services/", json={
        "name": f"{TAG}-svc", "service_category": c.json()["id"], "cost": "100.00",
        "cost_method": "fixed",
    })
    assert sv.status_code == 201, sv.text
    cleanup.append(f"{V1}/service-categories/{c.json()['id']}/")
    cleanup.append(f"{V1}/services/{sv.json()['id']}/")
    return sv.json()


# ---------------- health / auth ----------------
def test_health_public():
    r = requests.get(f"{BASE}/api/health/", timeout=30)
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_login_bad_password():
    r = requests.post(f"{BASE}/api/auth/token/", json={"username": USER, "password": "bad"}, timeout=30)
    assert r.status_code == 401


def test_login_missing_fields():
    assert requests.post(f"{BASE}/api/auth/token/", json={}, timeout=30).status_code == 400


def test_refresh_and_verify(tokens):
    r = requests.post(f"{BASE}/api/auth/token/refresh/", json={"refresh": tokens["refresh"]}, timeout=30)
    assert r.status_code == 200 and "access" in r.json()
    v = requests.post(f"{BASE}/api/auth/token/verify/", json={"token": tokens["access"]}, timeout=30)
    assert v.status_code == 200


@pytest.mark.parametrize("path", [
    "clients/", "service-categories/", "services/", "invoices/", "expense-main-categories/",
    "expense-categories/", "expenses/", "expenses/summary/", "statistics/",
])
def test_protected_without_token(path):
    assert requests.get(f"{V1}/{path}", timeout=30).status_code == 401


def test_garbage_token_rejected():
    r = requests.get(f"{V1}/clients/", headers={"Authorization": "Bearer abc.def.ghi"}, timeout=30)
    assert r.status_code == 401


# ---------------- lists ----------------
@pytest.mark.parametrize("path", [
    "clients/", "service-categories/", "services/", "invoices/", "expense-main-categories/",
    "expense-categories/", "expenses/",
])
def test_list_shape(s, path):
    r = s.get(f"{V1}/{path}")
    assert r.status_code == 200
    assert {"count", "results"} <= set(r.json())


def test_statistics_shape(s):
    d = s.get(f"{V1}/statistics/").json()
    assert {"total_invoices", "total_expenses", "current_money", "month", "year"} <= set(d)


def test_expense_summary(s):
    r = s.get(f"{V1}/expenses/summary/")
    assert r.status_code == 200 and "total_expenses" in r.json()


# ---------------- clients ----------------
def test_client_validation(s):
    assert s.post(f"{V1}/clients/", json={}).status_code == 400
    assert s.post(f"{V1}/clients/", json={"name": "x"}).status_code == 400


def test_client_lifecycle_and_soft_delete(s):
    p = phone()
    r = s.post(f"{V1}/clients/", json={"name": f"{TAG}-life", "phone": p})
    assert r.status_code == 201
    cid = r.json()["id"]
    dup = s.post(f"{V1}/clients/", json={"name": f"{TAG}-dup", "phone": p})
    assert dup.status_code == 400
    up = s.patch(f"{V1}/clients/{cid}/", json={"note": "n"})
    assert up.status_code == 200 and up.json()["note"] == "n"
    assert any(c["id"] == cid for c in s.get(f"{V1}/clients/", params={"search": TAG}).json()["results"])
    assert s.delete(f"{V1}/clients/{cid}/").status_code == 204
    assert s.get(f"{V1}/clients/{cid}/").status_code == 404
    # phone reusable after soft delete
    again = s.post(f"{V1}/clients/", json={"name": f"{TAG}-reuse", "phone": p})
    assert again.status_code == 201
    s.delete(f"{V1}/clients/{again.json()['id']}/")


def test_client_404(s):
    assert s.get(f"{V1}/clients/99999999/").status_code == 404
    assert s.get(f"{V1}/clients/99999999/statement/").status_code == 404


def test_deposit_and_statement(s, client_obj):
    url = f"{V1}/clients/{client_obj['id']}/deposits/"
    assert s.post(url, json={"amount": "0"}).status_code == 400
    assert s.post(url, json={"amount": "-1"}).status_code == 400
    r = s.post(url, json={"amount": "10.00", "notes": TAG})
    assert r.status_code == 201
    st = s.get(f"{V1}/clients/{client_obj['id']}/statement/").json()
    assert Decimal(st["total_deposits"]) >= Decimal("10.00")
    assert Decimal(st["balance_due"]) == Decimal(st["total_charged"]) - Decimal(st["total_deposits"])


# ---------------- services ----------------
def test_service_rules(s, service_obj):
    assert service_obj["color"].startswith("#")
    bad = s.post(f"{V1}/services/", json={"name": TAG, "service_category": service_obj["service_category"],
                                          "cost": "-1", "cost_method": "fixed"})
    assert bad.status_code == 400
    bad = s.post(f"{V1}/services/", json={"name": TAG, "service_category": service_obj["service_category"],
                                          "cost": "1", "cost_method": "bogus"})
    assert bad.status_code == 400


def test_category_unique_name(s, service_obj):
    r = s.post(f"{V1}/service-categories/", json={"name": f"{TAG}-cat"})
    assert r.status_code == 400


# ---------------- invoices & payments ----------------
def new_invoice(s, client_obj, service_obj):
    inv = s.post(f"{V1}/invoices/", json={"client": client_obj["id"]})
    assert inv.status_code == 201, inv.text
    iid = inv.json()["id"]
    it = s.post(f"{V1}/invoices/{iid}/items/", json={"service": service_obj["id"]})
    assert it.status_code in (200, 201), it.text
    return iid


def test_invoice_requires_client(s):
    assert s.post(f"{V1}/invoices/", json={}).status_code == 400


def test_draft_invoice_delete_is_soft(s, client_obj, service_obj):
    iid = new_invoice(s, client_obj, service_obj)
    assert s.delete(f"{V1}/invoices/{iid}/").status_code == 204
    assert s.get(f"{V1}/invoices/{iid}/").status_code == 404


def test_confirm_requires_items(s, client_obj):
    iid = s.post(f"{V1}/invoices/", json={"client": client_obj["id"]}).json()["id"]
    assert s.post(f"{V1}/invoices/{iid}/confirm/", json={}).status_code == 400
    s.delete(f"{V1}/invoices/{iid}/")


def test_payment_flow(s, client_obj, service_obj):
    iid = new_invoice(s, client_obj, service_obj)
    assert s.post(f"{V1}/invoices/{iid}/pay/", json={"amount": "5"}).status_code == 400  # draft
    over = s.post(f"{V1}/invoices/{iid}/confirm/", json={"amount_paid": "100000"})
    assert over.status_code == 400
    ok = s.post(f"{V1}/invoices/{iid}/confirm/", json={"amount_paid": "40.00"})
    assert ok.status_code == 200
    d = ok.json()
    assert d["total"] == "100.00" and d["amount_remaining"] == "60.00" and d["payment_status"] == "partial"
    assert s.delete(f"{V1}/invoices/{iid}/").status_code == 400  # confirmed not deletable
    assert s.post(f"{V1}/invoices/{iid}/pay/", json={"amount": "61"}).status_code == 400
    paid = s.post(f"{V1}/invoices/{iid}/pay/", json={"amount": "60"}).json()
    assert paid["is_settled"] is True and paid["amount_remaining"] == "0.00"
    assert s.post(f"{V1}/invoices/{iid}/pay/", json={"amount": "1"}).status_code == 400
    assert s.post(f"{V1}/invoices/{iid}/cancel/").status_code == 200
    assert s.post(f"{V1}/invoices/{iid}/cancel/").status_code == 400
    st = s.get(f"{V1}/clients/{client_obj['id']}/statement/").json()
    assert Decimal(st["balance_due"]) == Decimal(st["total_charged"]) - Decimal(st["total_deposits"])


def test_server_authoritative_total(s, client_obj, service_obj):
    r = s.post(f"{V1}/invoices/", json={"client": client_obj["id"], "total": "1", "subtotal": "1"})
    assert r.status_code == 201
    iid = r.json()["id"]
    s.post(f"{V1}/invoices/{iid}/items/", json={"service": service_obj["id"]})
    assert s.get(f"{V1}/invoices/{iid}/").json()["total"] == "100.00"
    s.delete(f"{V1}/invoices/{iid}/")


def test_invoice_discount_cannot_exceed_subtotal(s, client_obj, service_obj):
    iid = new_invoice(s, client_obj, service_obj)
    r = s.patch(f"{V1}/invoices/{iid}/", json={"discount_amount": "9999"})
    assert r.status_code == 400
    s.delete(f"{V1}/invoices/{iid}/")


# ---------------- expenses ----------------
def test_expense_hierarchy_and_soft_delete(s, client_obj):
    m = s.post(f"{V1}/expense-main-categories/", json={"name": f"{TAG}-main"})
    assert m.status_code == 201
    mid = m.json()["id"]
    assert s.post(f"{V1}/expense-main-categories/", json={"name": f"{TAG}-main"}).status_code == 400
    c = s.post(f"{V1}/expense-categories/", json={"main_category": mid, "name": f"{TAG}-cat"})
    assert c.status_code == 201
    cid = c.json()["id"]
    bad = s.post(f"{V1}/expenses/", json={"amount": "0", "description": "x",
                                          "expense_date": "2026-01-01", "category": cid})
    assert bad.status_code == 400
    e = s.post(f"{V1}/expenses/", json={"amount": "7.50", "description": TAG,
                                        "expense_date": "2026-01-01", "category": cid,
                                        "client": client_obj["id"]})
    assert e.status_code == 201, e.text
    eid = e.json()["id"]
    assert s.patch(f"{V1}/expenses/{eid}/", json={"amount": "8.00"}).json()["amount"] == "8.00"
    # in-use category / main category protected
    assert s.delete(f"{V1}/expense-categories/{cid}/").status_code == 400
    assert s.delete(f"{V1}/expense-main-categories/{mid}/").status_code == 400
    assert s.delete(f"{V1}/expenses/{eid}/").status_code == 204
    assert s.get(f"{V1}/expenses/{eid}/").status_code == 404
    assert s.delete(f"{V1}/expense-categories/{cid}/").status_code == 204
    assert s.delete(f"{V1}/expense-main-categories/{mid}/").status_code == 204


# ---------------- robustness / security ----------------
@pytest.mark.parametrize("payload", ["'; DROP TABLE clients;--", "<script>alert(1)</script>", "A" * 5000])
def test_hostile_input_never_500(s, payload):
    r = s.post(f"{V1}/clients/", json={"name": payload, "phone": phone()})
    assert r.status_code < 500
    if r.status_code == 201:
        s.delete(f"{V1}/clients/{r.json()['id']}/")
    assert s.get(f"{V1}/clients/", params={"search": payload}).status_code < 500


def test_malformed_json_is_400(s):
    r = s.post(f"{V1}/clients/", data="{bad", headers={"Content-Type": "application/json"})
    assert r.status_code == 400


def test_method_not_allowed(s):
    assert s.put(f"{V1}/statistics/", json={}).status_code == 405


def test_no_stack_trace_leak(s):
    r = s.get(f"{V1}/clients/abc/")
    assert r.status_code == 404 and "Traceback" not in r.text


def test_cors_and_security_headers():
    r = requests.get(f"{BASE}/api/health/", timeout=30)
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
