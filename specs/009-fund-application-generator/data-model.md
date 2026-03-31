# Data Model — 009 Fund Application Generator

**Date**: 2026-03-31

## Entites

### FundApplication (table: `fund_applications`)

Dossier de candidature a un fonds vert, adapte au destinataire.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL, INDEX | Proprietaire du dossier |
| fund_id | UUID | FK → funds.id, NOT NULL, INDEX | Fonds vise |
| match_id | UUID | FK → fund_matches.id, NULLABLE | Match a l'origine du dossier |
| intermediary_id | UUID | FK → intermediaries.id, NULLABLE | Intermediaire choisi (si acces intermediaire) |
| target_type | Enum | NOT NULL | Type de destinataire : fund_direct, intermediary_bank, intermediary_agency, intermediary_developer |
| status | Enum | NOT NULL, DEFAULT draft | Statut du parcours (voir machine a etats ci-dessous) |
| sections | JSONB | NOT NULL, DEFAULT {} | Contenu des sections (cle → {title, content, status, updated_at}) |
| checklist | JSONB | NOT NULL, DEFAULT [] | Documents requis ({name, status, document_id?, required_by}) |
| intermediary_prep | JSONB | NULLABLE | Donnees fiche de preparation intermediaire |
| simulation | JSONB | NULLABLE | Resultats du simulateur de financement |
| created_at | DateTime(tz) | NOT NULL, DEFAULT now() | Date de creation |
| updated_at | DateTime(tz) | NOT NULL, DEFAULT now(), ON UPDATE | Derniere modification |
| submitted_at | DateTime(tz) | NULLABLE | Date de soumission |

**Index** : `ix_fund_applications_user_id` sur user_id.

### Enumerations

#### TargetType

| Valeur | Description |
|--------|-------------|
| fund_direct | Candidature directe aupres du fonds |
| intermediary_bank | Via une banque partenaire (ton bancaire, solvabilite) |
| intermediary_agency | Via une agence d'implementation (ton developpement) |
| intermediary_developer | Via un developpeur de projets carbone (ton technique) |

#### ApplicationStatus

| Valeur | Description | Parcours |
|--------|-------------|----------|
| draft | Brouillon initial | Direct + Intermediaire |
| preparing_documents | Preparation des documents | Direct + Intermediaire |
| in_progress | Redaction en cours | Direct + Intermediaire |
| review | Relecture | Direct + Intermediaire |
| ready_for_intermediary | Pret pour l'intermediaire | Intermediaire uniquement |
| ready_for_fund | Pret pour soumission au fonds | Direct uniquement |
| submitted_to_intermediary | Soumis a l'intermediaire | Intermediaire uniquement |
| submitted_to_fund | Soumis au fonds | Direct + Intermediaire |
| under_review | En cours d'examen | Direct + Intermediaire |
| accepted | Accepte | Direct + Intermediaire |
| rejected | Rejete | Direct + Intermediaire |

## Machine a etats (statut)

### Parcours direct (fund_direct)

```
draft → preparing_documents → in_progress → review → ready_for_fund → submitted_to_fund → under_review → accepted/rejected
```

### Parcours intermediaire (intermediary_*)

```
draft → preparing_documents → in_progress → review → ready_for_intermediary → submitted_to_intermediary → submitted_to_fund → under_review → accepted/rejected
```

## Structure JSONB sections

```json
{
  "company_presentation": {
    "title": "Presentation de l'entreprise",
    "content": "<html content>",
    "status": "generated",
    "updated_at": "2026-03-31T10:00:00Z"
  },
  "project_description": {
    "title": "Description du projet",
    "content": null,
    "status": "not_generated",
    "updated_at": null
  }
}
```

Statuts de section : `not_generated`, `generated`, `validated`.

## Structure JSONB checklist

```json
[
  {
    "key": "financial_statements",
    "name": "Bilans comptables (3 derniers exercices)",
    "status": "missing",
    "document_id": null,
    "required_by": "intermediary_bank"
  },
  {
    "key": "env_impact_study",
    "name": "Etude d'impact environnemental",
    "status": "provided",
    "document_id": "uuid-du-document",
    "required_by": "fund_direct"
  }
]
```

## Structure JSONB intermediary_prep

```json
{
  "company_summary": "Texte resume 1 page...",
  "esg_score": { "total": 72, "strengths": ["..."], "weaknesses": ["..."] },
  "carbon_summary": { "total_tco2e": 150, "main_sources": ["..."] },
  "fund_eligibility": { "fund_name": "SUNREF", "why_eligible": "..." },
  "available_documents": ["Bilan 2024", "Rapport ESG"],
  "questions_to_ask": ["Question 1", "...", "Question 5"],
  "generated_at": "2026-03-31T10:00:00Z"
}
```

## Structure JSONB simulation

```json
{
  "eligible_amount_xof": 50000000,
  "roi_green": { "annual_savings_xof": 12000000, "payback_months": 50 },
  "timeline": [
    { "step": "Preparation du dossier", "duration_weeks": "2-4" },
    { "step": "Traitement par la banque", "duration_weeks": "2-4" },
    { "step": "Soumission au fonds", "duration_weeks": "1-2" },
    { "step": "Examen par le fonds", "duration_weeks": "8-16" }
  ],
  "carbon_impact_tco2e": 85,
  "intermediary_fees_xof": 2500000,
  "estimated_at": "2026-03-31T10:00:00Z"
}
```

## Relations

- FundApplication → Fund (N:1 via fund_id)
- FundApplication → User (N:1 via user_id)
- FundApplication → FundMatch (N:1 via match_id, optionnel)
- FundApplication → Intermediary (N:1 via intermediary_id, optionnel)

## Templates de sections par target_type

### fund_direct
1. company_presentation — Presentation de l'entreprise
2. project_description — Description du projet
3. environmental_impact — Impact environnemental
4. financial_plan — Plan financier
5. annexes — Annexes

### intermediary_bank
1. company_banking_history — Presentation de l'entreprise et historique bancaire
2. green_investment_project — Description du projet d'investissement vert
3. detailed_financial_plan — Plan financier detaille (remboursement, garanties, apport)
4. environmental_impact_expected — Impact environnemental attendu
5. financial_documents — Documents financiers (bilans, releves, fiscal)
6. annexes — Annexes

### intermediary_agency
1. project_holder_id — Fiche d'identification du porteur de projet
2. national_alignment — Alignement priorites nationales et programme-pays
3. technical_description — Description technique du projet
4. budget_cofinancing — Budget et co-financement
5. impact_indicators — Indicateurs d'impact mesurables

### intermediary_developer
1. project_methodology — Description du projet et methodologie applicable
2. emission_reductions — Estimation des reductions d'emissions (baseline vs projet)
3. monitoring_plan — Plan de monitoring
4. additionality_analysis — Analyse d'additionnalite
5. co_benefits — Co-benefices (ODD)

### generic (fallback)
1. company_presentation — Presentation de l'entreprise
2. project_description — Description du projet
3. impact_assessment — Evaluation de l'impact
4. financial_plan — Plan financier
5. annexes — Annexes
