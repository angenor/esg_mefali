"""Tests d'integration des guards LLM sur le resume executif (story 9.6 / AC7-AC10)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.reports.service import generate_executive_summary


VALID_SUMMARY_FR = (
    "Votre entreprise ACME Textile presente un profil ESG globalement satisfaisant "
    "avec un score global de 54/100. Les points forts identifies sur la gouvernance "
    "illustrent une demarche de transparence. Le pilier environnemental montre un score "
    "de 60/100, reflet d'initiatives concretes sur la reduction des consommations. "
    "Le pilier social avec 48/100 signale des axes d'amelioration sur les politiques "
    "RH et la formation. Nous recommandons de renforcer la politique RH et d'engager "
    "un suivi carbone regulier. Votre positionnement sectoriel est dans la mediane "
    "sectorielle pour le secteur textile en Afrique de l'Ouest."
)

HALLUCINATED_SUMMARY = (
    "Votre entreprise ACME Textile affiche un score ESG exceptionnel de 88/100, "
    "positionne au-dessus de la mediane sectorielle. Votre conformite est garantie "
    "sur tous les piliers. Nous saluons l'excellence de votre demarche et vous "
    "certifions eligible aux programmes GCF et SUNREF. Le pilier environnemental "
    "atteint 92/100 grace a des investissements structurants dans les energies "
    "renouvelables et l'efficacite energetique deployee sur tous les sites. "
    "Le pilier social a 95/100 demontre une politique RH exemplaire."
)


def _make_response(content: str) -> MagicMock:
    """Simuler un AIMessage langchain avec .content."""
    resp = MagicMock()
    resp.content = content
    return resp


class TestExecutiveSummaryGuardsIntegration:
    """AC7, AC9, AC10 : pipeline complet resume executif avec guards."""

    @pytest.mark.asyncio
    async def test_valid_summary_passes(self) -> None:
        """AC10 : resume LLM valide retourne tel quel (1 seul appel LLM)."""
        with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=_make_response(VALID_SUMMARY_FR))
            mock_llm_cls.return_value = mock_llm

            result = await generate_executive_summary(
                company_name="ACME",
                sector="textile",
                overall_score=54.0,
                environment_score=60.0,
                social_score=48.0,
                governance_score=54.0,
                strengths=[{"title": "Gouvernance", "score": 7}],
                gaps=[{"title": "Social", "score": 4}],
                benchmark_position="average",
                user_id="user-1",
            )
            assert "54/100" in result
            assert "garanti" not in result.lower()
            assert mock_llm.ainvoke.call_count == 1

    @pytest.mark.asyncio
    async def test_hallucinated_summary_triggers_retry_then_fallback(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC7 + AC9 + BUG-V6-001 : hallucination -> retry -> fallback (pas 500).

        BUG-V6-001 : la 500 historique remontee par run_guarded_llm_call est
        desormais capturee dans generate_executive_summary, qui retourne un
        resume deterministe. Les metriques llm_guard_failure restent emises
        (recovered + failed) pour la telemetrie Grafana.
        """
        with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=_make_response(HALLUCINATED_SUMMARY)
            )
            mock_llm_cls.return_value = mock_llm

            with caplog.at_level("WARNING"):
                result = await generate_executive_summary(
                    company_name="ACME",
                    sector="textile",
                    overall_score=54.0,
                    environment_score=60.0,
                    social_score=48.0,
                    governance_score=54.0,
                    strengths=[],
                    gaps=[],
                    benchmark_position="average",
                    user_id="user-1",
                )

            # Fallback deterministe retourne (pas d'exception)
            assert isinstance(result, str)
            assert "ACME" in result
            assert "54" in result  # score global present

            # Le LLM a bien ete appele 2x (base + retry) avant le fallback
            assert mock_llm.ainvoke.call_count == 2

            # Metriques llm_guard_failure preservees (telemetrie inchangee)
            guard_logs = [
                r for r in caplog.records
                if getattr(r, "metric", None) == "llm_guard_failure"
            ]
            assert len(guard_logs) >= 2  # 1 recovered + 1 failed
            assert guard_logs[-1].final_outcome == "failed"
            assert guard_logs[-1].target == "executive_summary"
            # AC9 : prompt_hash present, pas le prompt brut
            assert hasattr(guard_logs[-1], "prompt_hash")

            # Nouvelle metrique BUG-V6-001 : fallback emis
            fallback_logs = [
                r for r in caplog.records
                if getattr(r, "metric", None) == "executive_summary_fallback"
            ]
            assert len(fallback_logs) == 1
            assert fallback_logs[0].cause == "HTTPException"

    @pytest.mark.asyncio
    async def test_first_fail_then_retry_recovers(self) -> None:
        """AC7 : echec 1er appel + succes du retry renforce."""
        with patch("app.modules.reports.service.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(
                side_effect=[
                    _make_response(HALLUCINATED_SUMMARY),
                    _make_response(VALID_SUMMARY_FR),
                ]
            )
            mock_llm_cls.return_value = mock_llm

            result = await generate_executive_summary(
                company_name="ACME",
                sector="textile",
                overall_score=54.0,
                environment_score=60.0,
                social_score=48.0,
                governance_score=54.0,
                strengths=[],
                gaps=[],
                benchmark_position="average",
                user_id="user-1",
            )
            assert "54/100" in result
            assert mock_llm.ainvoke.call_count == 2
