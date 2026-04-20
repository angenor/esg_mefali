"""Tests des endpoints REST du router maturity (Story 10.3 AC3, AC8)."""

from __future__ import annotations

import pytest

_ENDPOINTS = [
    ("post", "/api/maturity/declare", {"level": "informel"}),
    ("get", "/api/maturity/formalization-plan", None),
    ("get", "/api/maturity/levels", None),
]


async def _call(client, method: str, url: str, body: dict | None):
    if method == "get":
        return await client.get(url)
    return await client.post(url, json=body)


@pytest.mark.asyncio
async def test_endpoints_return_501_authenticated(authenticated_client):
    """Test 8 — 3 endpoints authentifies -> 501 + message contient 'Epic 12'."""
    for method, url, body in _ENDPOINTS:
        response = await _call(authenticated_client, method, url, body)
        assert response.status_code == 501, (
            f"{method.upper()} {url} -> attendu 501, obtenu {response.status_code}"
        )
        detail = response.json().get("detail", "")
        assert "Epic 12" in detail, (
            f"{method.upper()} {url} -> detail attendu avec 'Epic 12', obtenu : {detail}"
        )


@pytest.mark.asyncio
async def test_endpoints_return_401_without_auth(client):
    """Test 9 — sans JWT -> 401 prime sur 501 (AC3 §ordre 401 -> 501)."""
    for method, url, body in _ENDPOINTS:
        response = await _call(client, method, url, body)
        assert response.status_code == 401, (
            f"{method.upper()} {url} -> attendu 401, obtenu {response.status_code}"
        )


@pytest.mark.asyncio
async def test_openapi_documents_501_responses(client):
    """Test 10 — /openapi.json documente 501 pour chaque endpoint /api/maturity/*."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()

    paths = spec.get("paths", {})
    maturity_paths = {
        p: ops for p, ops in paths.items() if p.startswith("/api/maturity")
    }
    assert maturity_paths, "aucun chemin /api/maturity documente dans OpenAPI"

    for path, ops in maturity_paths.items():
        for method, operation in ops.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = operation.get("responses", {})
            assert "501" in responses, (
                f"{method.upper()} {path} : statut 501 absent de OpenAPI"
            )
