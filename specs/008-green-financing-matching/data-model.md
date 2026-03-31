# Data Model: 008-green-financing-matching

**Date**: 2026-03-31

## Entites

### Fund (table: `funds`)

| Champ | Type | Contraintes | Description |
|-------|------|------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| name | String(255) | NOT NULL | Nom du fonds |
| organization | String(255) | NOT NULL | Organisation gestionnaire |
| fund_type | Enum(FundType) | NOT NULL | international, regional, national, carbon_market, local_bank_green_line |
| description | Text | NOT NULL | Description detaillee |
| website_url | String(500) | nullable | Site web officiel |
| contact_info | JSONB | nullable | Coordonnees de contact |
| eligibility_criteria | JSONB | NOT NULL, default={} | Criteres d'eligibilite structures |
| sectors_eligible | JSONB | NOT NULL, default=[] | Liste des secteurs eligibles |
| min_amount_xof | BigInteger | nullable | Montant minimum en FCFA |
| max_amount_xof | BigInteger | nullable | Montant maximum en FCFA |
| application_deadline | Date | nullable | Date limite de candidature |
| required_documents | JSONB | NOT NULL, default=[] | Documents requis pour candidater |
| esg_requirements | JSONB | NOT NULL, default={} | Exigences ESG (score min, criteres) |
| status | Enum(FundStatus) | NOT NULL, default=active | active, closed, upcoming |
| access_type | Enum(AccessType) | NOT NULL | direct, intermediary_required, mixed |
| intermediary_type | Enum(IntermediaryType) | nullable | Type d'intermediaire requis |
| application_process | JSONB | NOT NULL, default=[] | Etapes du parcours de candidature |
| typical_timeline_months | Integer | nullable | Duree typique du processus |
| success_tips | Text | nullable | Conseils pour maximiser les chances |
| created_at | DateTime | auto | Date de creation |
| updated_at | DateTime | auto | Date de derniere modification |

### Intermediary (table: `intermediaries`)

| Champ | Type | Contraintes | Description |
|-------|------|------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| name | String(255) | NOT NULL | Nom de l'intermediaire |
| intermediary_type | Enum(IntermediaryType) | NOT NULL | accredited_entity, partner_bank, implementation_agency, project_developer, national_agency |
| organization_type | Enum(OrganizationType) | NOT NULL | bank, development_bank, un_agency, ngo, government_agency, consulting_firm, carbon_developer |
| description | Text | nullable | Description de l'intermediaire |
| country | String(100) | NOT NULL | Pays |
| city | String(100) | NOT NULL | Ville |
| website_url | String(500) | nullable | Site web |
| contact_email | String(255) | nullable | Email de contact |
| contact_phone | String(50) | nullable | Telephone |
| physical_address | Text | nullable | Adresse physique complete |
| accreditations | JSONB | NOT NULL, default=[] | Fonds pour lesquels accredite |
| services_offered | JSONB | NOT NULL, default={} | Services proposes |
| typical_fees | Text | nullable | Description des frais |
| eligibility_for_sme | JSONB | NOT NULL, default={} | Criteres d'eligibilite PME |
| rating | Float | nullable | Note (usage futur) |
| is_active | Boolean | NOT NULL, default=True | Actif ou non |
| created_at | DateTime | auto | Date de creation |
| updated_at | DateTime | auto | Date de derniere modification |

### FundIntermediary (table: `fund_intermediaries`)

| Champ | Type | Contraintes | Description |
|-------|------|------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| fund_id | UUID | FK → funds, NOT NULL | Fonds lie |
| intermediary_id | UUID | FK → intermediaries, NOT NULL | Intermediaire lie |
| role | Text | nullable | Role specifique pour ce fonds |
| is_primary | Boolean | NOT NULL, default=False | Intermediaire principal recommande |
| geographic_coverage | JSONB | NOT NULL, default=[] | Zones geographiques couvertes |
| notes | Text | nullable | Notes complementaires |

**Contrainte unique** : (fund_id, intermediary_id)

### FundMatch (table: `fund_matches`)

| Champ | Type | Contraintes | Description |
|-------|------|------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| user_id | UUID | FK → users, NOT NULL | Utilisateur concerne |
| fund_id | UUID | FK → funds, NOT NULL | Fonds matche |
| compatibility_score | Integer | NOT NULL, check 0-100 | Score de compatibilite |
| matching_criteria | JSONB | NOT NULL, default={} | Criteres utilises pour le matching |
| missing_criteria | JSONB | NOT NULL, default={} | Criteres manquants |
| recommended_intermediaries | JSONB | NOT NULL, default=[] | Intermediaires recommandes (IDs + noms) |
| access_pathway | JSONB | NOT NULL, default={} | Parcours d'acces complet |
| estimated_timeline_months | Integer | nullable | Duree estimee du processus |
| status | Enum(MatchStatus) | NOT NULL, default=suggested | suggested, interested, contacting_intermediary, applying, submitted, accepted, rejected |
| contacted_intermediary_id | UUID | FK → intermediaries, nullable | Intermediaire choisi |
| created_at | DateTime | auto | Date de creation |

**Contrainte unique** : (user_id, fund_id) — un seul match par utilisateur par fonds

### FinancingChunk (table: `financing_chunks`)

| Champ | Type | Contraintes | Description |
|-------|------|------------|-------------|
| id | UUID | PK, auto | Identifiant unique |
| source_type | Enum(FinancingSourceType) | NOT NULL | fund, intermediary |
| source_id | UUID | NOT NULL | ID du fonds ou de l'intermediaire |
| content | Text | NOT NULL | Texte du chunk |
| embedding | Vector(1536) | nullable | Embedding pgvector |
| created_at | DateTime | auto | Date de creation |

**Index HNSW** : sur `embedding` avec `vector_cosine_ops`

## Enumerations

```
FundType: international, regional, national, carbon_market, local_bank_green_line
FundStatus: active, closed, upcoming
AccessType: direct, intermediary_required, mixed
IntermediaryType: accredited_entity, partner_bank, implementation_agency, project_developer, national_agency
OrganizationType: bank, development_bank, un_agency, ngo, government_agency, consulting_firm, carbon_developer
MatchStatus: suggested, interested, contacting_intermediary, applying, submitted, accepted, rejected
FinancingSourceType: fund, intermediary
```

## Relations

```
Fund 1──N FundIntermediary N──1 Intermediary
Fund 1──N FundMatch N──1 User
FundMatch N──1 Intermediary (contacted_intermediary_id, nullable)
Fund 1──N FinancingChunk (source_type=fund)
Intermediary 1──N FinancingChunk (source_type=intermediary)
```

## Transitions d'etat — FundMatch.status

```
suggested → interested → contacting_intermediary → applying → submitted → accepted
                                                                        → rejected
```

Toutes les transitions sont unidirectionnelles sauf :
- `rejected` : peut retourner a `interested` (nouvelle tentative)
