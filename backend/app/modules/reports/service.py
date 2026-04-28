"""Service de generation de rapports ESG PDF.

Orchestre la collecte de donnees, generation de graphiques SVG,
appel LLM pour le resume executif, rendu template Jinja2 et
conversion HTML -> PDF via WeasyPrint.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import get_storage_provider, storage_key_for_report
from app.core.llm_guards import (
    MAX_SUMMARY_LEN,
    MIN_SUMMARY_LEN,
    LLMGuardError,
    assert_language_fr,
    assert_length,
    assert_no_forbidden_vocabulary,
    assert_numeric_coherence,
    run_guarded_llm_call,
)
from app.models.esg import ESGAssessment, ESGStatusEnum
from app.models.report import Report, ReportStatusEnum, ReportTypeEnum
from app.models.user import User
from app.modules.reports.charts import (
    generate_bar_chart_svg,
    generate_benchmark_chart_svg,
    generate_radar_chart_svg,
)
from app.prompts.esg_report import ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT

logger = logging.getLogger(__name__)

# Chemins
TEMPLATES_DIR = Path(__file__).parent / "templates"
# Story 10.6 : UPLOADS_DIR supprimé — persistance via `get_storage_provider()`.

# Mapping secteur -> label francais
SECTOR_LABELS = {
    "agriculture": "Agriculture",
    "energy": "Energie",
    "recycling": "Recyclage",
    "transport": "Transport",
    "manufacturing": "Industrie manufacturiere",
    "services": "Services",
    "construction": "Construction / BTP",
    "commerce": "Commerce",
    "mining": "Exploitation miniere",
    "fishing": "Peche",
    "tourism": "Tourisme",
    "tech": "Technologie",
    "finance": "Finance",
    "health": "Sante",
    "education": "Education",
}

BENCHMARK_POSITION_LABELS = {
    "above_average": "Au-dessus de la moyenne sectorielle",
    "average": "Dans la moyenne sectorielle",
    "below_average": "En dessous de la moyenne sectorielle",
}


# BUG-V6-001 PATCH-1 : constante pré-validée utilisée si le fallback dynamique
# échoue lui-même les guards (cas pathologique : company_name="Garantie SARL" etc.).
# Texte fixe, sans données dynamiques, vérifié à l'import (assertions module).
_FALLBACK_MINIMAL_SUMMARY = (
    "Le rapport ESG est genere a partir des donnees structurees de l'evaluation. "
    "Les scores des piliers Environnement, Social et Gouvernance sont consultables "
    "dans les sections detaillees du document. "
    "Une lecture critere par critere est recommandee pour orienter le plan "
    "d'action et engager une mise en conformite progressive avec les referentiels "
    "applicables. Les axes prioritaires d'amelioration apparaissent dans la section "
    "consacree aux ecarts identifies, et les points forts dans la section dediee."
)


def _build_deterministic_summary(
    company_name: str,
    sector_label: str,
    overall_score: float,
    environment_score: float,
    social_score: float,
    governance_score: float,
    strengths: list[dict],
    gaps: list[dict],
    benchmark_position_label: str,
) -> str:
    """Resume executif fallback construit depuis les donnees structurees.

    Utilise quand l'appel LLM echoue (timeout, guard post-retry, infra). Le
    texte respecte les 4 guards : longueur >= MIN_SUMMARY_LEN, langue FR,
    aucun terme de FORBIDDEN_VOCAB, valeurs numeriques = sources reelles.

    BUG-V6-001 PATCH-1 : les 4 guards sont re-appliques apres construction.
    Si le texte construit echoue un guard (ex. company_name contient un terme
    interdit comme "Garantie"), bascule vers _FALLBACK_MINIMAL_SUMMARY (texte
    constant pre-valide, sans donnees dynamiques).
    """
    parts = [
        f"L'entreprise {company_name} ({sector_label}) obtient un score ESG global "
        f"de {overall_score}/100, avec un pilier Environnement a {environment_score}/100, "
        f"un pilier Social a {social_score}/100 et un pilier Gouvernance a "
        f"{governance_score}/100."
    ]
    if strengths:
        top = ", ".join(s.get("title", "") for s in strengths[:3] if s.get("title"))
        if top:
            parts.append(f"Les principaux points forts identifies sont : {top}.")
    if gaps:
        top = ", ".join(g.get("title", "") for g in gaps[:3] if g.get("title"))
        if top:
            parts.append(f"Les axes d'amelioration prioritaires concernent : {top}.")
    if benchmark_position_label:
        parts.append(f"Positionnement sectoriel : {benchmark_position_label}.")
    parts.append(
        "Ce resume est genere a partir des donnees structurees de l'evaluation. "
        "Une lecture detaillee des piliers et critere par critere est recommandee "
        "pour orienter le plan d'action et la mise en conformite progressive."
    )
    candidate = " ".join(parts)

    # PATCH-1 : re-appliquer les guards sur le fallback dynamique.
    # source_values filtre les zeros (cf. assert_numeric_coherence) ; pas
    # de drift attendu puisque les chiffres ecrits sont les sources reelles.
    raw_sources = {
        "overall_score": overall_score,
        "environment_score": environment_score,
        "social_score": social_score,
        "governance_score": governance_score,
    }
    source_values = {
        name: float(v)
        for name, v in raw_sources.items()
        if v is not None and float(v) != 0.0
    }
    try:
        assert_length(candidate, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
        assert_language_fr(candidate, "executive_summary")
        assert_no_forbidden_vocabulary(candidate, "executive_summary")
        assert_numeric_coherence(candidate, source_values, "executive_summary")
        return candidate
    except LLMGuardError as guard_err:
        logger.warning(
            "Resume executif : fallback dynamique non conforme, bascule vers minimal",
            extra={
                "metric": "executive_summary_fallback_minimal",
                "guard_code": guard_err.code,
                "guard_details": guard_err.details,
            },
        )
        return _FALLBACK_MINIMAL_SUMMARY


async def generate_executive_summary(
    company_name: str,
    sector: str,
    overall_score: float,
    environment_score: float,
    social_score: float,
    governance_score: float,
    strengths: list[dict],
    gaps: list[dict],
    benchmark_position: str,
    user_id: str | None = None,
    assessment_id: str | None = None,
) -> str:
    """Generer le resume executif via LLM avec guards (story 9.6).

    BUG-V6-001 : timeout LLM porte a 120 s pour absorber les generations
    longues sur 30 criteres ESG. Tout echec (timeout, guard post-retry, infra)
    bascule sur un resume deterministe construit depuis les donnees
    structurees, pour eviter un 500 utilisateur.
    """
    strengths_text = "\n".join(
        f"- {s.get('title', 'N/A')} ({s.get('score', 0)}/10)" for s in (strengths or [])
    ) or "Aucun point fort identifie"

    gaps_text = "\n".join(
        f"- {g.get('title', 'N/A')} ({g.get('score', 0)}/10)" for g in (gaps or [])
    ) or "Aucun axe d'amelioration identifie"

    base_prompt = ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT.format(
        company_name=company_name,
        sector=SECTOR_LABELS.get(sector, sector),
        overall_score=overall_score,
        environment_score=environment_score,
        social_score=social_score,
        governance_score=governance_score,
        strengths_text=strengths_text,
        gaps_text=gaps_text,
        benchmark_position=BENCHMARK_POSITION_LABELS.get(benchmark_position, benchmark_position),
    )
    hardened_prompt = base_prompt + (
        "\n\nCONTRAINTES STRICTES :"
        "\n- Redige exclusivement en francais."
        f"\n- Utilise uniquement ces valeurs numeriques : "
        f"overall={overall_score}/100, E={environment_score}/100, "
        f"S={social_score}/100, G={governance_score}/100."
        "\n- Interdiction d'utiliser les mots : garanti, certifie, valide par, "
        "homologue, accredite."
        f"\n- Longueur : entre {MIN_SUMMARY_LEN} et {MAX_SUMMARY_LEN} caracteres."
    )

    # Filtrer None et 0 des sources pour eviter les faux drifts (review 9.6).
    raw_sources = {
        "overall_score": overall_score,
        "environment_score": environment_score,
        "social_score": social_score,
        "governance_score": governance_score,
    }
    source_values: dict[str, float] = {
        name: float(v)
        for name, v in raw_sources.items()
        if v is not None and float(v) != 0.0
    }

    def guards(text: str) -> None:
        # Ordre deterministe AC7 : length -> langue -> vocab -> numerique
        assert_length(text, MIN_SUMMARY_LEN, MAX_SUMMARY_LEN, "executive_summary")
        assert_language_fr(text, "executive_summary")
        assert_no_forbidden_vocabulary(text, "executive_summary")
        assert_numeric_coherence(text, source_values, "executive_summary")

    async def llm_call(prompt_to_send: str) -> str:
        llm = ChatOpenAI(
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=0.3,
            # BUG-V6-001 : 120 s pour absorber les generations longues
            # (vs ~30 s defaut httpx). Local au resume executif, le provider
            # partage reste a 60 s pour les autres surfaces LLM.
            request_timeout=120,
        )
        # Placer le prompt dans SystemMessage (coherent avec action_plan)
        # pour que le hardened_prompt soit effectif au retry (review 9.6).
        response = await llm.ainvoke([
            SystemMessage(content=prompt_to_send),
            HumanMessage(content="Redige le resume executif demande."),
        ])
        content = response.content if hasattr(response, "content") else str(response)
        return content.strip() if isinstance(content, str) else str(content).strip()

    try:
        return await run_guarded_llm_call(
            llm_call=llm_call,
            guards=guards,
            base_prompt=base_prompt,
            hardened_prompt=hardened_prompt,
            target="executive_summary",
            user_id=user_id or "anonymous",
        )
    except Exception as exc:
        # BUG-V6-001 : fallback deterministe sur tout echec (timeout httpx,
        # HTTPException(500) post-retry, ConnectionError, RateLimitError...).
        # Le rapport reste genere avec un resume minimal mais conforme aux
        # guards plutot qu'un 500 utilisateur. Les ValueError metier amont
        # (assessment introuvable / not completed) ne traversent pas cette
        # fonction : ils sont leves dans generate_report avant l'appel.
        # PATCH-2 : ne PAS logger str(exc) brut — peut contenir des secrets
        # (clé API OpenRouter, payload sensible). On capte uniquement le
        # type d'exception, et le status_code si HTTPException FastAPI.
        log_extra: dict[str, Any] = {
            "metric": "executive_summary_fallback",
            "cause": type(exc).__name__,
            "user_id": user_id or "anonymous",
            "assessment_id": assessment_id or "unknown",
        }
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            log_extra["status_code"] = status_code
        logger.warning(
            "Resume executif : fallback deterministe (LLM indisponible)",
            extra=log_extra,
        )
        return _build_deterministic_summary(
            company_name=company_name,
            sector_label=SECTOR_LABELS.get(sector, sector),
            overall_score=overall_score,
            environment_score=environment_score,
            social_score=social_score,
            governance_score=governance_score,
            strengths=strengths or [],
            gaps=gaps or [],
            benchmark_position_label=BENCHMARK_POSITION_LABELS.get(
                benchmark_position, benchmark_position
            ),
        )


def _extract_criteria_by_pillar(assessment_data: dict) -> dict[str, list[dict]]:
    """Extraire les scores par critere groupes par pilier."""
    criteria_scores = assessment_data.get("criteria_scores", {})
    pillar_criteria: dict[str, list[dict]] = {
        "environment": [],
        "social": [],
        "governance": [],
    }

    pillar_prefixes = {"E": "environment", "S": "social", "G": "governance"}

    for code, detail in criteria_scores.items():
        prefix = code[0].upper() if code else ""
        pillar = pillar_prefixes.get(prefix)
        if pillar:
            pillar_criteria[pillar].append({
                "code": code,
                "label": code,
                "score": detail.get("score", 0),
                "max": 10,
            })

    # Trier par code
    for pillar in pillar_criteria:
        pillar_criteria[pillar].sort(key=lambda c: c["code"])

    return pillar_criteria


def _render_html(
    assessment: ESGAssessment,
    user: User,
    executive_summary: str,
    radar_svg: str,
    pillar_bar_charts: dict[str, str],
    benchmark_svg: str | None,
    pillar_criteria: dict[str, list[dict]],
) -> str:
    """Rendre le template HTML du rapport avec les donnees."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("esg_report.html")

    css_path = TEMPLATES_DIR / "esg_report.css"
    css_content = css_path.read_text(encoding="utf-8")

    sector = assessment.sector or "unknown"
    benchmark = assessment.sector_benchmark or {}

    return template.render(
        css=css_content,
        company_name=user.company_name,
        sector_label=SECTOR_LABELS.get(sector, sector),
        overall_score=assessment.overall_score or 0,
        environment_score=assessment.environment_score or 0,
        social_score=assessment.social_score or 0,
        governance_score=assessment.governance_score or 0,
        executive_summary=executive_summary,
        generation_date=datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        radar_chart_svg=radar_svg,
        pillar_bar_charts=pillar_bar_charts,
        pillar_criteria=pillar_criteria,
        strengths=assessment.strengths or [],
        gaps=assessment.gaps or [],
        recommendations=assessment.recommendations or [],
        benchmark_chart_svg=benchmark_svg,
        benchmark_position=benchmark.get("position"),
        benchmark_position_label=BENCHMARK_POSITION_LABELS.get(
            benchmark.get("position", ""), ""
        ),
    )


async def generate_report(
    db: AsyncSession,
    assessment_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Report:
    """Generer un rapport PDF a partir d'une evaluation ESG completee.

    Raises:
        ValueError: Si l'evaluation n'existe pas ou n'est pas completee.
    """
    # 1. Charger l'evaluation
    result = await db.execute(
        select(ESGAssessment).where(
            ESGAssessment.id == assessment_id,
            ESGAssessment.user_id == user_id,
        )
    )
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise ValueError(f"Evaluation ESG introuvable : {assessment_id}")

    if assessment.status != ESGStatusEnum.completed:
        raise ValueError(
            "L'evaluation ESG doit etre au statut 'completed' pour generer un rapport."
        )

    # 1b. Verifier qu'il n'y a pas deja une generation en cours pour cette evaluation
    from sqlalchemy import and_

    existing_generating = await db.execute(
        select(Report).where(
            and_(
                Report.assessment_id == assessment_id,
                Report.status == ReportStatusEnum.generating,
            )
        )
    )
    if existing_generating.scalar_one_or_none() is not None:
        raise ValueError(
            "Une generation de rapport est deja en cours pour cette evaluation."
        )

    # 2. Charger l'utilisateur
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    # 3. Creer l'entree Report (status: generating)
    file_name = f"rapport-esg-{user.company_name.replace(' ', '-').lower()}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}.pdf"
    report = Report(
        user_id=user_id,
        assessment_id=assessment_id,
        report_type=ReportTypeEnum.esg_compliance,
        status=ReportStatusEnum.generating,
        file_path=file_name,
    )
    db.add(report)
    await db.flush()

    try:
        # 4. Generer les graphiques SVG
        pillar_scores = {
            "environment": assessment.environment_score or 0,
            "social": assessment.social_score or 0,
            "governance": assessment.governance_score or 0,
        }
        radar_svg = generate_radar_chart_svg(pillar_scores)

        assessment_data = assessment.assessment_data or {}
        pillar_criteria = _extract_criteria_by_pillar(assessment_data)

        pillar_bar_charts = {}
        pillar_labels = {"environment": "Environnement", "social": "Social", "governance": "Gouvernance"}
        for pillar_key, pillar_label in pillar_labels.items():
            if pillar_criteria[pillar_key]:
                pillar_bar_charts[pillar_key] = generate_bar_chart_svg(
                    pillar_criteria[pillar_key], pillar_label
                )
            else:
                pillar_bar_charts[pillar_key] = ""

        # Benchmark chart
        benchmark_svg = None
        benchmark = assessment.sector_benchmark
        if benchmark and benchmark.get("averages"):
            company_scores = {
                **pillar_scores,
                "overall": assessment.overall_score or 0,
            }
            benchmark_svg = generate_benchmark_chart_svg(
                company_scores,
                benchmark["averages"],
                SECTOR_LABELS.get(assessment.sector, assessment.sector),
            )

        # 5. Generer le resume executif IA
        executive_summary = await generate_executive_summary(
            company_name=user.company_name,
            sector=assessment.sector,
            overall_score=assessment.overall_score or 0,
            environment_score=assessment.environment_score or 0,
            social_score=assessment.social_score or 0,
            governance_score=assessment.governance_score or 0,
            strengths=assessment.strengths or [],
            gaps=assessment.gaps or [],
            benchmark_position=(benchmark or {}).get("position", "unknown"),
            user_id=str(user_id),
            assessment_id=str(assessment_id),  # PATCH-3 : metric Grafana correlable
        )

        # 6. Rendre le template HTML
        html_content = _render_html(
            assessment=assessment,
            user=user,
            executive_summary=executive_summary,
            radar_svg=radar_svg,
            pillar_bar_charts=pillar_bar_charts,
            benchmark_svg=benchmark_svg,
            pillar_criteria=pillar_criteria,
        )

        # 7. Convertir HTML -> PDF via WeasyPrint (buffer in-memory)
        from weasyprint import HTML

        buffer = BytesIO()
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(buffer)
        pdf_bytes = buffer.getvalue()

        # 8. Persister via storage provider (local ou S3)
        storage = get_storage_provider()
        storage_key = storage_key_for_report(report.id, file_name)
        await storage.put(storage_key, pdf_bytes, content_type="application/pdf")

        # 9. Mettre à jour le rapport (clé opaque stockée en BDD)
        report.file_path = storage_key
        report.file_size = len(pdf_bytes)
        report.status = ReportStatusEnum.completed
        report.generated_at = datetime.now(timezone.utc)
        await db.flush()

    except Exception:
        logger.exception("Erreur lors de la generation du rapport PDF")
        report.status = ReportStatusEnum.failed
        await db.flush()
        raise

    return report


async def get_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Report | None:
    """Recuperer un rapport par ID pour un utilisateur donne."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_report_any_user(
    db: AsyncSession,
    report_id: uuid.UUID,
) -> Report | None:
    """Recuperer un rapport par ID sans filtre utilisateur (pour verification ownership)."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def list_reports(
    db: AsyncSession,
    user_id: uuid.UUID,
    assessment_id: uuid.UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Report], int]:
    """Lister les rapports d'un utilisateur avec pagination."""
    query = select(Report).where(Report.user_id == user_id)

    if assessment_id:
        query = query.where(Report.assessment_id == assessment_id)

    # Compter le total
    from sqlalchemy import func

    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginer
    query = query.order_by(Report.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    reports = list(result.scalars().all())

    return reports, total
