"""Tests unitaires du service de generation de rapports ESG (T013).

Verifie la logique metier : validation, generation complete avec mock LLM.
"""

import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.esg import ESGAssessment, ESGStatusEnum
from app.models.report import Report, ReportStatusEnum
from app.models.user import User
from tests.conftest import make_unique_email


async def create_test_user(db: AsyncSession) -> User:
    """Creer un utilisateur de test."""
    user = User(
        email=make_unique_email(),
        hashed_password="fakehash",
        full_name="Aminata Toure",
        company_name="GreenTech SARL",
    )
    db.add(user)
    await db.flush()
    return user


async def create_completed_assessment(db: AsyncSession, user_id: uuid.UUID) -> ESGAssessment:
    """Creer une evaluation ESG completee avec donnees realistes."""
    assessment = ESGAssessment(
        user_id=user_id,
        status=ESGStatusEnum.completed,
        sector="agriculture",
        overall_score=71.7,
        environment_score=72.0,
        social_score=58.0,
        governance_score=85.0,
        assessment_data={
            "criteria_scores": {
                "E1": {"score": 7, "justification": "Bonne gestion", "sources": []},
                "E2": {"score": 5, "justification": "Peut mieux faire", "sources": []},
                "S1": {"score": 6, "justification": "Correct", "sources": []},
                "G1": {"score": 9, "justification": "Excellent", "sources": []},
            },
            "pillar_details": {
                "environment": {"raw_score": 6.0, "weighted_score": 72.0, "weights_applied": {}},
                "social": {"raw_score": 5.8, "weighted_score": 58.0, "weights_applied": {}},
                "governance": {"raw_score": 8.5, "weighted_score": 85.0, "weights_applied": {}},
            },
        },
        recommendations=[
            {
                "priority": 1,
                "criteria_code": "E2",
                "pillar": "environment",
                "title": "Ameliorer l'efficacite energetique",
                "description": "Investir dans les energies renouvelables",
                "impact": "high",
                "effort": "medium",
                "timeline": "6 mois",
            }
        ],
        strengths=[
            {
                "criteria_code": "G1",
                "pillar": "governance",
                "title": "Gouvernance exemplaire",
                "description": "Structure de gouvernance solide",
                "score": 9,
            }
        ],
        gaps=[
            {"criteria_code": "E2", "pillar": "environment", "title": "Energie", "score": 5}
        ],
        sector_benchmark={
            "sector": "agriculture",
            "averages": {
                "environment": 55.0,
                "social": 60.0,
                "governance": 50.0,
                "overall": 55.0,
            },
            "position": "above_average",
            "percentile": 75,
        },
    )
    db.add(assessment)
    await db.flush()
    return assessment


class TestGenerateReport:
    """Tests de la fonction generate_report."""

    @pytest.mark.asyncio
    async def test_generate_report_success(self, db_session: AsyncSession) -> None:
        """T013-01 : Generation reussie d'un rapport PDF."""
        user = await create_test_user(db_session)
        assessment = await create_completed_assessment(db_session, user.id)
        await db_session.commit()

        mock_weasyprint = MagicMock()

        def _fake_write_pdf(target):
            """Story 10.6 : write_pdf reçoit désormais un BytesIO buffer
            (persistance via storage.put). Garde rétrocompat path."""
            from io import IOBase
            from pathlib import Path

            fake_content = b"%PDF-1.4 fake content"
            if isinstance(target, IOBase) or hasattr(target, "write"):
                target.write(fake_content)
                return
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_bytes(fake_content)

        mock_weasyprint.HTML.return_value.write_pdf.side_effect = _fake_write_pdf

        with (
            patch(
                "app.modules.reports.service.generate_executive_summary",
                new_callable=AsyncMock,
                return_value="Resume executif de test genere par IA.",
            ),
            patch.dict(sys.modules, {"weasyprint": mock_weasyprint}),
        ):
            from app.modules.reports.service import generate_report

            report = await generate_report(db_session, assessment.id, user.id)

        assert report is not None
        assert report.status == ReportStatusEnum.completed
        assert report.assessment_id == assessment.id
        assert report.user_id == user.id
        assert report.file_size is not None
        assert report.file_size > 0
        assert report.generated_at is not None

    @pytest.mark.asyncio
    async def test_generate_report_rejects_draft_assessment(self, db_session: AsyncSession) -> None:
        """T013-02 : Rejet si l'evaluation n'est pas completee."""
        from app.modules.reports.service import generate_report

        user = await create_test_user(db_session)
        assessment = ESGAssessment(
            user_id=user.id,
            status=ESGStatusEnum.draft,
            sector="agriculture",
        )
        db_session.add(assessment)
        await db_session.commit()

        with pytest.raises(ValueError, match="completed"):
            await generate_report(db_session, assessment.id, user.id)

    @pytest.mark.asyncio
    async def test_generate_report_rejects_nonexistent_assessment(
        self, db_session: AsyncSession
    ) -> None:
        """T013-03 : Rejet si l'evaluation n'existe pas."""
        from app.modules.reports.service import generate_report

        user = await create_test_user(db_session)
        await db_session.commit()

        fake_id = uuid.uuid4()
        with pytest.raises(ValueError, match="introuvable"):
            await generate_report(db_session, fake_id, user.id)


class TestExecutiveSummaryFallback:
    """BUG-V6-001 : fallback deterministe sur echec LLM."""

    @pytest.mark.asyncio
    async def test_executive_summary_timeout_fallback(self, caplog) -> None:
        """Si LLM timeout, fallback deterministe est retourne sans exception."""
        import asyncio
        import logging

        from app.core.llm_guards import (
            FORBIDDEN_VOCAB,
            MAX_SUMMARY_LEN,
            MIN_SUMMARY_LEN,
            assert_language_fr,
            assert_length,
            assert_no_forbidden_vocabulary,
            assert_numeric_coherence,
        )
        from app.modules.reports.service import generate_executive_summary

        async def _timeout_call(*args, **kwargs):
            raise asyncio.TimeoutError("simulated httpx read timeout after 120s")

        caplog.set_level(logging.WARNING)
        with patch(
            "app.modules.reports.service.run_guarded_llm_call",
            side_effect=_timeout_call,
        ):
            result = await generate_executive_summary(
                company_name="GreenTech SARL",
                sector="agriculture",
                overall_score=71.7,
                environment_score=72.0,
                social_score=58.0,
                governance_score=85.0,
                strengths=[
                    {"title": "Gouvernance exemplaire", "score": 9},
                    {"title": "Reporting financier solide", "score": 8},
                ],
                gaps=[
                    {"title": "Efficacite energetique", "score": 5},
                ],
                benchmark_position="above_average",
                user_id="test-user-1",
            )

        # 1) string non vide, longueur dans les bornes
        assert isinstance(result, str)
        assert len(result) >= MIN_SUMMARY_LEN
        assert len(result) <= MAX_SUMMARY_LEN

        # 2) contient les elements cles structures
        assert "GreenTech SARL" in result
        assert "71.7" in result
        assert "Agriculture" in result

        # 3) pas de vocabulaire interdit
        for term in FORBIDDEN_VOCAB:
            assert term not in result.lower()

        # 4) passe les 4 guards (length / langue FR / vocab / coherence numerique)
        sources = {
            "overall": 71.7,
            "environment": 72.0,
            "social": 58.0,
            "governance": 85.0,
        }
        assert_length(result, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
        assert_language_fr(result, "executive_summary")
        assert_no_forbidden_vocabulary(result, "executive_summary")
        assert_numeric_coherence(result, sources, "executive_summary")

        # 5) log fallback emis avec metric exploitable + assessment_id
        fallback_records = [
            r for r in caplog.records
            if getattr(r, "metric", None) == "executive_summary_fallback"
        ]
        assert len(fallback_records) == 1
        assert fallback_records[0].cause == "TimeoutError"
        assert fallback_records[0].user_id == "test-user-1"
        # PATCH-2 : aucun str(exc) brut dans les logs (pas de fuite secrets)
        assert not hasattr(fallback_records[0], "cause_msg")

    @pytest.mark.parametrize(
        "exc_factory",
        [
            pytest.param(lambda: ConnectionError("network down"), id="connection"),
            pytest.param(lambda: RuntimeError("rate limit hit"), id="runtime"),
            pytest.param(
                lambda: __import__("fastapi").HTTPException(503, "provider"),
                id="http_503",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_executive_summary_fallback_on_infra_errors(
        self, caplog, exc_factory
    ) -> None:
        """PATCH-4 : fallback active sur la matrice d'erreurs infra (BUG-V6-001 I/O)."""
        import logging

        from app.modules.reports.service import generate_executive_summary

        async def _raise(*args, **kwargs):
            raise exc_factory()

        caplog.set_level(logging.WARNING)
        with patch(
            "app.modules.reports.service.run_guarded_llm_call",
            side_effect=_raise,
        ):
            result = await generate_executive_summary(
                company_name="ACME SARL",
                sector="services",
                overall_score=50.0,
                environment_score=50.0,
                social_score=50.0,
                governance_score=50.0,
                strengths=[],
                gaps=[],
                benchmark_position="average",
                user_id="user-1",
                assessment_id="assess-42",
            )

        assert isinstance(result, str)
        assert len(result) >= 200
        fallback = [
            r for r in caplog.records
            if getattr(r, "metric", None) == "executive_summary_fallback"
        ]
        assert len(fallback) == 1
        assert fallback[0].assessment_id == "assess-42"

    @pytest.mark.asyncio
    async def test_fallback_with_minimal_data_passes_guards(self) -> None:
        """PATCH-5 : strengths=[], gaps=[], benchmark_position vide -> fallback >= 200 chars."""
        from app.core.llm_guards import (
            FORBIDDEN_VOCAB,
            MAX_SUMMARY_LEN,
            MIN_SUMMARY_LEN,
            assert_language_fr,
            assert_length,
            assert_no_forbidden_vocabulary,
            assert_numeric_coherence,
        )
        from app.modules.reports.service import _build_deterministic_summary

        result = _build_deterministic_summary(
            company_name="X SARL",
            sector_label="Services",
            overall_score=50.0,
            environment_score=50.0,
            social_score=50.0,
            governance_score=50.0,
            strengths=[],
            gaps=[],
            benchmark_position_label="",
        )
        assert MIN_SUMMARY_LEN <= len(result) <= MAX_SUMMARY_LEN
        assert_length(result, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
        assert_language_fr(result, "executive_summary")
        assert_no_forbidden_vocabulary(result, "executive_summary")
        assert_numeric_coherence(
            result, {"overall": 50.0, "e": 50.0, "s": 50.0, "g": 50.0}, "executive_summary"
        )
        for term in FORBIDDEN_VOCAB:
            assert term not in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_with_zero_scores_passes_guards(self) -> None:
        """PATCH-5 : tous scores a 0 -> source_values vide, pas de drift numerique."""
        from app.core.llm_guards import (
            MAX_SUMMARY_LEN,
            MIN_SUMMARY_LEN,
            assert_length,
            assert_numeric_coherence,
        )
        from app.modules.reports.service import _build_deterministic_summary

        result = _build_deterministic_summary(
            company_name="ZeroCo",
            sector_label="Services",
            overall_score=0.0,
            environment_score=0.0,
            social_score=0.0,
            governance_score=0.0,
            strengths=[],
            gaps=[],
            benchmark_position_label="",
        )
        assert_length(result, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
        # source_values vide -> assert_numeric_coherence ne doit rien lever
        assert_numeric_coherence(result, {}, "executive_summary")

    @pytest.mark.asyncio
    async def test_fallback_with_forbidden_company_name_falls_to_minimal(
        self, caplog
    ) -> None:
        """PATCH-1 : nom d'entreprise contenant 'Garantie' -> bascule vers minimal."""
        import logging

        from app.modules.reports.service import (
            _FALLBACK_MINIMAL_SUMMARY,
            _build_deterministic_summary,
        )

        caplog.set_level(logging.WARNING)
        result = _build_deterministic_summary(
            company_name="Garantie SARL",  # contient 'garantie' (FORBIDDEN_VOCAB)
            sector_label="Services",
            overall_score=50.0,
            environment_score=50.0,
            social_score=50.0,
            governance_score=50.0,
            strengths=[],
            gaps=[],
            benchmark_position_label="",
        )
        assert result == _FALLBACK_MINIMAL_SUMMARY
        minimal_logs = [
            r for r in caplog.records
            if getattr(r, "metric", None) == "executive_summary_fallback_minimal"
        ]
        assert len(minimal_logs) == 1
        assert minimal_logs[0].guard_code == "forbidden_vocab"

    @pytest.mark.asyncio
    async def test_pdf_generation_succeeds_with_30_criteria_via_fallback(
        self, db_session: AsyncSession, caplog
    ) -> None:
        """PDF se genere avec 30 criteres ESG meme si le LLM echoue (HTTPException 500)."""
        import logging

        from fastapi import HTTPException

        user = await create_test_user(db_session)

        # Construire un assessment avec 30 criteres (E1-E10, S1-S10, G1-G10).
        criteria_scores = {}
        for prefix in ("E", "S", "G"):
            for i in range(1, 11):
                criteria_scores[f"{prefix}{i}"] = {
                    "score": 6,
                    "justification": f"Critere {prefix}{i} evalue",
                    "sources": [],
                }

        assessment = ESGAssessment(
            user_id=user.id,
            status=ESGStatusEnum.completed,
            sector="agriculture",
            overall_score=65.0,
            environment_score=60.0,
            social_score=65.0,
            governance_score=70.0,
            assessment_data={
                "criteria_scores": criteria_scores,
                "pillar_details": {
                    "environment": {"raw_score": 6.0, "weighted_score": 60.0, "weights_applied": {}},
                    "social": {"raw_score": 6.5, "weighted_score": 65.0, "weights_applied": {}},
                    "governance": {"raw_score": 7.0, "weighted_score": 70.0, "weights_applied": {}},
                },
            },
            strengths=[{"title": "Gouvernance", "score": 7}],
            gaps=[{"title": "Energie", "score": 5}],
            sector_benchmark={
                "sector": "agriculture",
                "averages": {"environment": 55.0, "social": 60.0, "governance": 50.0, "overall": 55.0},
                "position": "above_average",
                "percentile": 70,
            },
        )
        db_session.add(assessment)
        await db_session.commit()

        mock_weasyprint = MagicMock()

        def _fake_write_pdf(target):
            from io import IOBase
            from pathlib import Path

            fake_content = b"%PDF-1.4 fake content from fallback path"
            if isinstance(target, IOBase) or hasattr(target, "write"):
                target.write(fake_content)
                return
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_bytes(fake_content)

        mock_weasyprint.HTML.return_value.write_pdf.side_effect = _fake_write_pdf

        async def _raise_http_500(*args, **kwargs):
            raise HTTPException(
                status_code=500,
                detail="Erreur generation executive_summary : guard LLM echoue apres retry",
            )

        caplog.set_level(logging.WARNING)
        with (
            patch(
                "app.modules.reports.service.run_guarded_llm_call",
                side_effect=_raise_http_500,
            ),
            patch.dict(sys.modules, {"weasyprint": mock_weasyprint}),
        ):
            from app.modules.reports.service import generate_report

            report = await generate_report(db_session, assessment.id, user.id)

        # PDF aboutit malgre l'echec LLM
        assert report is not None
        assert report.status == ReportStatusEnum.completed
        assert report.file_size is not None
        assert report.file_size > 0
        assert report.generated_at is not None

        # Log fallback emis (metric Grafana)
        fallback_records = [
            r for r in caplog.records
            if getattr(r, "metric", None) == "executive_summary_fallback"
        ]
        assert len(fallback_records) == 1
        assert fallback_records[0].cause == "HTTPException"
