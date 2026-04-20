"""Tests des endpoints REST du router projects (Story 10.2 AC3, AC8)."""

from __future__ import annotations

import uuid

import pytest

_ENDPOINTS = [
    ("post", "/api/projects", {"name": "X", "company_id": str(uuid.uuid4())}),
    ("get", f"/api/projects/{uuid.uuid4()}", None),
    ("get", "/api/projects", None),
    (
        "post",
        f"/api/projects/{uuid.uuid4()}/memberships",
        {"company_id": str(uuid.uuid4()), "role": "porteur_principal"},
    ),
]


async def _call(client, method: str, url: str, body: dict | None):
    if method == "get":
        return await client.get(url)
    return await client.post(url, json=body)


@pytest.mark.asyncio
async def test_endpoints_return_404_when_flag_disabled(
    authenticated_client, monkeypatch
):
    """Test 6 — ENABLE_PROJECT_MODEL=false -> 404 sur les 4 endpoints."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "false")

    for method, url, body in _ENDPOINTS:
        response = await _call(authenticated_client, method, url, body)
        assert response.status_code == 404, (
            f"{method.upper()} {url} -> attendu 404, obtenu {response.status_code}"
        )
        detail = response.json().get("detail", "")
        assert "ENABLE_PROJECT_MODEL" in detail


@pytest.mark.asyncio
async def test_endpoints_return_501_when_flag_enabled(
    authenticated_client, monkeypatch
):
    """Test 7 — ENABLE_PROJECT_MODEL=true -> 501 squelette Epic 11."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")

    for method, url, body in _ENDPOINTS:
        response = await _call(authenticated_client, method, url, body)
        assert response.status_code == 501, (
            f"{method.upper()} {url} -> attendu 501, obtenu {response.status_code}"
        )
        assert "Epic 11" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_endpoints_return_401_without_auth(client, monkeypatch):
    """Test 8 — sans JWT -> 401 prime sur 404/501 (AC3 §ordre 401->404->501)."""
    # Flag ON pour ne pas masquer derrière 404 : on doit voir 401.
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")

    for method, url, body in _ENDPOINTS:
        response = await _call(client, method, url, body)
        assert response.status_code == 401, (
            f"{method.upper()} {url} -> attendu 401, obtenu {response.status_code}"
        )


@pytest.mark.asyncio
async def test_openapi_documents_404_and_501_responses(client):
    """Test 9 — /openapi.json documente 404 ET 501 pour /api/projects/*."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()

    paths = spec.get("paths", {})
    projects_paths = {p: ops for p, ops in paths.items() if p.startswith("/api/projects")}
    assert projects_paths, "aucun chemin /api/projects documenté dans OpenAPI"

    for path, ops in projects_paths.items():
        for method, operation in ops.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = operation.get("responses", {})
            assert "404" in responses, (
                f"{method.upper()} {path} : statut 404 absent de OpenAPI"
            )
            assert "501" in responses, (
                f"{method.upper()} {path} : statut 501 absent de OpenAPI"
            )
