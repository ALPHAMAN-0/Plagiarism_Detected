"""
Health endpoint — RED test.

User journey:
  As a load balancer / k8s probe, I want GET /healthz to return
  {"status":"ok"} so I can confirm the service is up.

Acceptance criteria:
  1. GET /healthz returns 200.
  2. Body equals {"status":"ok"}.
  3. GET /readyz returns 200 once the app is initialised.
  4. /readyz body is JSON with a "ready" boolean.
"""

from __future__ import annotations


def test_healthz_returns_ok(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ready_flag(client) -> None:
    response = client.get("/readyz")
    assert response.status_code in (200, 503), response.text
    body = response.json()
    assert "ready" in body
    assert isinstance(body["ready"], bool)
