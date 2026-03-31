"""Tests integration des endpoints API rapports ESG (T015).

Verifie POST generate, GET status, GET download, GET liste.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.esg import ESGAssessment, ESGStatusEnum
from app.models.report import Report, ReportStatusEnum, ReportTypeEnum
from tests.conftest import make_unique_email


async def create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Creer un utilisateur et retourner ses donnees + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Aminata Toure",
        "company_name": "GreenTech SARL",
    }
    await client.post("/api/auth/register", json=data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login_response.json()["access_token"]
    return data, token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def set_user_sector(client: AsyncClient, token: str, sector: str = "agriculture") -> None:
    """Configurer le secteur du profil utilisateur."""
    await client.patch(
        "/api/company/profile",
        headers=auth_headers(token),
        json={"sector": sector},
    )


async def create_completed_assessment_via_api(
    client: AsyncClient, token: str, db_session: AsyncSession
) -> str:
    """Creer une evaluation completee directement en base."""
    await set_user_sector(client, token)

    # Creer l'evaluation via API
    response = await client.post(
        "/api/esg/assessments",
        headers=auth_headers(token),
    )
    assessment_id = response.json()["id"]

    # Completer directement en base
    from sqlalchemy import select, update

    await db_session.execute(
        update(ESGAssessment)
        .where(ESGAssessment.id == uuid.UUID(assessment_id))
        .values(
            status=ESGStatusEnum.completed,
            overall_score=71.7,
            environment_score=72.0,
            social_score=58.0,
            governance_score=85.0,
            assessment_data={
                "criteria_scores": {
                    "E1": {"score": 7, "justification": "Bon", "sources": []},
                },
                "pillar_details": {
                    "environment": {"raw_score": 7.0, "weighted_score": 72.0, "weights_applied": {}},
                    "social": {"raw_score": 5.8, "weighted_score": 58.0, "weights_applied": {}},
                    "governance": {"raw_score": 8.5, "weighted_score": 85.0, "weights_applied": {}},
                },
            },
            recommendations=[],
            strengths=[],
            gaps=[],
            sector_benchmark={
                "sector": "agriculture",
                "averages": {"environment": 55.0, "social": 60.0, "governance": 50.0, "overall": 55.0},
                "position": "above_average",
                "percentile": 75,
            },
        )
    )
    await db_session.commit()
    return assessment_id


class TestGenerateEndpoint:
    """Tests POST /api/reports/esg/{assessment_id}/generate."""

    @pytest.mark.asyncio
    async def test_generate_report_201(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """T015-01 : Generation reussie retourne 201."""
        _, token = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume executif de test.",
        ):
            response = await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token),
            )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "completed"
        assert body["assessment_id"] == assessment_id
        assert body["report_type"] == "esg_compliance"

    @pytest.mark.asyncio
    async def test_generate_report_400_not_completed(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T015-02 : Retourne 400 si evaluation pas completee."""
        _, token = await create_authenticated_user(client)
        await set_user_sector(client, token)

        response = await client.post(
            "/api/esg/assessments",
            headers=auth_headers(token),
        )
        assessment_id = response.json()["id"]

        response = await client.post(
            f"/api/reports/esg/{assessment_id}/generate",
            headers=auth_headers(token),
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_report_404_not_found(self, client: AsyncClient) -> None:
        """T015-03 : Retourne 404 si evaluation inexistante."""
        _, token = await create_authenticated_user(client)
        fake_id = uuid.uuid4()

        response = await client.post(
            f"/api/reports/esg/{fake_id}/generate",
            headers=auth_headers(token),
        )
        assert response.status_code == 404


class TestStatusEndpoint:
    """Tests GET /api/reports/{report_id}/status."""

    @pytest.mark.asyncio
    async def test_status_returns_200(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T015-04 : Statut d'un rapport existant."""
        _, token = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume de test.",
        ):
            gen_response = await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token),
            )

        report_id = gen_response.json()["id"]
        response = await client.get(
            f"/api/reports/{report_id}/status",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["status"] in ("generating", "completed", "failed")


class TestDownloadEndpoint:
    """Tests GET /api/reports/{report_id}/download."""

    @pytest.mark.asyncio
    async def test_download_returns_pdf(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T015-05 : Telechargement d'un rapport complete."""
        _, token = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume de test.",
        ):
            gen_response = await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token),
            )

        report_id = gen_response.json()["id"]
        response = await client.get(
            f"/api/reports/{report_id}/download",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_download_404_nonexistent(self, client: AsyncClient) -> None:
        """T015-06 : Retourne 404 si rapport inexistant."""
        _, token = await create_authenticated_user(client)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/api/reports/{fake_id}/download",
            headers=auth_headers(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_403_other_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T015-07 : Retourne 403 si rapport d'un autre utilisateur."""
        # Utilisateur 1 genere le rapport
        _, token1 = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token1, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume de test.",
        ):
            gen_response = await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token1),
            )
        report_id = gen_response.json()["id"]

        # Utilisateur 2 tente de telecharger
        _, token2 = await create_authenticated_user(client)
        response = await client.get(
            f"/api/reports/{report_id}/download",
            headers=auth_headers(token2),
        )
        assert response.status_code == 403


class TestListReportsEndpoint:
    """Tests GET /api/reports/ (T022 — US2)."""

    @pytest.mark.asyncio
    async def test_list_reports_paginated(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T022-01 : Liste paginee retourne les rapports de l'utilisateur."""
        _, token = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token, db_session)

        # Generer 2 rapports
        for _ in range(2):
            with patch(
                "app.modules.reports.service.generate_executive_summary",
                new_callable=AsyncMock,
                return_value="Resume de test.",
            ):
                await client.post(
                    f"/api/reports/esg/{assessment_id}/generate",
                    headers=auth_headers(token),
                )

        response = await client.get(
            "/api/reports/?page=1&limit=10",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_reports_filter_by_assessment(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T022-02 : Filtrage par assessment_id."""
        _, token = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume de test.",
        ):
            await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token),
            )

        # Filtrer par le bon assessment_id
        response = await client.get(
            f"/api/reports/?assessment_id={assessment_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert all(r["assessment_id"] == assessment_id for r in body["items"])

        # Filtrer par un assessment_id inexistant
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/reports/?assessment_id={fake_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_reports_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """T022-03 : Isolation par user_id — un utilisateur ne voit que ses rapports."""
        # Utilisateur 1 genere un rapport
        _, token1 = await create_authenticated_user(client)
        assessment_id = await create_completed_assessment_via_api(client, token1, db_session)

        with patch(
            "app.modules.reports.service.generate_executive_summary",
            new_callable=AsyncMock,
            return_value="Resume de test.",
        ):
            await client.post(
                f"/api/reports/esg/{assessment_id}/generate",
                headers=auth_headers(token1),
            )

        # Utilisateur 2 ne doit rien voir
        _, token2 = await create_authenticated_user(client)
        response = await client.get(
            "/api/reports/",
            headers=auth_headers(token2),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_reports_empty(self, client: AsyncClient) -> None:
        """T022-04 : Liste vide pour un utilisateur sans rapports."""
        _, token = await create_authenticated_user(client)
        response = await client.get(
            "/api/reports/",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []
