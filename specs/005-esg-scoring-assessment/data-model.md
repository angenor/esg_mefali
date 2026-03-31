# Data Model: Evaluation et Scoring ESG Contextualise

**Feature**: 005-esg-scoring-assessment
**Date**: 2026-03-31

## Entites

### ESGAssessment

Represente une evaluation ESG complete pour une entreprise.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-genere | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL | Proprietaire de l'evaluation |
| conversation_id | UUID | FK → conversations.id, nullable | Conversation associee |
| version | Integer | NOT NULL, default 1 | Numero de version de l'evaluation |
| status | Enum | NOT NULL, default 'draft' | Statut : draft, in_progress, completed |
| sector | String | NOT NULL | Secteur evalue (copie depuis profil au moment de l'evaluation) |
| overall_score | Float | 0-100, nullable | Score global pondere |
| environment_score | Float | 0-100, nullable | Score pilier Environnement |
| social_score | Float | 0-100, nullable | Score pilier Social |
| governance_score | Float | 0-100, nullable | Score pilier Gouvernance |
| assessment_data | JSONB | nullable | Donnees detaillees : scores par critere, reponses, sources RAG |
| recommendations | JSONB | nullable | Liste de recommandations priorisees |
| strengths | JSONB | nullable | Points forts identifies |
| gaps | JSONB | nullable | Lacunes identifiees |
| sector_benchmark | JSONB | nullable | Benchmark sectoriel au moment de l'evaluation |
| current_pillar | String | nullable | Pilier en cours d'evaluation (environment, social, governance) |
| evaluated_criteria | JSONB | nullable, default [] | Liste des codes criteres deja evalues |
| created_at | Timestamp(tz) | NOT NULL, auto | Date de creation |
| updated_at | Timestamp(tz) | NOT NULL, auto | Date de derniere modification |

**Relations**:
- Appartient a un User (many-to-one)
- Associe optionnellement a une Conversation (many-to-one)

**Index**:
- `ix_esg_assessments_user_id` sur user_id
- `ix_esg_assessments_status` sur status

### Structure JSONB : assessment_data

```json
{
  "criteria_scores": {
    "E1": { "score": 7, "justification": "...", "sources": ["doc_id_1"] },
    "E2": { "score": 5, "justification": "...", "sources": [] },
    "S1": { "score": 8, "justification": "...", "sources": ["doc_id_2"] }
  },
  "pillar_details": {
    "environment": { "raw_score": 65, "weighted_score": 72, "weights_applied": {...} },
    "social": { "raw_score": 70, "weighted_score": 68, "weights_applied": {...} },
    "governance": { "raw_score": 55, "weighted_score": 58, "weights_applied": {...} }
  }
}
```

### Structure JSONB : recommendations

```json
[
  {
    "priority": 1,
    "criteria_code": "G3",
    "pillar": "governance",
    "title": "Formaliser une politique anti-corruption",
    "description": "...",
    "impact": "high",
    "effort": "medium",
    "timeline": "3-6 mois"
  }
]
```

### Structure JSONB : strengths

```json
[
  {
    "criteria_code": "E7",
    "pillar": "environment",
    "title": "Politique environnementale solide",
    "description": "...",
    "score": 9
  }
]
```

### Structure JSONB : sector_benchmark

```json
{
  "sector": "agriculture",
  "averages": {
    "environment": 52,
    "social": 48,
    "governance": 45,
    "overall": 48
  },
  "position": "above_average",
  "percentile": 72
}
```

## Donnees de reference (pas de table, configuration code)

### Criteres ESG (30)

Definis dans `modules/esg/criteria.py` comme constantes Python :

- **Environnement (E1-E10)** : Gestion dechets, Consommation energie, Emissions carbone, Ressources naturelles, Biodiversite, Gestion eau, Politique environnementale, Energies renouvelables, Transport vert, Economie circulaire
- **Social (S1-S10)** : Conditions travail, Egalite H/F, Formation, Impact communautaire, Sante securite, Remuneration, Inclusion diversite, Dialogue social, Fournisseurs locaux, Satisfaction employes
- **Gouvernance (G1-G10)** : Transparence financiere, Structure decision, Ethique anti-corruption, Conformite reglementaire, Politique anti-corruption, Gestion risques, Responsabilite dirigeant, Communication parties prenantes, Confidentialite donnees, Planification succession

### Ponderations sectorielles

Definies dans `modules/esg/weights.py`, dictionnaire par secteur avec poids par critere (default 1.0).

### Benchmarks sectoriels

Definis dans `modules/esg/weights.py`, moyennes E/S/G par secteur pour la zone UEMOA.

## Transitions d'etat

```
draft → in_progress → completed
  ↑         |
  └─────────┘ (reprise apres interruption)
```

- **draft** : Evaluation creee, pas encore de questions posees
- **in_progress** : Au moins un critere evalue, evaluation non terminee
- **completed** : Tous les criteres evalues, scores calcules

## Modification du ConversationState LangGraph

Ajout dans `graph/state.py` :

```
esg_assessment: dict | None  # Etat de l'evaluation ESG en cours
```

Contenu a runtime :
```json
{
  "assessment_id": "uuid",
  "status": "in_progress",
  "current_pillar": "social",
  "evaluated_criteria": ["E1", "E2", ..., "E10"],
  "partial_scores": { "E1": 7, "E2": 5, ... }
}
```
