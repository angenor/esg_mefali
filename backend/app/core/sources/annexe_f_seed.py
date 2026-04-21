"""Seed Annexe F — 22 sources officielles ESG/financement vert.

Référence : `_bmad-output/planning-artifacts/prd.md#Annexe F`.

Source unique de vérité (Story 10.11, règle 10.5 « pas de duplication ») :
la migration `030_seed_sources_annexe_f.py` importe `ANNEXE_F_SOURCES` sans
répliquer les URLs. Pattern CCC-9 (Story 10.8) : tuple frozen + validation
unicité import-time.

Aucune URL ne porte le préfixe `legacy://` : ces sentinelles sont réservées
aux lignes existantes backfillées par la migration 025, exclues du scan
nightly via la clause `NOT LIKE 'legacy://%'`.
"""

from __future__ import annotations

from typing import Final

from app.core.sources.types import SourceSeed


def _validate_unique_urls(seeds: tuple[SourceSeed, ...]) -> None:
    """Garantit l'unicité des URLs (fail-fast import-time).

    Pattern CCC-9 Story 10.8 (cf. `registry._validate_unique_names`).
    Lève `ValueError` si une URL apparaît plus d'une fois — on ne peut
    pas insérer 2 lignes avec la contrainte `UniqueConstraint("url")`
    du modèle `sources`.
    """

    seen: set[str] = set()
    for seed in seeds:
        if seed.url in seen:
            raise ValueError(f"duplicate URL in ANNEXE_F_SOURCES: {seed.url}")
        seen.add(seed.url)


ANNEXE_F_SOURCES: Final[tuple[SourceSeed, ...]] = (
    # ---------- Bailleurs climat / DFI ----------
    SourceSeed(
        url="https://www.greenclimate.fund/projects",
        source_type="web",
        description="Green Climate Fund — portefeuille projets",
    ),
    SourceSeed(
        url="https://www.thegef.org/projects-operations/database",
        source_type="web",
        description="Global Environment Facility — base projets",
    ),
    SourceSeed(
        url="https://www.proparco.fr/fr/nos-engagements-esg",
        source_type="web",
        description="Proparco (AFD) — engagements ESG",
    ),
    SourceSeed(
        url="https://www.boad.org/wp-content/uploads/upload/SSI_BOAD.pdf",
        source_type="pdf",
        description="BOAD — Système de Sauvegarde Intégré",
    ),
    SourceSeed(
        url="https://www.afdb.org/en/documents/integrated-safeguards-system",
        source_type="web",
        description="Banque africaine de développement — Integrated Safeguards",
    ),
    SourceSeed(
        url="https://www.worldbank.org/en/projects-operations/environmental-and-social-framework",
        source_type="web",
        description="Banque mondiale — Environmental and Social Framework (ESF)",
    ),
    SourceSeed(
        url="https://www.ifc.org/en/insights-reports/2012/publications-handbook-dfi-harmonized-project",
        source_type="regulation",
        description="DFI — Harmonized Indicators for Private Sector Operations",
    ),
    # ---------- Certifications sectorielles ----------
    SourceSeed(
        url="https://www.rainforest-alliance.org/business/certification/",
        source_type="web",
        description="Rainforest Alliance — certification agriculture durable",
    ),
    SourceSeed(
        url="https://www.fairtrade.net/standard",
        source_type="web",
        description="Fairtrade International — standards certifiés",
    ),
    SourceSeed(
        url="https://www.bonsucro.com/production-standard/",
        source_type="web",
        description="Bonsucro — standard de production canne à sucre",
    ),
    SourceSeed(
        url="https://fsc.org/en/fsc-standards",
        source_type="web",
        description="Forest Stewardship Council — standards forestiers",
    ),
    SourceSeed(
        url="https://responsiblemining.net/what-we-do/standard/",
        source_type="web",
        description="IRMA — Initiative for Responsible Mining Assurance",
    ),
    SourceSeed(
        url="https://www.responsiblesteel.org/standard/",
        source_type="web",
        description="ResponsibleSteel — standard acier responsable",
    ),
    # ---------- Reporting ESG / climat ----------
    SourceSeed(
        url="https://www.globalreporting.org/standards/",
        source_type="regulation",
        description="GRI — Global Reporting Initiative Standards",
    ),
    SourceSeed(
        url="https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/",
        source_type="regulation",
        description="TCFD / ISSB — IFRS Sustainability Disclosure Standards",
    ),
    SourceSeed(
        url="https://www.cdp.net/en/guidance",
        source_type="web",
        description="CDP — guidance disclosure climat/eau/forêts",
    ),
    SourceSeed(
        url="https://sasb.ifrs.org/standards/",
        source_type="regulation",
        description="SASB — Sustainability Accounting Standards (IFRS)",
    ),
    SourceSeed(
        url="https://iris.thegiin.org/metrics/",
        source_type="web",
        description="GIIN IRIS+ — métriques impact",
    ),
    # ---------- Transparence / gouvernance ----------
    SourceSeed(
        url="https://eiti.org/documents/eiti-standard",
        source_type="regulation",
        description="ITIE / EITI — standard transparence industries extractives",
    ),
    SourceSeed(
        url="https://www.sedex.com/our-services/smeta-audit/",
        source_type="web",
        description="Sedex / SMETA — audit social 4 piliers",
    ),
    SourceSeed(
        url="https://ecovadis.com/suppliers/",
        source_type="web",
        description="EcoVadis — évaluation RSE fournisseurs",
    ),
    SourceSeed(
        url="https://sa-intl.org/programs/sa8000/",
        source_type="regulation",
        description="SA8000 — norme internationale travail décent",
    ),
)


_validate_unique_urls(ANNEXE_F_SOURCES)
