"""Configuration des templates de sections par target_type."""

from app.models.application import TargetType

# Chaque template definit les sections du dossier, l'ordre, et les instructions de ton
# Structure : cle_section → {title, description, tone_instructions}

SECTION_TEMPLATES: dict[str, list[dict[str, str]]] = {
    TargetType.fund_direct: [
        {
            "key": "company_presentation",
            "title": "Présentation de l'entreprise",
            "description": "Historique, mission, activites, localisation, effectifs.",
            "tone": "Institutionnel, factuel. Mettre en avant la solidite et la credibilite de l'entreprise.",
        },
        {
            "key": "project_description",
            "title": "Description du projet",
            "description": "Objectifs, activites prevues, beneficiaires, zone d'intervention.",
            "tone": "Clair, structure. Aligner le projet sur les criteres du fonds.",
        },
        {
            "key": "environmental_impact",
            "title": "Impact environnemental",
            "description": "Benefices environnementaux, reduction emissions, ODD cibles.",
            "tone": "Technique mais accessible. Quantifier les impacts autant que possible.",
        },
        {
            "key": "financial_plan",
            "title": "Plan financier",
            "description": "Budget, sources de financement, calendrier de decaissement.",
            "tone": "Precis, chiffre. Montrer la viabilite financiere du projet.",
        },
        {
            "key": "annexes",
            "title": "Annexes",
            "description": "Liste des documents justificatifs a joindre.",
            "tone": "Factuel. Lister les pieces a fournir.",
        },
    ],
    TargetType.intermediary_bank: [
        {
            "key": "company_banking_history",
            "title": "Présentation de l'entreprise et historique bancaire",
            "description": "Presentation generale + relation bancaire, historique de credit, garanties existantes.",
            "tone": "Business case. Mettre en avant la solvabilite, l'historique de remboursement et la relation bancaire.",
        },
        {
            "key": "green_investment_project",
            "title": "Description du projet d'investissement vert",
            "description": "Projet detaille, retour sur investissement attendu, avantages concurrentiels.",
            "tone": "Oriente ROI et business case. Demontrer la rentabilite de l'investissement vert.",
        },
        {
            "key": "detailed_financial_plan",
            "title": "Plan financier détaillé",
            "description": "Plan de remboursement, garanties proposees, apport personnel, tresorerie previsionnelle.",
            "tone": "Bancaire, precis. Detailler les garanties, les ratios financiers et le plan de remboursement.",
        },
        {
            "key": "environmental_impact_expected",
            "title": "Impact environnemental attendu",
            "description": "Benefices environnementaux mesurables, conformite aux criteres verts de la ligne de credit.",
            "tone": "Factuel, quantifie. Aligner sur les criteres d'eligibilite verte de la banque.",
        },
        {
            "key": "financial_documents",
            "title": "Documents financiers",
            "description": "Bilans comptables, releves bancaires, declarations fiscales, business plan.",
            "tone": "Formel. Lister et decrire les documents financiers a fournir.",
        },
        {
            "key": "annexes",
            "title": "Annexes",
            "description": "Pieces complementaires : certificats, permis, etudes.",
            "tone": "Factuel. Lister les pieces a fournir.",
        },
    ],
    TargetType.intermediary_agency: [
        {
            "key": "project_holder_id",
            "title": "Fiche d'identification du porteur de projet",
            "description": "Identite juridique, gouvernance, experience, capacite de mise en oeuvre.",
            "tone": "Developpement. Mettre en avant l'ancrage local et la capacite institutionnelle.",
        },
        {
            "key": "national_alignment",
            "title": "Alignement priorités nationales et programme-pays",
            "description": "Coherence avec les plans nationaux, contributions aux ODD, priorites de l'agence.",
            "tone": "Strategique. Aligner le projet sur les priorites du programme-pays de l'agence.",
        },
        {
            "key": "technical_description",
            "title": "Description technique du projet",
            "description": "Methodologie, activites, chronogramme, parties prenantes.",
            "tone": "Technique, structure. Detailler la methodologie et le plan de mise en oeuvre.",
        },
        {
            "key": "budget_cofinancing",
            "title": "Budget et co-financement",
            "description": "Budget detaille, sources de co-financement, contributions en nature.",
            "tone": "Precis, transparent. Montrer les co-financements et la soutenabilite.",
        },
        {
            "key": "impact_indicators",
            "title": "Indicateurs d'impact mesurables",
            "description": "Cadre de resultats, indicateurs SMART, plan de suivi-evaluation.",
            "tone": "Rigoureux, mesurable. Utiliser des indicateurs quantifiables et verifiables.",
        },
    ],
    TargetType.intermediary_developer: [
        {
            "key": "project_methodology",
            "title": "Description du projet et méthodologie applicable",
            "description": "Description technique, methodologie de quantification (Gold Standard, Verra, REDD+).",
            "tone": "Technique, methodologique. Utiliser le vocabulaire des standards carbone.",
        },
        {
            "key": "emission_reductions",
            "title": "Estimation des réductions d'émissions",
            "description": "Baseline vs scenario projet, facteurs d'emission, calcul tCO2e evitees.",
            "tone": "Scientifique, quantifie. Detailler les calculs et hypotheses.",
        },
        {
            "key": "monitoring_plan",
            "title": "Plan de monitoring",
            "description": "Methodologie de mesure, frequence, outils, responsables.",
            "tone": "Rigoureux. Decrire le dispositif de suivi-mesure-verification (MRV).",
        },
        {
            "key": "additionality_analysis",
            "title": "Analyse d'additionnalité",
            "description": "Demonstration que le projet n'aurait pas eu lieu sans le financement carbone.",
            "tone": "Analytique. Argumenter l'additionnalite financiere et/ou technologique.",
        },
        {
            "key": "co_benefits",
            "title": "Co-bénéfices (ODD)",
            "description": "Co-benefices sociaux, economiques, environnementaux. Contribution aux ODD.",
            "tone": "Positif, structure. Mettre en valeur les impacts au-dela du carbone.",
        },
    ],
}

# Template generique (fallback)
GENERIC_TEMPLATE: list[dict[str, str]] = [
    {
        "key": "company_presentation",
        "title": "Présentation de l'entreprise",
        "description": "Historique, mission, activites, localisation.",
        "tone": "Factuel, institutionnel.",
    },
    {
        "key": "project_description",
        "title": "Description du projet",
        "description": "Objectifs, activites, beneficiaires.",
        "tone": "Clair et structure.",
    },
    {
        "key": "impact_assessment",
        "title": "Évaluation de l'impact",
        "description": "Impacts environnementaux et sociaux attendus.",
        "tone": "Quantifie et factuel.",
    },
    {
        "key": "financial_plan",
        "title": "Plan financier",
        "description": "Budget, sources de financement.",
        "tone": "Precis et chiffre.",
    },
    {
        "key": "annexes",
        "title": "Annexes",
        "description": "Documents justificatifs.",
        "tone": "Factuel.",
    },
]


def get_template_for_target(target_type: str) -> list[dict[str, str]]:
    """Retourner le template de sections pour un target_type donne."""
    return SECTION_TEMPLATES.get(target_type, GENERIC_TEMPLATE)


def initialize_sections(target_type: str) -> dict:
    """Initialiser les sections d'un dossier a not_generated."""
    template = get_template_for_target(target_type)
    return {
        section["key"]: {
            "title": section["title"],
            "content": None,
            "status": "not_generated",
            "updated_at": None,
        }
        for section in template
    }


# Checklists documentaires par target_type
CHECKLISTS: dict[str, list[dict[str, str]]] = {
    TargetType.fund_direct: [
        {"key": "company_registration", "name": "Registre de commerce (RCCM)", "required_by": "fund_direct"},
        {"key": "env_impact_study", "name": "Étude d'impact environnemental", "required_by": "fund_direct"},
        {"key": "project_budget", "name": "Budget détaillé du projet", "required_by": "fund_direct"},
        {"key": "financial_statements", "name": "États financiers (2 derniers exercices)", "required_by": "fund_direct"},
        {"key": "esg_report", "name": "Rapport d'évaluation ESG", "required_by": "fund_direct"},
    ],
    TargetType.intermediary_bank: [
        {"key": "company_registration", "name": "Registre de commerce (RCCM)", "required_by": "intermediary_bank"},
        {"key": "financial_statements", "name": "Bilans comptables (3 derniers exercices)", "required_by": "intermediary_bank"},
        {"key": "bank_statements", "name": "Relevés bancaires (12 derniers mois)", "required_by": "intermediary_bank"},
        {"key": "tax_declarations", "name": "Déclarations fiscales", "required_by": "intermediary_bank"},
        {"key": "business_plan", "name": "Business plan / plan d'affaires", "required_by": "intermediary_bank"},
        {"key": "collateral_docs", "name": "Documents de garanties (titres fonciers, nantissements)", "required_by": "intermediary_bank"},
        {"key": "env_impact_study", "name": "Étude d'impact environnemental", "required_by": "intermediary_bank"},
        {"key": "esg_report", "name": "Rapport d'évaluation ESG", "required_by": "intermediary_bank"},
    ],
    TargetType.intermediary_agency: [
        {"key": "company_registration", "name": "Registre de commerce (RCCM)", "required_by": "intermediary_agency"},
        {"key": "org_chart", "name": "Organigramme de l'organisation", "required_by": "intermediary_agency"},
        {"key": "project_proposal", "name": "Note conceptuelle du projet", "required_by": "intermediary_agency"},
        {"key": "budget_detailed", "name": "Budget détaillé avec co-financements", "required_by": "intermediary_agency"},
        {"key": "results_framework", "name": "Cadre de résultats et indicateurs", "required_by": "intermediary_agency"},
        {"key": "env_impact_study", "name": "Étude d'impact environnemental", "required_by": "intermediary_agency"},
    ],
    TargetType.intermediary_developer: [
        {"key": "project_design_doc", "name": "Document de conception du projet (PDD)", "required_by": "intermediary_developer"},
        {"key": "baseline_study", "name": "Étude de référence (baseline)", "required_by": "intermediary_developer"},
        {"key": "monitoring_methodology", "name": "Méthodologie de monitoring MRV", "required_by": "intermediary_developer"},
        {"key": "additionality_proof", "name": "Preuve d'additionnalité", "required_by": "intermediary_developer"},
        {"key": "stakeholder_consultation", "name": "Rapport de consultation des parties prenantes", "required_by": "intermediary_developer"},
    ],
}


def get_checklist_for_target(target_type: str) -> list[dict]:
    """Retourner la checklist documentaire pour un target_type donne."""
    items = CHECKLISTS.get(target_type, CHECKLISTS[TargetType.fund_direct])
    return [
        {**item, "status": "missing", "document_id": None}
        for item in items
    ]
