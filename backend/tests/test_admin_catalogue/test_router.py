"""Tests des endpoints REST du router admin_catalogue (Story 10.4 AC3, AC8)."""

from __future__ import annotations

import uuid

import pytest

_GET_ENDPOINTS = [
    ("get", "/api/admin/catalogue/fact-types", None),
]

_POST_ENDPOINTS = [
    (
        "post",
        "/api/admin/catalogue/criteria",
        {"code": "c1", "label_fr": "C1", "dimension": "E"},
    ),
    (
        "post",
        "/api/admin/catalogue/referentials",
        {"code": "r1", "label_fr": "R1"},
    ),
    (
        "post",
        "/api/admin/catalogue/packs",
        {"code": "p1", "label_fr": "P1"},
    ),
    (
        "post",
        "/api/admin/catalogue/rules",
        {
            "criterion_id": str(uuid.uuid4()),
            "rule_type": "threshold",
            "rule_json": {},
        },
    ),
]

_ALL_ENDPOINTS = _GET_ENDPOINTS + _POST_ENDPOINTS


async def _call(client, method: str, url: str, body: dict | None):
    if method == "get":
        return await client.get(url)
    return await client.post(url, json=body)


@pytest.mark.asyncio
async def test_endpoints_return_401_without_auth(client):
    """Test 8 — sans JWT -> 5 endpoints renvoient 401 (get_current_user prime)."""
    for method, url, body in _ALL_ENDPOINTS:
        response = await _call(client, method, url, body)
        assert response.status_code == 401, (
            f"{method.upper()} {url} -> attendu 401, obtenu {response.status_code}"
        )


@pytest.mark.asyncio
async def test_endpoints_return_403_for_non_admin_user(
    monkeypatch, authenticated_client
):
    """Test 9 — user PME non-whiteliste -> 403 avec detail 'admin_mefali' + 'Epic 18'."""
    # S'assurer que l'email du mock user n'est pas dans la whitelist.
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "")

    for method, url, body in _ALL_ENDPOINTS:
        response = await _call(authenticated_client, method, url, body)
        assert response.status_code == 403, (
            f"{method.upper()} {url} -> attendu 403, obtenu {response.status_code}"
        )
        detail = response.json().get("detail", "")
        assert "admin_mefali" in detail, (
            f"{method.upper()} {url} -> detail attendu avec 'admin_mefali', obtenu : {detail}"
        )
        assert "Epic 18" in detail, (
            f"{method.upper()} {url} -> detail attendu avec 'Epic 18', obtenu : {detail}"
        )


@pytest.mark.asyncio
async def test_post_endpoints_return_501_for_admin_user(admin_authenticated_client):
    """Test 10 — admin whiteliste -> 4 POST renvoient 501 ; GET fact-types -> 200."""
    for method, url, body in _POST_ENDPOINTS:
        response = await _call(admin_authenticated_client, method, url, body)
        assert response.status_code == 501, (
            f"{method.upper()} {url} -> attendu 501, obtenu {response.status_code}"
        )
        detail = response.json().get("detail", "")
        assert "Epic 13" in detail, (
            f"{method.upper()} {url} -> detail attendu avec 'Epic 13', obtenu : {detail}"
        )

    response = await admin_authenticated_client.get("/api/admin/catalogue/fact-types")
    assert response.status_code == 200
    payload = response.json()
    assert "fact_types" in payload
    fact_types = payload["fact_types"]
    assert isinstance(fact_types, list)
    assert len(fact_types) >= 12
    assert "energy_consumption_kwh" in fact_types


@pytest.mark.asyncio
async def test_openapi_documents_403_and_501_responses(client):
    """Test 11 — /openapi.json documente 403 pour 5 endpoints + 501 pour 4 POST."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()

    paths = spec.get("paths", {})
    admin_paths = {
        p: ops for p, ops in paths.items() if p.startswith("/api/admin/catalogue")
    }
    assert admin_paths, "aucun chemin /api/admin/catalogue documente dans OpenAPI"

    post_paths = {
        "/api/admin/catalogue/criteria",
        "/api/admin/catalogue/referentials",
        "/api/admin/catalogue/packs",
        "/api/admin/catalogue/rules",
    }

    for path, ops in admin_paths.items():
        for method, operation in ops.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = operation.get("responses", {})
            assert "403" in responses, (
                f"{method.upper()} {path} : statut 403 absent de OpenAPI"
            )
            if path in post_paths and method == "post":
                assert "501" in responses, (
                    f"{method.upper()} {path} : statut 501 absent de OpenAPI"
                )

    # GET /fact-types ne doit PAS documenter 501
    fact_types_ops = admin_paths.get("/api/admin/catalogue/fact-types", {})
    get_op = fact_types_ops.get("get", {})
    get_responses = get_op.get("responses", {})
    assert "501" not in get_responses, (
        "GET /fact-types ne doit pas documenter 501 (endpoint effectif)"
    )
