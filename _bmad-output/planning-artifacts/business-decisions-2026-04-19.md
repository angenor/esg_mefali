---
title: Décisions business quantifiées — atelier solo 2026-04-19
type: business-decisions
status: validated
author: Angenor (solo)
date: 2026-04-19
scope: quantification des items `[à quantifier]` PRD + arbitrage R-04-1 readiness check
consommateurs:
  - /bmad-sprint-planning (priorisation stories Epic 20 + budget infra)
  - /bmad-dev-story (AC Story 10.13, 17.5, 20.4)
  - atelier stakeholders business post-pilote (révision valeurs selon données terrain)
revue_prevue: après 3 mois pilote ou à GTM MVP (selon premier événement)
---

# Décisions business quantifiées — atelier solo 2026-04-19

Quantification des 4 items PRD marqués `[à quantifier]` + 3 items budget + arbitrage R-04-1 du readiness check 2026-04-19. Décisions prises en mode solo par le Project Lead, révisables à la lumière des données terrain pilote.

## Contexte

Le PRD (ligne 102) prévoit un atelier stakeholders business avant GTM MVP pour quantifier SC-B1, SC-B5, SC-B6, MO-5. En mode solo avec contrainte temps, les valeurs par défaut défendables ci-dessous débloquent le sprint planning. Elles seront révisées après 3 mois de données pilote ou avant GTM si partenaires institutionnels apportent leurs propres métriques.

## Valeurs quantifiées

### SC-B1 — Adoption cible T+12 mois post-MVP

**Valeur retenue : 200 utilisateurs actifs mensuels (MAU)**

Composition attendue :
- 150 PME accompagnées directement
- 50 consultants ESG / accompagnateurs institutionnels agissant pour compte de PME

Justification :
- Démarrage solo + 1 pays pilote (SN ou CI à trancher) + 1-2 partenariats institutionnels
- Benchmark SaaS B2B compliance AO : croissance organique lente sans force commerciale
- 200 MAU = objectif réaliste avec canal partenaire (coopératives, chambres de commerce, BAD/Proparco programmes PME)

**Conditions de révision** :
- À la hausse (300-500 MAU) si : 2+ pays MVP OR partenariat Proparco/BAD signé avec engagement volume
- À la baisse (100 MAU) si : pas de partenariat institutionnel actif à T+3 mois post-MVP

### SC-B5 — Revenus d'abonnement sur cohorte pilote

**Valeur retenue : freemium MVP, monétisation différée Phase Growth**

Modalités MVP :
- 100 % gratuit pour PME pilotes
- Modèle B2B indirect validé : Proparco / BAD / coopérative paie l'accès pour X PME accompagnées

Modalités Phase Growth (cible T+12 mois) :
- 10-30 €/mois par PME OHADA niveau 2-3
- OU B2B2C via intermédiaires (SIB / Ecobank paient pour leurs PME clientes)

**Métrique pilote opérationnelle** :
*"Modèle économique validé sur 50 PME pilotes avec au moins 1 partenaire payant identifié à T+9 mois post-MVP."*

### SC-B6 — Rétention à 6 mois

**Valeur retenue : 60 %**

Définition : 60 % des PME ayant complété au moins un dossier (FundApplication signée et exportée) reviennent à 6 mois pour :
- Suivi du statut du dossier soumis
- Nouvelle évaluation ESG annuelle
- Préparation d'un nouveau projet
- Consultation du plan d'action

Justification :
- Cycle formalisation + ESG = 3-6 mois → users reviennent naturellement pour suivi
- Benchmark SaaS B2B compliance : 50-70 % rétention 6 mois
- 60 % = cible ambitieuse mais réaliste, positionne Mefali comme outil de référence récurrent

### MO-5 — Taux de passage de niveau formalisation

**Valeur retenue : 40 % passage niveau 0 → 1 à 6 mois, 20 % passage niveau 1 → 2 à 12 mois**

Périmètre : users "activement accompagnés" uniquement (exclut les lurkers, définis comme users sans interaction chat depuis > 30 jours).

Justification :
- Niveau 0 → 1 (RCCM + NINEA) : coût 100-150k FCFA + démarches 2-3 semaines → 40 % réaliste avec accompagnement FormalizationPlan + rappels FR54 + coordonnées locales précises
- Niveau 1 → 2 (caisse sociale + 1er bilan) : plus exigeant → 20 % à 12 mois

**Risque associé** : RI-5 PRD (formalisation graduée, taux bas). Mitigation : chiffrage exact FCFA + rappels auto + partenariats cabinets comptables locaux Phase Growth.

### SC-B-PILOTE — Budget pilote

**Valeur retenue : 15 000 € total** (cap bas de la fourchette PRD 15-30 k€)

Décomposition :
| Poste | Budget | Notes |
|---|---|---|
| Consultants ESG AO seniors | 10 000 € | 10 jours-expert × 1 500 €/j pour sourcing catalogue Phase 0 + validation pilote Phase 1 fin |
| Support PME pilotes | 3 000 € | Assistance tech, formation onboarding, hotline email/WhatsApp |
| Incentives utilisateurs pilotes | 2 000 € | Bonus complétion dossier (voucher, airtime, goodies) pour 20-50 PME pilotes |

**Exclusions** : chargé bailleur régional = gratuit (intérêt mutuel à valider). Budget complémentaire si bailleur exige revue payante.

**Conditions d'activation** : budget débloqué quand partenaire bailleur identifié (Proparco, BAD, BOAD, ou équivalent).

### NFR68 — Budget LLM mensuel

**Valeur retenue : 500 €/mois cap MVP, alerting 400 €/500 € (warning/critical)**

Volumétrie estimée :
- 200 MAU × 30 appels LLM/mois × coût moyen 0.01-0.05 € (Claude via OpenRouter) = 60-300 €/mois
- Buffer sécurité + pics d'usage + tools batch (batch_save_esg_criteria, batch_save_emission_entries) = 500 €/mois cap

Alerting Story 17.5 (déjà prévu) :
- **Warning à 400 €/mois** (80 % du cap) → review ops, identifier users/tools outliers
- **Critical à 500 €/mois** (100 % cap) → throttling automatique, alert ops email + Sentry

**Révision** : après 3 mois production avec données volumétrie réelles. Peut descendre à 300 € ou monter à 800 € selon usage observé.

### NFR69 — Budget infrastructure MVP

**Valeur retenue : 1 000 €/mois cap MVP** (cap bas de la fourchette PRD 800-2000 €)

Décomposition indicative :
| Poste | Budget mensuel | Notes |
|---|---|---|
| AWS ECS Fargate compute | 200-300 € | 2 tâches MVP |
| AWS RDS PostgreSQL t3.micro + pgvector | 100-200 € | 1 instance PROD + STAGING t3.micro |
| S3 + CRR EU-West-3 → EU-West-1 + CloudFront | 100 € | Documents + embeddings + backup |
| Mailgun | 50-100 € | Transactionnel + notifications critiques |
| Sentry + monitoring | 100-200 € | Error tracking + observabilité |
| AWS Secrets Manager + KMS | 50 € | Secrets + chiffrement at rest |
| Buffer (DNS, divers) | 100-200 € | Marge d'imprévus |

**Review trimestrielle** : ajustement selon volumétrie réelle. Upgrade RDS + ECS déclenché par traction (≥ 500 MAU).

### Story 20.4 — Audit WCAG externe

**Valeur retenue : 4 000 € cap** (milieu de la fourchette readiness 3-8 k€)

Périmètre :
- Prestataire FR / UE mid-range certifié RGAA / WCAG 2.1 AA
- Scope : 5 journeys personas + 8 composants à gravité Storybook
- Livrables : audit initial + rapport + re-test post-corrections
- Exclut : corrections code (internes Angenor)

**Planning** : Phase 1 fin (avant go-live MVP), cohérent avec Story 20.4 repositionnée au Lot 7 validation epics.

## Arbitrage R-04-1 — Bench 3 providers LLM

**Décision retenue : AC9 ajouté à Story 10.13 (pas de nouvelle Story 10.22)**

Scope du bench :

**Providers benchmarkés** :
- **(a) Anthropic via OpenRouter** — baseline si migration vers Claude
- **(b) Anthropic direct** (api.anthropic.com) — vérifier si l'absence d'intermédiaire OpenRouter améliore latence / coût
- **(c) MiniMax (`minimax/minimax-m2.7`) via OpenRouter** — baseline actuelle `.env` du projet, valide si MiniMax tient la charge vs Claude

**Tools benchmarkés (5)** :
1. `generate_formalization_plan` (Aminata niveau 0 first-wow — JSON structuré avec coordonnées locales)
2. `query_cube_4d` (matching projet-financement — logique complexe + RAG)
3. `derive_verdicts_multi_ref` (ESG 3 couches — DSL borné + multi-référentiels)
4. `generate_action_plan` (JSON structuré 10+ actions multi-catégories avec guards)
5. `generate_executive_summary` (texte long livrable bailleur PDF avec guards)

**Métriques mesurées** :
- Latence p95 / p99 par tool call
- Coût par tool call (€ / 1000 tokens input + output)
- Qualité output via revue manuelle 10 échantillons par tool × 3 providers = 150 échantillons scorés sur 4 axes :
  - Respect format structuré (Pydantic schema valid)
  - Cohérence numérique avec données source (pas d'hallucination chiffres)
  - Respect vocabulaire interdit (guards LLM 9.6)
  - Qualité rédactionnelle FR avec accents (é è ê à ç ù)

**Livrable** : `docs/bench-llm-providers-phase0.md` avec recommandation provider primaire MVP + fallback configuré dans `EmbeddingProvider` / `LLMProvider` abstraction (décision D10 architecture).

**Décision finale** actée avant Sprint 1 Phase 1.

**Impact Story 10.13** : estimate ajusté **L → XL** pour absorber les ~2 jours de dev supplémentaires (bench script + 150 échantillons qualité + rapport + recommandation).

## Traçabilité

| Décision | Valeur 2026-04-19 | Consommé par | Révision |
|---|---|---|---|
| SC-B1 adoption | 200 MAU T+12m | Sprint planning priorisation Epic 17 dashboard | Après 3 mois pilote |
| SC-B5 revenus | freemium MVP | Aucune story MVP (Phase Growth) | Phase Growth |
| SC-B6 rétention | 60 % à 6 mois | Story 17.6 alerting anomalies (baseline) | Après 6 mois pilote |
| MO-5 passage niveau | 40 % à 6 mois, 20 % à 12 mois | Story 17.5 monitoring | Après 6 mois pilote |
| SC-B-PILOTE budget | 15 k€ | Planning GTM hors BMAD | À activation partenaire |
| NFR68 budget LLM | 500 €/mois cap | Story 17.5 budget projection + 17.6 alerting | Après 3 mois production |
| NFR69 budget infra | 1 000 €/mois cap | Story 10.7 env + 10.6 storage + ops | Trimestrielle |
| Story 20.4 audit WCAG | 4 k€ | Story 20.4 AC | GTM MVP |
| R-04-1 bench LLM | AC9 dans Story 10.13 | Story 10.13 amendment | Rapport Phase 0 |

## Prochaines actions

1. **Amendment Story 10.13 dans `epics.md`** : ajouter AC9 bench + réestimer L → XL
2. **Lancer `/bmad-sprint-planning`** en contexte frais avec ce document comme input
3. **Revoir les valeurs** après 3 mois pilote ou à GTM MVP (premier événement)

## Historique

- **2026-04-19** — Création en mode solo par Angenor. Validé avec assistant Amelia.
- **À venir** — Révision post-pilote 3 mois OR atelier stakeholders si partenaire institutionnel signe avec métriques propres.
