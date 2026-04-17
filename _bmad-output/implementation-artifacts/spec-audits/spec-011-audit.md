# Audit Rétrospectif — Spec 011 : Dashboard Principal et Plan d'Action

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/011-dashboard-action-plan/](../../../specs/011-dashboard-action-plan/)
**Méthode** : rétrospective post-hoc + audit-tasks-discordance
**Statut rétro** : ✅ Audité — architecture mature, dettes de scale

---

## 1. Portée de la spec

Dashboard synthétique agrégeant ESG/carbone/crédit/financements + plan d'action personnalisé 6/12/24 mois + rappels in-app + gamification 5 badges. Feature d'intégration qui s'appuie sur TOUS les modules métier (002-010).

| Dimension | Livré |
|-----------|-------|
| Tâches | 57 / 57 `[x]` (100 %) |
| Discordance tasks↔code | 0 (audit forensique OK) |
| User Stories | 5 (US1-US2 P1, US3-US4 P2, US5 P3) |
| Nouveaux modules backend | 2 (`dashboard/`, `action_plan/`) |
| Nouveau noeud | `action_plan_node` |
| Tools LangChain | `ACTION_PLAN_TOOLS` (pas de dashboard tools — lecture seule) |
| Composants frontend | 10 (4 dashboard + 6 action_plan) |
| Tests backend | 7 fichiers (dashboard: service+router ; action_plan: service+router+reminders+router_reminders+badges) |
| Nouveaux modèles | 4 (`ActionPlan`, `ActionItem`, `Reminder`, `Badge`) |
| Clarifications | 2 (5 statuts ActionItem + contenu Activité Récente) |
| CLAUDE.md mentionne | "105 tests" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture la plus mature du projet

- `action_plan_node` + `ACTION_PLAN_TOOLS` + `INTERACTIVE_TOOLS` + `GUIDED_TOUR_TOOLS` (graph.py:142)
- Pattern cohérent avec spec 010 (la référence)
- Pas de dashboard tools = décision correcte (dashboard = lecture, pas d'action)

### 2.2 Contrainte "1 seul plan actif par user" en BDD

- **Unique partial index** : `postgresql_where=text("status = 'active'")` (action_plan.py:127)
- Pattern avancé : permet plusieurs plans archivés + 1 actif, garanti par la BDD
- Supérieur à la validation applicative seule (pas de race condition)

### 2.3 Snapshot des coordonnées intermédiaires

- `ActionItem` stocke `intermediary_name`, `intermediary_address`, `intermediary_phone`, `intermediary_email` (action_plan.py:207-210)
- FR-007 implémenté : les actions conservent les coordonnées au moment de la génération
- Edge case "intermédiaire supprimé/mis à jour" correctement géré
- **Contraste avec `FundMatch` (spec 008 §3.7)** qui n'a pas ce snapshot — spec 011 a appris de la dette

### 2.4 Polling rappels propre

- `useActionPlan.ts:248` : `setInterval` avec cleanup (`ReturnType<typeof setInterval>`)
- Polling 60s pour détecter les rappels échus côté client
- Toast variant "intermediary" différencié (fond bleu + icône banque)

### 2.5 Activity Feed multi-sources

- Agrège 5 sources d'événements : action_items, badges, esg_assessments, carbon_assessments, fund_applications
- Clarification explicite documentée (Q2) avec 10 derniers éléments
- Pattern cohérent avec l'architecture data-agnostique

### 2.6 Badges automatiques à la volée

- `check_and_award_badges` intégré dans les mutations pertinentes (T050)
- 5 badges explicites : `first_carbon`, `esg_above_50`, `first_application`, `first_intermediary_contact`, `full_journey`
- Condition `full_journey` = AND (ESG, carbone, candidature soumise, contact terminé) → motivation claire
- Pas de doublon badge (vérifié en T048)

### 2.7 Couverture de tests solide

- 7 fichiers de test (2 dashboard + 5 action_plan) — cohérent avec spec 010
- CLAUDE.md : "105 tests" (pour cette feature uniquement — solide)

---

## 3. Ce qui a posé problème

### 3.1 🟠 `get_dashboard_summary` : queries sérialisées sans `asyncio.gather`

- Service dashboard : **487 lignes** (service.py)
- **Vérification** : `grep -c "asyncio.gather" backend/app/modules/dashboard/service.py` → **0**
- Le dashboard agrège 5 modules : ESG + carbone + crédit + financements + applications
- Chaque query SQLAlchemy async est attendue avant la suivante → latence cumulée
- Avec 100-200ms par query en local, c'est OK en dev, mais à l'échelle (BDD distante, dataset plus gros) → risque de dépassement SC-001 "< 3 s"
- **Leçon** : tout agrégateur multi-modules doit paralléliser ses queries avec `asyncio.gather()` — coût négligeable en code, gain significatif en latence

### 3.2 🟠 `dashboard/service.py` = 487 lignes → God service

- Service dense avec la logique d'agrégation de 5 modules
- Probable duplication : chaque module a sa propre logique "summary" qui pourrait être déléguée au service de chaque module
- Pattern actuel : dashboard tire depuis les **tables** des autres modules plutôt que d'appeler leurs **services**
- **Impact** :
  - Une migration de schéma d'un module (ex: ESG) casse silencieusement le dashboard
  - Les règles métier (ex: "quel score afficher si plusieurs assessments") sont potentiellement **dupliquées** entre `esg/service.py` et `dashboard/service.py`
- **Leçon** : les agrégateurs doivent consommer les **services** des modules, pas leurs tables — frontière claire

### 3.3 🟠 Génération de plan via LLM synchrone (SC-002 "< 30s")

- Même dette que spec 006 (génération PDF synchrone)
- `action_plan/service.py:generate_action_plan` appelle Claude pour générer 10+ actions JSON
- Bloque un worker uvicorn pendant 5-30 s → pannes cascade si 5+ users simultanés
- Pas de queue asynchrone (BackgroundTask FastAPI minimal ou Celery)
- **Leçon** : dette transverse avec spec 006 — consolider en une story "queue async pour générations LLM longues"

### 3.4 🟡 Polling 60s côté client : coût serveur linéaire

- `useActionPlan.ts:253` : polling toutes les 60s sur `/api/reminders/upcoming`
- N users connectés = N requêtes/minute → scaling linéaire
- Pas grave à 10 users, coûteux à 1000
- Alternative : SSE/WebSocket ou push notification (spec dit "hors périmètre" mais migration facile plus tard)
- **Leçon** : le polling est un choix V1 légitime, mais le documenter comme dette scale

### 3.5 🟡 `check_and_award_badges` à chaque mutation ActionItem

- T050 intègre la vérification dans `update_action_item`
- Coût : vérification des 5 conditions badge à chaque update, même si le user n'a pas changé de statut pertinent (ex: mettre à jour `completion_percentage` déclenche la vérification inutilement)
- **Impact** : négligeable à 5 badges, problématique à 20+
- **Leçon** : les hooks "check badges" doivent être conditionnés par le type de changement (filter: only on status transitions)

### 3.6 🟡 Pas de versioning du plan d'action

- Un user peut générer plusieurs plans au fil du temps (l'ancien est archivé)
- Mais pas de comparaison entre versions : qu'est-ce qui a changé entre le plan de janvier et celui de juillet ?
- Pattern similaire à spec 005 §3.5 (historique ESG sans diff)
- **Leçon** : dette transverse — tous les "historiques" gagneraient à avoir une analyse comparative (diff par catégorie, delta d'actions, etc.)

### 3.7 🟡 Pas de rappel automatique avant échéance d'une action

- Les rappels sont créés **manuellement** par le user (ReminderForm)
- Pas de rappel auto-généré à J-7 avant l'échéance d'une action
- **Impact** : un user qui oublie de créer un rappel rate l'échéance
- **Leçon** : les actions à échéance devraient auto-générer un rappel à J-X (configurable)

### 3.8 🟡 Badges fixes dans le code

- 5 badges hard-codés dans `BADGE_DEFINITIONS` (badges.py)
- Ajouter un 6ᵉ badge = PR code + déploiement
- Pas d'interface admin, pas de conditionnalité dynamique
- **Dette transverse** avec les templates spec 009 et les benchmarks spec 005/007
- **Leçon** : la gamification gagnerait à être data-driven (JSONB de définitions) pour évoluer sans déploiement

---

## 4. Leçons transversales

1. **Agrégateurs multi-modules → `asyncio.gather`** (latence divisée par N).
2. **Consommer les services des modules, pas leurs tables** (frontière API claire, évite duplication règles métier).
3. **Queue async pour générations LLM longues** — dette transverse (specs 006, 011).
4. **Polling documenté comme dette scale** — acceptable V1, migration planifiée.
5. **Hooks conditionnés par type de changement** — pas "always check".
6. **Historiques avec diff** — dette transverse (specs 005, 011).
7. **Rappels auto à J-X** pour les échéances.
8. **Gamification data-driven** (JSONB) pour extensibilité sans déploiement.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Paralléliser queries `get_dashboard_summary`** avec `asyncio.gather` | P2 | §3.1 |
| 2 | **Refactorer dashboard/service pour consommer les services des modules** (pas leurs tables) | P2 | §3.2 |
| 3 | **Queue asynchrone générations LLM** (dashboard plan + rapport PDF spec 006) — consolider en 1 story | P2 | §3.3 (déjà P1 #6 pour PDF) |
| 4 | Rappel auto-généré à J-7 avant échéance d'une `ActionItem` | P3 | §3.7 |
| 5 | Analyse comparative entre versions de plans (diff par catégorie) | P3 | §3.6 |
| 6 | Badges data-driven (JSONB `BadgeDefinition`) | P3 | §3.8 |
| 7 | Optimiser `check_and_award_badges` (conditionné par type de changement) | P3 | §3.5 |
| 8 | Migration polling → SSE/WebSocket pour rappels (scale > 100 users connectés) | P3 | §3.4 |

**Actions déjà en place** :
- ✅ Unique partial index "1 plan actif par user"
- ✅ Snapshot coordonnées intermédiaires dans ActionItem
- ✅ Machine à états explicite (5 statuts ActionItem)
- ✅ Activity Feed multi-sources
- ✅ 5 badges automatiques avec conditions AND

**Consolidation avec autres audits** :
- §3.3 queue async → consolider avec dette P1 #6 (spec 006) en 1 story transverse "queue async LLM"
- §3.6 diff historiques → consolider avec P3 #8 (spec 005 "analyse comparative évaluations")

---

## 6. Verdict

**Spec 011 est la plus mature des specs d'intégration — 105 tests, architecture propre, contraintes BDD avancées (unique partial index), snapshot des données tierces (intermediary coordinates).**

Cette spec **apprend des dettes des précédentes** : elle stocke les snapshots (que spec 008 ne fait pas sur `FundMatch`), utilise GUIDED_TOUR_TOOLS (que spec 009 n'a pas), utilise l'unique partial index (pattern avancé).

Les dettes sont **opérationnelles et liées au scale** (queries sérialisées, polling, génération synchrone) plutôt qu'architecturales. Aucune dette P1.

**Recommandation** : spec 011 peut servir de **référence pour les features d'intégration** (qui agrègent plusieurs modules). Pattern à reproduire : unique partial index + snapshot des données tierces + badges data-driven (à améliorer).
