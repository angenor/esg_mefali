# Tasks: Tableau de bord principal et plan d'action

**Input**: Design documents from `/specs/011-dashboard-action-plan/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus (constitution exige Test-First, couverture >= 80%).

**Organization**: Tasks groupées par user story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story associée (US1, US2, US3, US4, US5)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup

**Purpose**: Structure des modules et dépendances

- [x] T001 Créer la structure du module backend dashboard dans backend/app/modules/dashboard/__init__.py
- [x] T002 [P] Créer la structure du module backend action_plan dans backend/app/modules/action_plan/__init__.py
- [x] T003 [P] Créer les répertoires de tests backend/tests/test_dashboard/ et backend/tests/test_action_plan/
- [x] T004 [P] Créer les répertoires frontend : frontend/app/pages/dashboard.vue (placeholder), frontend/app/pages/action-plan/index.vue (placeholder)
- [x] T005 [P] Créer les répertoires de composants frontend/app/components/dashboard/ et frontend/app/components/action-plan/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modèles de données, migration Alembic, schemas Pydantic partagés, enregistrement des routers

**CRITICAL**: Aucune user story ne peut démarrer avant complétion de cette phase.

- [x] T006 Créer les modèles SQLAlchemy ActionPlan, ActionItem, Reminder, Badge dans backend/app/models/action_plan.py (enums ActionItemCategory, ActionItemStatus, ActionItemPriority, ReminderType, BadgeType, PlanTimeframe, PlanStatus ; relations avec User, Fund, Intermediary ; contrainte unique partielle plan actif par user ; index reminders upcoming)
- [x] T007 Enregistrer les imports des nouveaux modèles dans backend/app/models/__init__.py
- [x] T008 Générer et appliquer la migration Alembic : `alembic revision --autogenerate -m "add action_plan dashboard tables"` puis `alembic upgrade head`
- [x] T009 [P] Créer les schemas Pydantic pour action_plan dans backend/app/modules/action_plan/schemas.py (ActionPlanCreate, ActionPlanResponse, ActionItemResponse, ActionItemUpdate, ReminderCreate, ReminderResponse, BadgeResponse, ProgressByCategory)
- [x] T010 [P] Créer les schemas Pydantic pour dashboard dans backend/app/modules/dashboard/schemas.py (DashboardSummary, EsgSummary, CarbonSummary, CreditSummary, FinancingSummary, NextAction, ActivityEvent)
- [x] T011 [P] Créer les types TypeScript frontend dans frontend/app/types/dashboard.ts (DashboardSummary, EsgSummary, CarbonSummary, CreditSummary, FinancingSummary, NextAction, ActivityEvent)
- [x] T012 [P] Créer les types TypeScript frontend dans frontend/app/types/actionPlan.ts (ActionPlan, ActionItem, ActionItemCategory, ActionItemStatus, Reminder, ReminderType, Badge, BadgeType, ProgressByCategory)
- [x] T013 Enregistrer les routers dashboard et action_plan dans backend/app/main.py (prefix /api/dashboard et /api/action-plan, tags dashboard et action-plan)

**Checkpoint**: Fondation prête — les tables existent, les schemas sont définis, les routers enregistrés.

---

## Phase 3: User Story 1 — Consultation du tableau de bord synthétique (Priority: P1) MVP

**Goal**: L'utilisateur voit un dashboard agrégé avec 4 cartes (ESG, Carbone, Crédit Vert, Financements enrichie), les 5 prochaines actions et les 10 derniers événements d'activité.

**Independent Test**: Accéder à GET /api/dashboard/summary avec un utilisateur ayant des données → retourne les 4 sections avec données à jour. Accéder sans données → retourne les sections à null avec états vides.

### Tests US1

- [x] T014 [P] [US1] Tests unitaires du service dashboard dans backend/tests/test_dashboard/test_service.py (agrégation ESG, carbone, crédit, financements avec données ; agrégation sans données retourne null ; prochaines actions triées par due_date ; activité récente 10 derniers événements multi-sources)
- [x] T015 [P] [US1] Tests du router dashboard dans backend/tests/test_dashboard/test_router.py (GET /api/dashboard/summary 200 avec données ; 200 sans données retourne nulls ; 401 sans auth)

### Implementation US1

- [x] T016 [US1] Implémenter le service dashboard dans backend/app/modules/dashboard/service.py (get_dashboard_summary : agrège les données des services existants ESG, carbone, crédit, financement, applications ; calcule prochaines 5 actions triées par due_date ; collecte 10 derniers événements activité depuis action_items, badges, esg_assessments, carbon_assessments, fund_applications)
- [x] T017 [US1] Implémenter le router dashboard dans backend/app/modules/dashboard/router.py (GET /summary → appelle service, retourne DashboardSummary)
- [x] T018 [P] [US1] Créer le store Pinia dashboard dans frontend/app/stores/dashboard.ts (state : summary, loading, error ; actions : setSummary, setLoading, setError)
- [x] T019 [P] [US1] Créer le composable useDashboard dans frontend/app/composables/useDashboard.ts (fetchSummary → GET /api/dashboard/summary ; pattern natif fetch + Bearer token + store sync)
- [x] T020 [P] [US1] Créer le composant ScoreCard.vue dans frontend/app/components/dashboard/ScoreCard.vue (carte générique pour ESG/Carbone/Crédit : props score, label, icon, trend, mini chart slot ; dark mode ; état vide avec CTA)
- [x] T021 [P] [US1] Créer le composant FinancingCard.vue dans frontend/app/components/dashboard/FinancingCard.vue (carte Financements enrichie : fonds compatibles, dossiers en cours avec badges statut, prochaine action intermédiaire, icône banque si parcours intermédiaire ; dark mode ; état vide)
- [x] T022 [P] [US1] Créer le composant NextActions.vue dans frontend/app/components/dashboard/NextActions.vue (liste 5 prochaines actions triées ; icône banque + adresse pour actions intermediary_contact ; dark mode ; état vide)
- [x] T023 [P] [US1] Créer le composant ActivityFeed.vue dans frontend/app/components/dashboard/ActivityFeed.vue (10 derniers événements avec icône par type, timestamp relatif ; dark mode ; état vide)
- [x] T024 [US1] Implémenter la page dashboard dans frontend/app/pages/dashboard.vue (remplacer le placeholder index.vue ; layout 4 cartes en grid responsive ; section Prochaines Actions ; section Activité Récente ; appel useDashboard.fetchSummary au mount ; definePageMeta layout default)
- [x] T025 [US1] Mettre à jour la redirection : frontend/app/pages/index.vue redirige vers /dashboard (navigateTo('/dashboard'))

**Checkpoint**: Le dashboard est fonctionnel et affiche les données agrégées des modules existants.

---

## Phase 4: User Story 2 — Génération et gestion du plan d'action (Priority: P1)

**Goal**: L'utilisateur peut générer un plan d'action personnalisé via l'API ou le chat, avec des actions concrètes liées aux intermédiaires. Il peut mettre à jour le statut des actions.

**Independent Test**: POST /api/action-plan/generate avec timeframe=12 → plan avec 10+ actions couvrant 4+ catégories. Les actions intermediary_contact contiennent les coordonnées. PATCH /api/action-plan/items/{id} met à jour le statut. Le chat affiche les blocs visuels.

### Tests US2

- [x] T026 [P] [US2] Tests du service action_plan dans backend/tests/test_action_plan/test_service.py (generate_action_plan : crée plan avec actions multi-catégories ; actions intermediary_contact avec coordonnées snapshot ; archive ancien plan si existant ; erreur si profil incomplet ; get_active_plan ; get_items avec filtre catégorie ; update_item avec transitions valides/invalides ; update compteurs plan)
- [x] T027 [P] [US2] Tests du router action_plan dans backend/tests/test_action_plan/test_router.py (POST /generate 201 ; POST /generate 428 profil incomplet ; GET / 200 plan actif ; GET / 404 aucun plan ; GET /{id}/items 200 avec filtre ; PATCH /items/{id} 200 ; PATCH /items/{id} 400 transition invalide)

### Implementation US2

- [x] T028 [US2] Créer le prompt système plan d'action dans backend/app/prompts/action_plan.py (prompt pour Claude : contexte profil entreprise, score ESG, bilan carbone, fonds recommandés, intermédiaires avec coordonnées ; instructions JSON structuré avec catégories, priorités, échéances, coûts estimés XOF ; actions intermediary_contact avec fund_id et intermediary_id)
- [x] T029 [US2] Implémenter le service action_plan dans backend/app/modules/action_plan/service.py (generate_action_plan : collecte contexte utilisateur, appelle Claude via LangChain, parse JSON, crée ActionPlan + ActionItems avec snapshot coordonnées intermédiaires ; get_active_plan ; get_plan_items avec filtre category/status + pagination + progress par catégorie ; update_action_item avec validation transitions statut + mise à jour compteurs plan ; archive_plan)
- [x] T030 [US2] Implémenter le router action_plan dans backend/app/modules/action_plan/router.py (POST /generate, GET /, GET /{plan_id}/items, PATCH /items/{item_id})
- [x] T031 [US2] Ajouter le noeud action_plan_node dans backend/app/graph/nodes.py (détection intent plan d'action ; appelle service generate ; formate réponse avec blocs visuels ```timeline, ```table, ```mermaid parcours financement, ```gauge complétion, ```chart avancement par catégorie)
- [x] T032 [US2] Mettre à jour le routeur LangGraph dans backend/app/graph/graph.py (ajouter _route_action_plan, patterns regex pour détection, edge vers action_plan_node)
- [x] T033 [US2] Mettre à jour le state LangGraph dans backend/app/graph/state.py (ajouter action_plan_data: dict et _route_action_plan: bool)
- [x] T034 [P] [US2] Créer le store Pinia actionPlan dans frontend/app/stores/actionPlan.ts (state : plan, items, loading, error, progress ; actions : setPlan, setItems, updateItem, setProgress)
- [x] T035 [P] [US2] Créer le composable useActionPlan dans frontend/app/composables/useActionPlan.ts (generatePlan → POST /api/action-plan/generate ; fetchPlan → GET /api/action-plan/ ; fetchItems → GET /api/action-plan/{id}/items avec filtre category ; updateItem → PATCH /api/action-plan/items/{id})

**Checkpoint**: Le plan d'action peut être généré, consulté et mis à jour. Le chat affiche les blocs visuels.

---

## Phase 5: User Story 3 — Consultation et filtrage du plan d'action (Priority: P2)

**Goal**: L'utilisateur consulte son plan avec une timeline visuelle, filtre par catégorie, et accède aux détails des actions intermédiaires avec coordonnées et lien vers /applications.

**Independent Test**: Accéder à /action-plan avec un plan existant → timeline visible, filtre "Contacts intermédiaires" fonctionne, détail action montre coordonnées et lien fiche préparation.

### Implementation US3

- [x] T036 [P] [US3] Créer le composant Timeline.vue dans frontend/app/components/action-plan/Timeline.vue (timeline verticale chronologique ; codes couleur par catégorie ; indicateur visuel par statut ; icône banque pour intermediary_contact ; responsive ; dark mode)
- [x] T037 [P] [US3] Créer le composant ActionCard.vue dans frontend/app/components/action-plan/ActionCard.vue (détail action : titre, description, statut, priorité, échéance, coût XOF, bénéfice, progression ; si intermediary_contact : coordonnées complètes intermédiaire + bouton "Voir la fiche de préparation" lien vers /applications/{related_fund_id} ; dark mode)
- [x] T038 [P] [US3] Créer le composant CategoryFilter.vue dans frontend/app/components/action-plan/CategoryFilter.vue (filtre par catégorie : 6 catégories + "Tous" ; icône banque pour "Contacts intermédiaires" ; compteur d'actions par catégorie ; dark mode)
- [x] T039 [P] [US3] Créer le composant ProgressBar.vue dans frontend/app/components/action-plan/ProgressBar.vue (barre de progression globale ; graphique barres horizontales avancement par catégorie via Chart.js ; dark mode)
- [x] T040 [US3] Implémenter la page plan d'action dans frontend/app/pages/action-plan/index.vue (en-tête avec titre plan + timeframe + bouton régénérer ; ProgressBar ; CategoryFilter ; Timeline avec ActionCards ; appel useActionPlan au mount ; gestion état vide sans plan ; definePageMeta layout default ; dark mode)

**Checkpoint**: La page plan d'action est fonctionnelle avec timeline, filtres et détails.

---

## Phase 6: User Story 4 — Rappels et notifications (Priority: P2)

**Goal**: L'utilisateur peut créer des rappels liés aux actions et reçoit des toasts in-app distincts visuellement (bleu pour les rappels intermédiaires).

**Independent Test**: POST /api/reminders/ crée un rappel. GET /api/reminders/upcoming retourne les rappels non envoyés. Le frontend affiche un toast bleu pour les rappels intermédiaires.

### Tests US4

- [x] T041 [P] [US4] Tests du service reminders dans backend/tests/test_action_plan/test_reminders.py (create_reminder ; get_upcoming tri par date ; mark_as_sent ; filtre par type)
- [x] T042 [P] [US4] Tests du router reminders dans backend/tests/test_action_plan/test_router_reminders.py (POST /reminders/ 201 ; GET /reminders/upcoming 200)

### Implementation US4

- [x] T043 [US4] Ajouter le service rappels dans backend/app/modules/action_plan/service.py (create_reminder ; get_upcoming_reminders trié par scheduled_at, filtré sent=false ; mark_reminder_sent)
- [x] T044 [US4] Ajouter les endpoints rappels dans backend/app/modules/action_plan/router.py (POST /reminders/, GET /reminders/upcoming)
- [x] T045 [P] [US4] Créer le composant ReminderForm.vue dans frontend/app/components/action-plan/ReminderForm.vue (formulaire création rappel : action liée, type, message, date ; dark mode)
- [x] T046 [US4] Ajouter les fonctions rappels dans frontend/app/composables/useActionPlan.ts (createReminder → POST /api/reminders/ ; fetchUpcomingReminders → GET /api/reminders/upcoming ; polling 60s pour rappels échus)
- [x] T047 [US4] Mettre à jour le composant ToastNotification.vue dans frontend/app/components/ui/ToastNotification.vue (ajouter variante "intermediary" : fond bleu, icône banque ; afficher les rappels échus en toast ; distinguer visuellement les rappels intermediary_followup)

**Checkpoint**: Les rappels fonctionnent avec notifications in-app visuellement distinctes.

---

## Phase 7: User Story 5 — Gamification et badges (Priority: P3)

**Goal**: 5 badges de gamification se déclenchent automatiquement (premier bilan carbone, score ESG > 50, première candidature, premier contact intermédiaire, parcours complet).

**Independent Test**: Simuler les conditions de chaque badge → le badge est débloqué et visible dans le dashboard.

### Tests US5

- [x] T048 [P] [US5] Tests du service badges dans backend/tests/test_action_plan/test_badges.py (check_and_award_badges : first_carbon quand bilan existe ; esg_above_50 quand score > 50 ; first_application quand candidature soumise ; first_intermediary_contact quand action intermédiaire terminée ; full_journey quand toutes conditions remplies ; pas de doublon badge ; get_user_badges)

### Implementation US5

- [x] T049 [US5] Créer le module badges dans backend/app/modules/action_plan/badges.py (BADGE_DEFINITIONS : dict badge_type → condition callable ; check_and_award_badges : vérifie toutes les conditions pour un user, attribue les badges manquants, retourne les nouveaux badges ; get_user_badges)
- [x] T050 [US5] Intégrer la vérification des badges dans les mutations pertinentes : update_action_item (pour first_intermediary_contact, full_journey) dans backend/app/modules/action_plan/service.py
- [x] T051 [P] [US5] Créer le composant BadgeGrid.vue dans frontend/app/components/action-plan/BadgeGrid.vue (grille de 5 badges : icône, titre, description, état verrouillé/débloqué, date débloquage ; dark mode)
- [x] T052 [US5] Intégrer BadgeGrid dans la page dashboard.vue dans frontend/app/pages/dashboard.vue (section badges après activité récente)

**Checkpoint**: Les 5 badges fonctionnent et sont visibles dans le dashboard.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Intégration finale, navigation, optimisations

- [x] T053 [P] Mettre à jour la sidebar navigation dans frontend/app/components/layout/AppSidebar.vue (ajouter liens /dashboard et /action-plan avec icônes appropriées)
- [x] T054 [P] Mettre à jour le CLAUDE.md avec les technologies ajoutées (011-dashboard-action-plan dans Recent Changes et Active Technologies)
- [x] T055 Vérifier la couverture de tests >= 80% avec `pytest --cov` et ajouter des tests manquants si nécessaire
- [x] T056 Exécuter la validation quickstart.md : tester les commandes curl et vérifier les réponses attendues
- [x] T057 Dark mode : vérifier tous les composants dashboard et action-plan en mode sombre

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dépendances — peut démarrer immédiatement
- **Foundational (Phase 2)**: Dépend de Setup — BLOQUE toutes les user stories
- **US1 Dashboard (Phase 3)**: Dépend de Foundational
- **US2 Génération plan (Phase 4)**: Dépend de Foundational
- **US3 Filtrage/Timeline (Phase 5)**: Dépend de US2 (besoin d'un plan existant pour l'afficher)
- **US4 Rappels (Phase 6)**: Dépend de US2 (besoin d'actions pour créer des rappels)
- **US5 Badges (Phase 7)**: Dépend de US2 (besoin du service action_plan pour intégrer les vérifications)
- **Polish (Phase 8)**: Dépend de toutes les phases précédentes

### User Story Dependencies

- **US1 (P1)**: Indépendant — peut démarrer dès Phase 2 terminée
- **US2 (P1)**: Indépendant — peut démarrer dès Phase 2 terminée, en parallèle avec US1
- **US3 (P2)**: Dépend de US2 (store + composable action plan)
- **US4 (P2)**: Dépend de US2 (modèle Reminder lié aux ActionItems)
- **US5 (P3)**: Dépend de US2 (service badges intégré au service action_plan)

### Within Each User Story

- Tests MUST être écrits et FAIL avant implémentation
- Modèles avant services
- Services avant endpoints/router
- Backend avant frontend (pour chaque endpoint)
- Composants avant pages

### Parallel Opportunities

- **Phase 1**: T001-T005 tous en parallèle
- **Phase 2**: T009, T010, T011, T012 en parallèle après T006-T008
- **Phase 3 + Phase 4**: US1 et US2 en parallèle après Phase 2
- **Phase 5 + Phase 6 + Phase 7**: US3, US4, US5 en parallèle après US2
- **Phase 8**: T053-T054 en parallèle

---

## Parallel Example: Phase 3 + Phase 4

```bash
# US1 et US2 peuvent tourner en parallèle après Phase 2 :

# Agent 1 — US1 Dashboard :
Task: T014 "Tests service dashboard"
Task: T015 "Tests router dashboard"
Task: T016 "Service dashboard"
Task: T017 "Router dashboard"
Task: T018-T023 "Composants frontend dashboard"
Task: T024-T025 "Page dashboard"

# Agent 2 — US2 Plan d'action :
Task: T026 "Tests service action_plan"
Task: T027 "Tests router action_plan"
Task: T028 "Prompt action_plan"
Task: T029-T030 "Service + Router action_plan"
Task: T031-T033 "Noeud LangGraph"
Task: T034-T035 "Store + Composable frontend"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Compléter Phase 1: Setup
2. Compléter Phase 2: Foundational (CRITICAL)
3. Compléter Phase 3: Dashboard (US1) + Phase 4: Plan d'action (US2) en parallèle
4. **STOP et VALIDER** : Dashboard fonctionnel + plan générable/modifiable
5. Déployer/démontrer le MVP

### Incremental Delivery

1. Setup + Foundational → Base prête
2. US1 (Dashboard) + US2 (Plan d'action) → MVP fonctionnel
3. US3 (Timeline/Filtres) → UX enrichie
4. US4 (Rappels) → Suivi actif
5. US5 (Badges) → Gamification motivationnelle
6. Polish → Qualité finale

---

## Notes

- [P] tasks = fichiers différents, pas de dépendances
- [Story] label associe la tâche à la user story pour traçabilité
- Chaque user story est indépendamment complétable et testable
- Vérifier que les tests échouent avant d'implémenter
- Committer après chaque tâche ou groupe logique
- S'arrêter à chaque checkpoint pour valider la story indépendamment
