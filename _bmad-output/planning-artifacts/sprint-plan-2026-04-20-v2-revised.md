---
title: Sprint plan recalibré — v2 (post-6-stories-Phase-4)
type: sprint-plan
version: 2.0
status: validated
validated_date: 2026-04-20
validated_trigger: 6 stories Phase 4 livrées (9.6 + 9.7 + 10.1 + 10.2 + 10.3 + 10.4) avec vélocité 60-75% estimates L + 20-30% estimates M + 4 reviews consécutives sans CRITICAL + leçons capitalisées proactivement
author: Angenor (Project Lead, solo) + assistant Amelia
date: 2026-04-20
supersedes: sprint-plan-2026-04-19-v1-archived.md
revue_prevue: après 3-4 stories complexes Epic 11+ pour valider tenue ratio hors squelettes
---

# Sprint plan recalibré — v2 (2026-04-20)

## Résumé exécutif

Le sprint plan v1 du 2026-04-19 estimait **14 mois** pour Phase 0 + Phase 1 MVP sur base de points Fibonacci théoriques (374 pts sur 30 sprints de 2 semaines). Après livraison de **5 stories Phase 4** (9.6 + 9.7 + 10.1 + 10.2 + 10.3, Story 10.4 en cours), la vélocité mesurée converge autour de **60-75 % des estimates L** et **25-35 % des estimates M** pour les stories squelettes répétitives. Le recalibrage cible **10-11 mois** pour MVP complet, avec buffer préservé pour les stories métier complexes Epic 13+ (moteur DSL XL, SGES BETA, Cube 4D).

**Nouvelle cible go-live MVP** : **T+10 mois** (soit fin février 2027 si démarrage Sprint 0 mi-avril 2026), vs T+14 mois v1.

## Vélocité mesurée (base 5 stories Phase 4)

| Story | Type | Estimate | Durée réelle | Ratio réel/estimé | Tests ajoutés |
|---|---|---|---|---|---|
| **9.6** Guards LLM | Complexe | L (8-12h) | ~1 jour (~8h) | ~75 % | +56 |
| **9.7** Observabilité | Transverse | L (8-12h) | ~6h (dev) + 2h (patches post-BLOCK) | ~70 % | +56 |
| **10.1** Migrations Alembic 020-027 | Bloc schéma | L (8-12h) | ~1 jour (~8h) | ~75 % | +39 |
| **10.2** Module projects squelette | Module | M (5-8h) | 1h30 | ~20-30 % | +34 |
| **10.3** Module maturity squelette | Module | M (5-8h) | 55 min | ~15-20 % | +21 |
| **10.4** Module admin_catalogue (en cours) | Module | M | ~1h attendu | ~20 % projeté | +14-19 attendu |

**Observations** :
- **Stories squelettes modules (10.2+)** : ~1h avec pattern établi, gain énorme par duplication intelligente
- **Stories transverses/complexes (9.7, 10.1)** : ~6-8h, pattern non-duplicable
- **Stories avec review BLOCK (9.7)** : +2-4h de patches supplémentaires, à budgeter
- **Qualité stabilisée** : 0 CRITICAL depuis patches 9.7, leçons capitalisées story après story (9.7 C1/C2 → 10.2 → 10.3 → 10.4)

## Phase 0 restante projetée

**Périmètre** : Epic 9 résiduel (stories 9.8 à 9.15) + Epic 10 restant (stories 10.5 à 10.21) + Epic 19.1 (socle RAG refactor).

| Groupe | Nb stories | Type dominant | Durée unitaire moyenne | Durée cumulée |
|---|---|---|---|---|
| Epic 9 résiduel (9.8 à 9.15) | 8 | Mix (S/M/L) | ~2-4h | ~20-30h |
| Epic 10 stories modules squelettes restantes | ~5 | M squelette | ~1h | ~5h |
| Epic 10 stories infra (RLS, StorageProvider, envs, framework prompts, Outbox, sourcing, audit trail, Voyage bench XL) | ~11 | S/M/L/XL | ~3-6h | ~40-60h |
| Epic 10 stories UI foundation (10.14-10.21 Storybook, Button, Input, Badge, Drawer, Combobox, Tabs, DatePicker, Lucide) | ~8 | S/M | ~1-2h | ~10-15h |
| Epic 19.1 socle RAG refactor | 1 | L | ~8h | ~8h |
| **Total Phase 0 restante** | **~33** | — | — | **~80-120h** |

**Estimation calendaire Phase 0 restante** : **5-7 semaines** en continu à ~20h/semaine effective (solo + interruptions réelles). Si démarrage 2026-04-20 → fin Phase 0 **~T+6-8 semaines = début juin 2026**.

Vs v1 Phase 0 sur 9 sprints = 18 semaines. **Gain : 10-12 semaines sur Phase 0** seule.

## Phase 1 MVP projetée

**Périmètre** : Epics 11-18 (stories fonctionnelles) + Epic 19.2 (RAG cross-module) + Epic 20 (release engineering).

**Prudence requise** : les stories Phase 1 touchent au cœur métier (ESG 3 couches, Cube 4D, SGES BETA, Dashboard). Elles ne sont pas de simples duplications de pattern. Le ratio 70-75 % observé sur stories L doit tenir, mais avec variance possible.

| Epic | Nb stories | Complexité | Durée cumulée projetée |
|---|---|---|---|
| Epic 11 Cluster A PME (11.1-11.8) | 8 | Mix M/L | ~30-40h |
| Epic 12 Cluster A' Maturité (12.1-12.6) | 6 | Mix M/L | ~25-35h |
| Epic 13 Cluster B ESG 3 couches (13.1-13.11, 14 stories) | 14 | Mix M/L/XL (13.4a moteur DSL XL critique) | ~80-110h |
| Epic 14 Cube 4D (14.1-14.10) | 10 | Mix M/L | ~50-70h |
| Epic 15 Moteur livrables + SGES (15.1a/b - 15.9) | 10 | Mix L/XL (15.5 SGES BETA NO BYPASS 95% coverage critique) | ~60-90h |
| Epic 16 Copilot (16.1-16.6) | 6 | Mix M/L | ~25-35h |
| Epic 17 Dashboard (17.1-17.6) | 6 | Mix M/L | ~25-35h |
| Epic 18 Compliance (18.1-18.7) | 7 | Mix M/L (18.3 MFA step-up critique) | ~35-50h |
| Epic 19.2 RAG 5 modules | 1 | L | ~8h |
| Epic 20 Release engineering (20.1-20.4) | 4 | Mix S/L (20.2 load test, 20.4 audit WCAG externe) | ~20-30h |
| **Total Phase 1** | **~72** | — | **~360-510h** |

**Estimation calendaire Phase 1** : **15-22 semaines** en continu à ~24h/semaine effective. Si démarrage début juin 2026 → fin Phase 1 **~T+4-5 mois = octobre-novembre 2026**.

Vs v1 Phase 1 sur 21 sprints = 42 semaines. **Gain : 20-27 semaines sur Phase 1**.

## Nouvelle timeline MVP

| Jalon | Date v1 (14 mois) | Date v2 (10 mois) | Gain |
|---|---|---|---|
| Démarrage Sprint 0 | 2026-04-19 | 2026-04-19 | — |
| Fin Phase 0 | 2026-08-20 (Sprint 8) | **2026-06-15** (~Sprint 4-5) | ~2 mois |
| Mid-Phase 1 (ESG 3 couches + Cube 4D livrés) | — | **2026-09-30** | — |
| Fin Phase 1 MVP prête pilote | 2027-06-20 (Sprint 29) | **2027-02-15** | ~4 mois |
| Audit WCAG externe (Story 20.4) | Sprint 28 | **2027-01-20** | — |
| Trigger SC-B-PILOTE 15 k€ (consultants ESG AO) | Sprint 27-28 | **2026-12-15** | — |
| Pilote PME démarre | 2027-07 | **2027-03** | ~4 mois |

## Buffer et risques

**Buffer conservé explicitement** : 20 % sur la durée Phase 1 pour absorber :
- Stories métier complexes Epic 13 moteur DSL / Epic 15 SGES BETA (patterns non-duplicables)
- Éventuels BLOCK en review (pattern 9.7) nécessitant patches
- Interruptions réelles (vie personnelle, autres projets Angenor)
- Pivots ou ajustements UX suite aux retours pilote

**Scénario pessimiste** : si le ratio vélocité L descend à 100 % des estimates v1 sur Epic 13+ (stories complexes non-squelettes), la timeline revient vers **12 mois** plutôt que 10. Toujours gain de 2 mois vs v1.

**Scénario optimiste** : si le ratio 70-75 % tient sur toutes stories Epic 11+, timeline possible **8-9 mois**. Non engagée publiquement.

## Cible officielle de communication

**Cible publique et partenaires** : **10-11 mois pour MVP**, soit GTM cible **T+12 mois ± 1** (février à avril 2027).

Cette cible :
- Reste conservatrice (préserve crédibilité si pattern se dégrade Epic 13+)
- Aligne sur l'engagement PRD T+12m initial (cf. Option A glissement validé 2026-04-19)
- Permet de promettre moins et livrer mieux
- Active pilote SC-B-PILOTE plus tôt que prévu (gain confiance stakeholders)

## Chemin critique recalibré

Les dépendances du DAG initial restent valides. Seule la vitesse change.

```
Phase 0 (T+0 à T+2 mois) :
  9.7 ✅ → 10.1 ✅ → 10.5 RLS → 10.10 Outbox → 10.13 Voyage+bench →
  10.14-21 UI foundation → 19.1 RAG refactor
  Epic 9 résiduel (9.8-9.15) en parallèle

Phase 1 MVP (T+2 à T+10 mois) :
  Epic 11 Cluster A → Epic 12 Cluster A' →
  Epic 13 ESG 3 couches + Epic 14 Cube 4D (partiellement parallèles) →
  Epic 15 Moteur livrables + SGES →
  Epic 16 Copilot + Epic 17 Dashboard (parallèles post-13/14) →
  Epic 18 Compliance →
  Epic 19.2 RAG cross-module →
  Epic 20 Release engineering (fin Phase 1)

Fin Phase 1 (T+10 mois) :
  Audit WCAG externe Story 20.4 (4 k€)
  Pen test Story 20.3
  Load test Story 20.2
  Cleanup flag Story 20.1
  Trigger SC-B-PILOTE 15 k€ consultants ESG AO
  Pilote PME démarre (cf. business-decisions-2026-04-19.md)
```

## Budget re-confirmé

Pas de changement vs v1 :
- Budget pilote SC-B-PILOTE : **15 000 €** (cap bas fourchette PRD)
- Budget infra NFR69 : **1 000 €/mois cap MVP**
- Budget LLM NFR68 : **500 €/mois cap**
- Budget audit WCAG Story 20.4 : **4 000 €** (milieu fourchette 3-8 k€)
- **Total hors salaires** : ~20 k€ cash + infra 10-11 mois × 1 000 €/mois = **~30-32 k€** (vs 40 k€ v1, économie par raccourcissement).

## Points d'attention

1. **Story 10.4 en cours** : pattern 3ème duplication, attendre sa complétion pour confirmer que le ratio 20-30 % tient sur 3ème itération
2. **Stories XL à surveiller** : 13.4a moteur DSL, 15.1b intégration guards, 15.5 SGES BETA, 10.13 Voyage+bench LLM
3. **Stories avec audit externe** : 20.3 pen test (calendrier prestataire), 20.4 audit WCAG (prestataire FR/UE)
4. **SC-B-PILOTE dépend** de partenaire bailleur identifié. Sans partenariat Proparco/BAD/BOAD, budget différé même si timeline respectée
5. **Review modèle différent** reste obligatoire pour stories critiques (pattern 9.7 BLOCK évité par cette discipline)

## Historique

- **2026-04-19** — Sprint plan v1 produit (sprint-plan-2026-04-19.md) : 14 mois / 374 pts Fibonacci / 30 sprints
- **2026-04-20** — Sprint plan v2 (ce fichier) : 10-11 mois cible, basé sur vélocité mesurée 5 stories Phase 4 + qualité stabilisée
- **À prévoir** — v3 après 3-4 stories Epic 11+ pour valider tenue ratio sur stories métier complexes
