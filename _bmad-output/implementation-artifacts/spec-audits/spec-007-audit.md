# Audit Rétrospectif — Spec 007 : Calculateur d'Empreinte Carbone Conversationnel

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/007-carbon-footprint-calculator/](../../../specs/007-carbon-footprint-calculator/)
**Méthode** : rétrospective post-hoc + audit-tasks-discordance
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Bilan carbone annuel conversationnel, facteurs d'émission Afrique de l'Ouest, visualisations progressives (chart/donut/gauge/timeline), plan de réduction FCFA, benchmark sectoriel, historique multi-années.

| Dimension | Livré |
|-----------|-------|
| Tâches | 41 / 41 `[X]` (100 %) — toutes vérifiées ✅ |
| Discordance tasks↔code | 0 (audit croisé OK) |
| User Stories | 5 (US1 P1, US2-US3 P2, US4-US5 P3) |
| Nouveaux modèles | `CarbonAssessment`, `CarbonEmissionEntry` |
| Facteurs d'émission | 7+ (électricité CI, essence, gasoil, butane, etc.) + conversions FCFA |
| Secteurs benchmarkés | 8 (agriculture, agroalimentaire, energie, transport, services, commerce, artisanat, textile) |
| CLAUDE.md mentionne | "57 tests" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture saine

- `carbon_node` + `CARBON_TOOLS` coexistent proprement (graph.py:138)
- `create_tool_loop` avec `CARBON_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS` → pattern cohérent avec ESG
- Pas de dead code

### 2.2 Unicité BDD respectée

- FR-012 "empêcher création de 2 bilans pour la même année" :
  - Migration Alembic 007 : `create_index(['user_id', 'year'], unique=True)` ✅
  - Service.py:39 : vérification applicative + `ValueError("Un bilan carbone existe deja pour l'annee {year}")` ✅
  - Double protection : applicative + BDD

### 2.3 Validation Pydantic solide

- `schemas.py:32` : `quantity: float = Field(gt=0)` ✅
- `emission_factor: float = Field(gt=0)` ✅
- `year: int = Field(ge=2020, le=2100)` ✅
- FR-015 partie "valeurs négatives" traitée au niveau schéma

### 2.4 Meilleure couverture sectorielle que spec 005

- 8 secteurs dans `benchmarks.py` vs 6 dans `weights.py` ESG
- `agroalimentaire`, `commerce`, `artisanat`, `textile` sont présents ici — **contrairement à spec 005** où ils tombaient sur "general"
- Fallback intelligent vers secteurs similaires (benchmarks.py:138)

### 2.5 Conversion FCFA → unités physiques

- `PRICE_REFERENCES_FCFA` (emission_factors.py:75) permet à l'utilisateur de répondre en FCFA
- Adapté au public cible (PME africaines qui raisonnent plus en coût qu'en kWh/litres)
- Conformité FR-002 ✅

### 2.6 TDD respecté

- 3 fichiers de test écrits avant implémentation (T013-T015)
- Couverture ≥ 80 % visée (T039) — CLAUDE.md confirme "57 tests"

---

## 3. Ce qui a posé problème

### 3.1 🔴 DETTE LATENTE — Pattern tool-calling séquentiel (même dette que spec 005)

- `carbon_tools.py` expose 4 tools : `create_carbon_assessment`, `save_emission_entry`, `finalize_carbon_assessment`, `get_carbon_summary`
- **`save_emission_entry` est appelé UNE FOIS PAR ENTRÉE** d'émission
- Un bilan typique a 5-15 entrées (électricité, générateur, 2-3 véhicules, déchets, etc.)
- Chaque appel = 1 tool_call + 1 LLM response → risque de **timeout LLM** sur les gros bilans (comme spec 005)
- **Spec 015 a corrigé le même pattern pour ESG** (`batch_save_esg_criteria`) mais **pas pour carbon**
- **Pourquoi c'est moins critique que ESG** : N plus petit (10-15 vs 30), mais le risque reste
- **Leçon** : quand spec 015 a introduit le batch save pattern, étendre la même solution aux autres modules qui ont le même pattern (carbon, credit, application)

### 3.2 🟠 SECTOR_BENCHMARKS hard-codés (dette identique spec 005)

- `backend/app/modules/carbon/benchmarks.py` : dict Python hard-codé
- Assumption explicite dans spec : *"Les benchmarks sectoriels sont bases sur des donnees estimees/moyennes et non sur des donnees officielles certifiees"*
- **Impact** :
  - Impossible d'affiner avec les données réelles utilisateurs
  - Pas de traçabilité "sources" des valeurs (d'où viennent les 22 tCO2e moyens pour le transport ?)
  - Chaque update nécessite un redéploiement
- **Leçon** : même pattern que spec 005 §3.2 — consolidation BDD à faire globalement pour ESG + carbon simultanément

### 3.3 🟠 Validation "anormalement élevée" non implémentée

- FR-015 prescrit *"signaler les valeurs incoherentes (negatives, anormalement elevees)"*
- Négatives : OK (Pydantic `gt=0`)
- **Anormalement élevées : pas de garde-fou**
  - Un utilisateur qui saisit "10 000 000 kWh/an" pour une PME passe sans alerte
  - Une consommation diesel de 500 000 L/an aussi
- `grep "anormal|upper|max_quantity|warning"` dans service.py → vide
- Acceptance Scenario 4 de US1 non implémenté intégralement
- **Leçon** : FR-015 devait avoir une tâche explicite de "bornes supérieures par catégorie" (ex: kWh < 1M, diesel < 100k L)

### 3.4 🟠 Pas d'`UniqueConstraint` ORM dans le model

- Le model `carbon.py` ne déclare pas `__table_args__ = (UniqueConstraint('user_id', 'year'),)`
- L'unicité est via un `create_index(unique=True)` dans la migration → contrainte BDD ✅
- Mais SQLAlchemy ne connaît pas la contrainte → en cas de violation race, on reçoit un `IntegrityError` brut plutôt qu'un message applicatif clair
- **Impact** : UX dégradée sur les cas de race (rare mais possible si double-click sur "créer bilan")
- **Leçon** : déclarer les contraintes au niveau ORM **et** BDD — les deux vivent dans des espaces différents mais doivent être cohérents

### 3.5 🟡 RAG documentaire non exploité pour le carbon

- Les bilans comptables + factures d'électricité + factures transport sont exactement le type de documents qui alimenteraient `save_emission_entry` automatiquement
- `search_similar_chunks` (spec 004) pourrait récupérer les montants FCFA directement depuis les documents uploadés
- Actuellement seul `esg_node` exploite le RAG (cf. audit spec 004 §3.1)
- **Leçon** : cohérent avec la dette transverse "RAG sous-exploité (1/8 modules)"

### 3.6 🟡 SC-003 "calculs corrects à 1%" non validé

- Les facteurs d'émission hard-codés (0.41 kgCO2e/kWh pour CI, etc.) — d'où viennent-ils ?
- Pas de référence dans le code (pas de commentaire "source ADEME 2024" ou "source BCEAO")
- Pas de test de régression "les calculs ne dérivent pas des facteurs de référence"
- **Leçon** : pour les valeurs numériques métier, documenter la source + date + cible de révision annuelle

### 3.7 🟡 Édition manuelle des entrées d'émission impossible

- L'utilisateur passe par le chat pour créer/modifier les entrées
- Pas de page `/carbon/edit/{id}` pour corriger une entrée sans reparler au LLM
- Si le LLM extrait mal une valeur, l'utilisateur ne peut la corriger qu'en recommençant la conversation
- **Leçon** : pattern à uniformiser avec spec 003 (page profil édition manuelle) — toute donnée extraite du chat doit être éditable via page dédiée

---

## 4. Leçons transversales

1. **Étendre `batch_save_*` pattern** à tous les modules à tool-calling séquentiel (carbon, credit, application) — déjà fait pour ESG en spec 015.
2. **SECTOR_BENCHMARKS en BDD** (dette partagée spec 005 + 007) — opportunité de consolidation en une seule story.
3. **Bornes supérieures = tâche explicite** quand la spec dit "anormalement élevée".
4. **ORM + BDD cohérents** pour les contraintes — toujours déclarer aux deux niveaux.
5. **Sources des valeurs numériques métier = commentaires dans le code** — 0.41 kgCO2e/kWh vient d'où ?
6. **Toute donnée extraite du chat doit être éditable hors chat** — cf. spec 003 page profil.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Étendre `batch_save_*` pattern** au module carbon (nouveau tool `batch_save_emission_entries`) | ~~P2~~ → **P1** (reclassé 2026-04-16) | §3.1 |
| 2 | **Bornes supérieures par catégorie** dans schemas Pydantic (ex: `kwh: float = Field(gt=0, lt=1_000_000)`) | P2 | §3.3 |
| 3 | Déclarer `UniqueConstraint` dans le model ORM (en plus de l'index unique en BDD) | P3 | §3.4 |
| 4 | Documenter les sources des facteurs d'émission dans `emission_factors.py` (commentaires + liens + date de révision) | P3 | §3.6 |
| 5 | Page d'édition manuelle `/carbon/assessments/{id}/edit` pour corriger les entrées hors chat | P3 | §3.7 |

**Consolidation avec autres audits** :
- Action §3.2 "SECTOR_BENCHMARKS BDD" → fusionner avec action P2 #9 de l'index (source spec 005)
- Action §3.5 "RAG sous-exploité carbon" → fusionner avec action P2 #6 de l'index (source spec 004)

**Actions déjà en place** :
- ✅ Unicité BDD `(user_id, year)` via index unique
- ✅ Validation Pydantic `gt=0` sur quantités
- ✅ 8 secteurs benchmarkés (mieux que spec 005)
- ✅ Conversion FCFA → unités physiques

---

## 6. Verdict

**Spec 007 livrée à 100 %, audit-tasks-discordance OK (0 manquant), architecture cohérente avec spec 005 mais mieux exécutée sur la couverture sectorielle (8 secteurs vs 6).**

La dette la plus préoccupante est **§3.1 le pattern tool-calling séquentiel** : c'est la même dette que spec 005 qu'il a fallu fixer en spec 015. Le correctif `batch_save_esg_criteria` n'a pas été étendu ici — dette latente à résoudre avant qu'un utilisateur ne trigger un timeout en production sur un bilan multi-véhicules.

Les autres dettes sont opérationnelles (bornes supérieures, sources des facteurs, édition manuelle) et **transverses** avec les autres specs (consolidation possible).

---

## 7. Mise à jour 2026-04-16 — reclassement tool-calling séquentiel P2 → **P1**

**Justification** : le pattern tool-calling séquentiel sur `save_emission_entry` a déjà cassé en prod sous une forme équivalente (ESG, corrigé en spec 015 via `batch_save_esg_criteria`). Pour carbon, le bug est **latent mais non fictif** :

- Un bilan typique couvre 3 véhicules + 2 sources énergie + 2 dechets = **7 appels tool séquentiels**
- Un bilan d'une PME transport/logistique peut dépasser 15 entrées
- Chaque appel LLM = latence de 2-5 s, cumul de 15-75 s
- Le timeout `request_timeout=60` de `get_llm()` (fix spec 015) plafonne à 60 s → **les gros bilans timeoutent silencieusement**

Gravité = identique à ESG (déjà P1 via spec 015). Reclassement cohérent.

Story BMAD recommandée : **consolider dans une seule story « pattern batch_* transversal »** qui couvre simultanément carbon + les audits à venir (credit, application probablement). Évite de fragmenter le problème.
