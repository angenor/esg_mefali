# Tasks: Génération de Rapports ESG en PDF

**Input**: Design documents from `/specs/006-esg-pdf-reports/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Inclus (constitution impose TDD, couverture 80%).

**Organization**: Tasks groupées par user story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story concernée (US1, US2, US3, US4)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Infrastructure partagée)

**Purpose**: Installation des dépendances et structure du module reports

- [X] T001 Installer les dépendances Python : weasyprint, matplotlib, jinja2 dans backend/requirements.txt
- [X] T002 Créer la structure du module reports : backend/app/modules/reports/__init__.py, router.py, schemas.py, service.py, charts.py
- [X] T003 [P] Créer le répertoire des templates : backend/app/modules/reports/templates/
- [X] T004 [P] Créer le répertoire de stockage : backend/uploads/reports/
- [X] T005 [P] Créer les types TypeScript : frontend/app/types/report.ts

---

## Phase 2: Foundational (Prérequis bloquants)

**Purpose**: Modèle de données et infrastructure partagée par toutes les user stories

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

- [X] T006 Créer le modèle SQLAlchemy Report avec enums ReportType et ReportStatus dans backend/app/models/report.py
- [X] T007 Enregistrer le modèle Report dans backend/app/models/__init__.py
- [X] T008 Créer la migration Alembic 006_add_reports_table dans backend/alembic/versions/
- [X] T009 Exécuter la migration : alembic upgrade head
- [X] T010 Créer les schemas Pydantic (ReportResponse, ReportListResponse, ReportStatusResponse, ReportGenerateResponse) dans backend/app/modules/reports/schemas.py
- [X] T011 [P] Créer le composable useReports (generateReport, downloadReport, listReports, pollStatus) dans frontend/app/composables/useReports.ts
- [X] T012 Enregistrer le router reports dans backend/app/main.py

**Checkpoint**: Modèle de données et infrastructure prêts — les user stories peuvent commencer

---

## Phase 3: User Story 1 — Générer un rapport PDF (Priority: P1) MVP

**Goal**: L'utilisateur peut générer un rapport PDF de 5-10 pages à partir d'une évaluation ESG complétée

**Independent Test**: Compléter une évaluation ESG, cliquer sur "Générer le rapport PDF", vérifier que le PDF est téléchargé avec les 9 sections

### Tests US1

- [X] T013 [P] [US1] Tests unitaires du service de génération dans backend/tests/test_report_service.py (generate_report, validation statut completed, génération complète avec mock LLM)
- [X] T014 [P] [US1] Tests unitaires de génération de graphiques dans backend/tests/test_report_charts.py (radar_chart_svg, bar_chart_svg, benchmark_chart_svg)
- [X] T015 [P] [US1] Tests intégration des endpoints API dans backend/tests/test_report_router.py (POST generate 201/400/404/409, GET status, GET download 200/403/404)

### Implémentation US1

- [X] T016 [P] [US1] Implémenter la génération de graphiques SVG (radar chart 3 piliers, barres de progression par critère, graphique benchmarking sectoriel) dans backend/app/modules/reports/charts.py
- [X] T017 [P] [US1] Créer le prompt LangChain pour le résumé exécutif IA (150-300 mots, français professionnel) dans backend/app/prompts/esg_report.py
- [X] T018 [US1] Créer le template HTML/CSS du rapport ESG avec les 9 sections (couverture, résumé exécutif, scores détaillés, points forts, axes d'amélioration, benchmarking, conformité UEMOA/BCEAO, plan d'action, méthodologie) dans backend/app/modules/reports/templates/esg_report.html et esg_report.css
- [X] T019 [US1] Implémenter le service de génération PDF (collecter données assessment, générer SVG, appeler LLM résumé, rendre template Jinja2, convertir WeasyPrint, sauvegarder fichier) dans backend/app/modules/reports/service.py
- [X] T020 [US1] Implémenter les endpoints POST /api/reports/esg/{assessment_id}/generate et GET /api/reports/{report_id}/status dans backend/app/modules/reports/router.py
- [X] T020 [US1] Ajouter le bouton "Générer le rapport PDF" avec indicateur de progression et polling de statut sur la page résultats ESG dans frontend/app/pages/esg/results.vue (ou composant frontend/app/components/esg/ReportButton.vue)

**Checkpoint**: L'utilisateur peut générer et télécharger un rapport PDF complet depuis la page résultats ESG

---

## Phase 4: User Story 2 — Télécharger et consulter les rapports (Priority: P1)

**Goal**: L'utilisateur peut retrouver, prévisualiser et re-télécharger ses rapports depuis une page dédiée

**Independent Test**: Accéder à /reports, voir la liste des rapports, prévisualiser et télécharger un rapport

### Tests US2

- [X] T022 [P] [US2] Tests intégration pour GET /api/reports/ (liste paginée, filtrage par assessment_id, isolation par user_id) dans backend/tests/test_report_router.py

### Implémentation US2

- [X] T023 [US2] Implémenter les endpoints GET /api/reports/ (liste paginée) et GET /api/reports/{report_id}/download (téléchargement PDF) dans backend/app/modules/reports/router.py
- [X] T024 [US2] Créer la page liste des rapports avec tableau (date, type, statut, évaluation), prévisualisation inline PDF et bouton de téléchargement dans frontend/app/pages/reports/index.vue
- [X] T025 [US2] Ajouter le lien de navigation vers /reports dans le layout ou la sidebar frontend

**Checkpoint**: L'utilisateur peut consulter la liste de ses rapports, les prévisualiser et les re-télécharger

---

## Phase 5: User Story 3 — Contenu narratif et graphiques de qualité (Priority: P2)

**Goal**: Le rapport contient un résumé exécutif pertinent, des graphiques lisibles et un tableau de conformité UEMOA/BCEAO

**Independent Test**: Ouvrir un PDF généré, vérifier la qualité du résumé, la lisibilité des graphiques radar/barres, le tableau de conformité

### Implémentation US3

- [X] T026 [US3] Affiner le prompt du résumé exécutif IA pour garantir pertinence et qualité (150-300 mots, cohérent avec scores, français professionnel) dans backend/app/prompts/esg_report.py
- [X] T027 [US3] Enrichir la section conformité réglementaire du template avec tableau détaillé des taxonomies UEMOA et réglementation BCEAO dans backend/app/modules/reports/templates/esg_report.html
- [X] T028 [US3] Optimiser les graphiques pour lisibilité A4 : taille des polices, couleurs contrastées, légendes claires dans backend/app/modules/reports/charts.py
- [X] T029 [US3] Ajuster le CSS print pour garantir le rapport entre 5-10 pages avec sauts de page propres entre sections dans backend/app/modules/reports/templates/esg_report.css

**Checkpoint**: Le rapport PDF est visuellement professionnel avec contenu narratif pertinent et graphiques lisibles

---

## Phase 6: User Story 4 — Notification dans le chat (Priority: P3)

**Goal**: Le chatbot informe l'utilisateur quand le rapport est prêt avec un aperçu et un lien de téléchargement

**Independent Test**: Déclencher une génération depuis le chat, vérifier qu'un message apparaît avec le lien

### Implémentation US4

- [X] T030 [US4] Ajouter un noeud ou intégration dans le graph LangGraph pour déclencher la génération de rapport et poster le message de notification (diagramme mermaid + lien download) dans backend/app/graph/nodes.py
- [X] T031 [US4] Rendre le lien de téléchargement cliquable dans le composant chat frontend pour les messages contenant un lien de rapport

**Checkpoint**: Le flux conversationnel intègre la génération de rapport avec notification

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Qualité, sécurité et finitions

- [X] T032 [P] Ajouter la gestion des edge cases : benchmark absent, fichier supprimé, génération simultanée bloquée dans backend/app/modules/reports/service.py
- [X] T033 [P] Vérifier la compatibilité dark mode sur la page frontend/app/pages/reports/index.vue et le composant ReportButton.vue
- [X] T034 Mettre à jour CLAUDE.md avec les technologies et changements de la feature 006
- [X] T035 Validation complète : exécuter tous les tests, vérifier couverture >= 80%, tester le PDF sur navigateur + Aperçu macOS

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : Pas de dépendances — démarrage immédiat
- **Foundational (Phase 2)** : Dépend de Phase 1 — BLOQUE toutes les user stories
- **US1 (Phase 3)** : Dépend de Phase 2 — MVP
- **US2 (Phase 4)** : Dépend de Phase 2 + partiellement US1 (endpoint download créé en US1)
- **US3 (Phase 5)** : Dépend de US1 (affine le contenu du rapport existant)
- **US4 (Phase 6)** : Dépend de US1 (nécessite le service de génération fonctionnel)
- **Polish (Phase 7)** : Dépend de toutes les user stories

### Within Each User Story

- Tests écrits et ÉCHOUENT avant implémentation
- Modèles avant services
- Services avant endpoints
- Backend avant frontend
- Commit après chaque tâche ou groupe logique

### Parallel Opportunities

- T003, T004, T005 en parallèle (Phase 1)
- T011 en parallèle avec T006-T010 (Phase 2)
- T013, T014, T015 en parallèle (tests US1)
- T016, T017 en parallèle (implémentation US1 — fichiers indépendants)
- T032, T033 en parallèle (Phase 7)

---

## Parallel Example: User Story 1

```bash
# Tests US1 en parallèle :
Task: "Tests service génération dans backend/tests/test_report_service.py"
Task: "Tests graphiques dans backend/tests/test_report_charts.py"
Task: "Tests endpoints API dans backend/tests/test_report_router.py"

# Implémentation composants indépendants en parallèle :
Task: "Graphiques SVG dans backend/app/modules/reports/charts.py"
Task: "Prompt résumé exécutif dans backend/app/prompts/esg_report.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Compléter Phase 1: Setup
2. Compléter Phase 2: Foundational (CRITIQUE — bloque tout)
3. Compléter Phase 3: User Story 1
4. **STOP et VALIDER** : Tester la génération PDF indépendamment
5. Déployer/démontrer si prêt

### Incremental Delivery

1. Setup + Foundational → Infrastructure prête
2. User Story 1 → Génération PDF fonctionnelle (MVP!)
3. User Story 2 → Liste et re-téléchargement → Démo
4. User Story 3 → Qualité contenu professionnelle → Démo
5. User Story 4 → Intégration chat → Démo
6. Chaque story ajoute de la valeur sans casser les précédentes

---

## Notes

- [P] = fichiers différents, pas de dépendances
- [Story] = traçabilité vers la user story
- Chaque user story est indépendamment testable
- Les tests doivent échouer avant implémentation (TDD)
- Commit après chaque tâche ou groupe logique
- Arrêt possible à chaque checkpoint pour validation indépendante
