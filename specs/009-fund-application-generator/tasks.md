# Tasks: Fund Application Generator

**Input**: Design documents from `/specs/009-fund-application-generator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Inclus (TDD requis par la constitution, objectif 80% couverture).

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, etc.)
- Chemins absolus depuis la racine du depot

---

## Phase 1: Setup

**Purpose**: Initialisation du module applications et dependances

- [x] T001 Ajouter python-docx aux dependances dans backend/requirements.txt
- [x] T002 Creer le module backend/app/modules/applications/__init__.py
- [x] T003 [P] Creer le modele FundApplication avec enums TargetType et ApplicationStatus dans backend/app/models/application.py
- [x] T004 [P] Creer la configuration des templates de sections par target_type dans backend/app/modules/applications/templates.py
- [x] T005 Generer la migration Alembic pour la table fund_applications
- [x] T006 Creer les schemas Pydantic (create, update, response, list) dans backend/app/modules/applications/schemas.py

**Checkpoint**: Structure du module en place, BDD migree, schemas prets.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Service de base et routeur — prerequis pour toutes les user stories

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase.

- [x] T007 Implementer le service de base (create, get, list, update_status) dans backend/app/modules/applications/service.py
- [x] T008 Implementer le routeur avec les endpoints POST /, GET /, GET /{id}, PATCH /{id}/status dans backend/app/modules/applications/router.py
- [x] T009 Enregistrer le routeur applications dans backend/app/main.py
- [x] T010 [P] Ecrire les tests unitaires du service de base (create, get, list, update_status) dans backend/tests/test_applications/test_service.py
- [x] T011 [P] Ecrire les tests d'integration du routeur (POST, GET, PATCH status) dans backend/tests/test_applications/test_router.py

**Checkpoint**: CRUD de base fonctionnel, tests passent, API accessible.

---

## Phase 3: User Story 1 — Dossier fonds acces direct (Priority: P1) MVP

**Goal**: Un utilisateur peut creer un dossier pour un fonds a acces direct (ex: FNDE) avec template institutionnel, sections generees par LLM, edition rich text, et export PDF/Word.

**Independent Test**: Creer un dossier FNDE, verifier le template fund_direct (5 sections), generer une section, la modifier, exporter en PDF.

### Tests US1

- [x] T012 [P] [US1] Ecrire les tests pour la generation de section LLM dans backend/tests/test_applications/test_service.py (test_generate_section_fund_direct)
- [x] T013 [P] [US1] Ecrire les tests pour l'export PDF et Word dans backend/tests/test_applications/test_export.py
- [x] T014 [P] [US1] Ecrire les tests des endpoints generate-section, PATCH sections/{key}, export dans backend/tests/test_applications/test_router.py

### Implementation US1

- [x] T015 [US1] Implementer la generation de section via LLM + RAG dans backend/app/modules/applications/service.py (generate_section avec build_section_prompt par target_type)
- [x] T016 [US1] Implementer l'endpoint POST /{id}/generate-section dans backend/app/modules/applications/router.py
- [x] T017 [US1] Implementer l'endpoint PATCH /{id}/sections/{key} dans backend/app/modules/applications/router.py
- [x] T018 [P] [US1] Implementer le module d'export PDF (WeasyPrint) + Word (python-docx) dans backend/app/modules/applications/export.py
- [x] T019 [P] [US1] Creer le template Jinja2 HTML pour l'export dossier dans backend/app/modules/applications/templates/application_export.html
- [x] T020 [US1] Implementer l'endpoint POST /{id}/export dans backend/app/modules/applications/router.py
- [x] T021 [US1] Creer la page liste des dossiers dans frontend/app/pages/applications/index.vue
- [x] T022 [US1] Creer le composable useApplications dans frontend/app/composables/useApplications.ts
- [x] T023 [US1] Creer le store Pinia applications dans frontend/app/stores/applications.ts
- [x] T024 [US1] Creer la page detail dossier avec navigation sections, editeur rich text, bandeau destinataire, code couleur sections dans frontend/app/pages/applications/[id].vue

**Checkpoint**: Dossier fund_direct creeable, sections generees/editables, export PDF/Word fonctionnel. MVP utilisable.

---

## Phase 4: User Story 2 — Dossier via banque partenaire (Priority: P1)

**Goal**: Un utilisateur peut creer un dossier SUNREF via SIB avec template bancaire (6 sections), ton oriente business case, checklist documents financiers.

**Independent Test**: Creer un dossier SUNREF/SIB, verifier que le template a 6 sections bancaires, que le ton est "business case", que la checklist demande des bilans comptables.

### Tests US2

- [x] T025 [P] [US2] Ecrire les tests pour la generation de section bancaire (ton, vocabulaire) dans backend/tests/test_applications/test_service.py (test_generate_section_intermediary_bank)
- [x] T026 [P] [US2] Ecrire les tests pour la checklist adaptee au destinataire dans backend/tests/test_applications/test_service.py (test_get_checklist_bank vs test_get_checklist_direct)
- [x] T027 [P] [US2] Ecrire les tests de l'endpoint GET /{id}/checklist dans backend/tests/test_applications/test_router.py

### Implementation US2

- [x] T028 [US2] Implementer la logique de determination automatique du target_type dans backend/app/modules/applications/service.py (determine_target_type depuis intermediary.intermediary_type)
- [x] T029 [US2] Implementer la generation de checklist adaptee au destinataire dans backend/app/modules/applications/service.py (get_checklist)
- [x] T030 [US2] Implementer l'endpoint GET /{id}/checklist dans backend/app/modules/applications/router.py
- [x] T031 [US2] Ajouter l'onglet Checklist avec statut documents (fourni/manquant) dans frontend/app/pages/applications/[id].vue

**Checkpoint**: Dossier bancaire creeable avec template 6 sections, checklist financiere, ton bancaire verifie.

---

## Phase 5: User Story 3 — Fiche de preparation intermediaire (Priority: P2)

**Goal**: Generer une fiche de preparation PDF (2-3 pages) avec resume entreprise, score ESG, bilan carbone, eligibilite, documents disponibles, 5 questions, coordonnees intermediaire.

**Independent Test**: Generer la fiche pour un dossier SUNREF/SIB, telecharger le PDF, verifier les 6 elements et les coordonnees de la SIB.

### Tests US3

- [x] T032 [P] [US3] Ecrire les tests pour la generation de la fiche de preparation dans backend/tests/test_applications/test_prep_sheet.py
- [x] T033 [P] [US3] Ecrire le test de l'endpoint POST /{id}/prep-sheet (succes + erreur si fund_direct) dans backend/tests/test_applications/test_router.py

### Implementation US3

- [x] T034 [US3] Implementer la generation de la fiche de preparation (collecte donnees + LLM pour questions) dans backend/app/modules/applications/prep_sheet.py
- [x] T035 [P] [US3] Creer le template Jinja2 HTML pour la fiche de preparation PDF dans backend/app/modules/applications/templates/prep_sheet.html
- [x] T036 [US3] Implementer l'endpoint POST /{id}/prep-sheet dans backend/app/modules/applications/router.py
- [x] T037 [US3] Ajouter l'onglet Fiche de preparation (apercu, coordonnees intermediaire avec liens tel:/mailto:, bouton telecharger PDF) dans frontend/app/pages/applications/[id].vue

**Checkpoint**: Fiche de preparation generee en PDF avec coordonnees, visible dans l'onglet frontend.

---

## Phase 6: User Story 4 — Dossier agence d'implementation (Priority: P2)

**Goal**: Template agence (5 sections developpement) pour les dossiers FEM/PNUD. Ton oriente alignement strategique et indicateurs d'impact.

**Independent Test**: Creer un dossier FEM via PNUD, verifier les 5 sections agence et le ton developpement.

### Tests US4

- [x] T038 [P] [US4] Ecrire les tests pour la generation de section agence (template + ton) dans backend/tests/test_applications/test_templates.py

### Implementation US4

- [x] T039 [US4] Verifier et ajuster le template intermediary_agency dans backend/app/modules/applications/templates.py (5 sections, instructions de ton)
- [x] T040 [US4] Ajouter le prompt agence specifique dans backend/app/modules/applications/service.py (build_section_prompt pour intermediary_agency)

**Checkpoint**: Dossier agence creeable avec template 5 sections et ton developpement.

---

## Phase 7: User Story 5 — Dossier developpeur projets carbone (Priority: P3)

**Goal**: Template carbone (5 sections techniques) pour Gold Standard/Verra. Ton technique et methodologique.

**Independent Test**: Creer un dossier Gold Standard, verifier les 5 sections techniques carbone.

### Tests US5

- [x] T041 [P] [US5] Ecrire les tests pour la generation de section carbone (template + ton) dans backend/tests/test_applications/test_templates.py

### Implementation US5

- [x] T042 [US5] Verifier et ajuster le template intermediary_developer dans backend/app/modules/applications/templates.py (5 sections, instructions de ton technique)
- [x] T043 [US5] Ajouter le prompt carbone specifique dans backend/app/modules/applications/service.py (build_section_prompt pour intermediary_developer)

**Checkpoint**: Dossier carbone creeable avec template technique.

---

## Phase 8: User Story 6 — Simulateur de financement (Priority: P2)

**Goal**: Simulation estimant montant eligible, ROI vert, timeline (avec etape intermediaire si applicable), impact carbone et frais intermediaire.

**Independent Test**: Lancer une simulation SUNREF/SIB, verifier que la timeline inclut "Traitement par la banque" et que les frais sont estimes.

### Tests US6

- [x] T044 [P] [US6] Ecrire les tests du simulateur (avec et sans intermediaire) dans backend/tests/test_applications/test_simulation.py
- [x] T045 [P] [US6] Ecrire le test de l'endpoint POST /{id}/simulate dans backend/tests/test_applications/test_router.py

### Implementation US6

- [x] T046 [US6] Implementer le simulateur de financement dans backend/app/modules/applications/simulation.py
- [x] T047 [US6] Implementer l'endpoint POST /{id}/simulate dans backend/app/modules/applications/router.py
- [x] T048 [US6] Ajouter l'onglet Simulation (montant, ROI, timeline, impact, frais) dans frontend/app/pages/applications/[id].vue

**Checkpoint**: Simulation fonctionnelle avec timeline enrichie (etape intermediaire visible).

---

## Phase 9: User Story 7 — Generation/regeneration de sections (Priority: P2)

**Goal**: Generer ou regenerer individuellement chaque section avec prise en compte du target_type et exploitation du RAG.

**Independent Test**: Regenerer une section d'un dossier bancaire, verifier que le nouveau contenu reste au ton bancaire.

### Implementation US7

- [x] T049 [US7] Ajouter le bouton "Regenerer" par section avec confirmation dans frontend/app/pages/applications/[id].vue
- [x] T050 [US7] Implementer la validation manuelle de section (passage statut validated) dans frontend/app/pages/applications/[id].vue

**Checkpoint**: Regeneration section par section fonctionnelle, validation manuelle operative.

---

## Phase 10: User Story 8 — Suivi statut enrichi (Priority: P3)

**Goal**: Machine a etats refletant le parcours via intermediaire avec libelles en francais contextualises.

**Independent Test**: Faire progresser un dossier a travers les statuts et verifier les libelles francais.

### Tests US8

- [x] T051 [P] [US8] Ecrire les tests de validation des transitions de statut (transitions valides/invalides) dans backend/tests/test_applications/test_service.py

### Implementation US8

- [x] T052 [US8] Implementer la validation des transitions de statut dans backend/app/modules/applications/service.py (matrice de transitions autorisees)
- [x] T053 [US8] Ajouter les libelles francais contextualises par statut dans backend/app/modules/applications/schemas.py (status_label dynamique)
- [x] T054 [US8] Enrichir la page liste dossiers avec statuts en francais et filtres dans frontend/app/pages/applications/index.vue

**Checkpoint**: Statuts enrichis avec transitions validees et libelles francais.

---

## Phase 11: User Story 9 — Visualisations chat (Priority: P3)

**Goal**: Node LangGraph application_node avec visualisations mermaid, progress, chart, gauge, timeline, table dans le chat.

**Independent Test**: Demander au chat l'etat d'un dossier SUNREF/SIB, verifier qu'un mermaid et un progress s'affichent.

### Tests US9

- [x] T055 [P] [US9] Ecrire les tests pour le application_node (build_application_prompt, reponse avec blocs visuels) dans backend/tests/test_applications/test_node.py

### Implementation US9

- [x] T056 [US9] Implementer application_node avec build_application_prompt dans backend/app/graph/nodes.py
- [x] T057 [US9] Ajouter le routing "application" dans le conditional edge du router_node dans backend/app/graph/graph.py

**Checkpoint**: Chat conversationnel operationnel avec visualisations adaptees au dossier.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Ameliorations transversales et validation finale

- [ ] T058 [P] Dark mode complet sur toutes les pages applications dans frontend/app/pages/applications/index.vue et frontend/app/pages/applications/[id].vue
- [ ] T059 [P] Gestion des etats vides et erreurs (pas de dossiers, erreur generation, profil incomplet) dans frontend/app/pages/applications/index.vue et [id].vue
- [ ] T060 Verifier la couverture de tests >= 80% et completer si necessaire
- [ ] T061 Valider le quickstart.md en executant les commandes de verification rapide
- [ ] T062 Mettre a jour le CLAUDE.md avec les informations du module applications

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Pas de dependances — demarrage immediat
- **Phase 2 (Foundational)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **Phases 3-11 (User Stories)**: Dependent de Phase 2
  - US1 (P1) et US2 (P1) : peuvent demarrer en parallele apres Phase 2
  - US3 (P2) : depend de US2 (necessite intermediary_id)
  - US4 (P2), US5 (P3) : independants, parallelisables
  - US6 (P2) : independant
  - US7 (P2) : depend de US1 (generation de sections)
  - US8 (P3) : independant
  - US9 (P3) : independant (mais plus riche si US1-US8 sont en place)
- **Phase 12 (Polish)**: Depend de toutes les user stories souhaitees

### User Story Dependencies

- **US1** (fund_direct): Independant — MVP
- **US2** (intermediary_bank): Independant (reutilise US1 pour templates)
- **US3** (prep sheet): Necessite intermediary_id → apres US2
- **US4** (agence): Independant
- **US5** (carbone): Independant
- **US6** (simulation): Independant
- **US7** (regeneration): Necessite generation → apres US1
- **US8** (statuts): Independant
- **US9** (chat node): Independant

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant implementation
- Modeles/config avant services
- Services avant endpoints
- Backend avant frontend
- Commit apres chaque tache ou groupe logique

### Parallel Opportunities

- T003 + T004 (modele + templates config) en parallele
- T010 + T011 (tests service + router) en parallele
- T012 + T013 + T014 (tests US1) en parallele
- T018 + T019 (export + template HTML) en parallele
- T025 + T026 + T027 (tests US2) en parallele
- T032 + T033 (tests US3) en parallele
- US4 + US5 + US6 + US8 peuvent tous tourner en parallele

---

## Parallel Example: Phase 3 (US1)

```bash
# Tests en parallele :
Task: "Tests generation section fund_direct" (T012)
Task: "Tests export PDF/Word" (T013)
Task: "Tests endpoints generate-section, sections, export" (T014)

# Implementation parallele :
Task: "Export PDF + Word" (T018) — fichier separe export.py
Task: "Template HTML export" (T019) — fichier separe application_export.html
```

---

## Implementation Strategy

### MVP First (US1 seule)

1. Phase 1: Setup
2. Phase 2: Foundational (CRUD + routeur)
3. Phase 3: US1 — Dossier fund_direct complet (creation → generation → edition → export)
4. **STOP et VALIDER**: Tester le parcours complet fund_direct

### Incremental Delivery

1. Setup + Foundational → Base prete
2. US1 (fund_direct) → MVP ! Dossier creeable et exportable
3. US2 (intermediary_bank) → Template bancaire + checklist adaptee
4. US3 (prep sheet) → Fiche preparation PDF
5. US4 + US5 (agence + carbone) → Tous les templates
6. US6 (simulation) → Simulateur financement
7. US7 (regeneration) → UX amelioree
8. US8 (statuts) → Suivi parcours enrichi
9. US9 (chat) → Integration conversationnelle
10. Polish → Dark mode, etats vides, couverture tests

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = tracabilite vers la user story
- Chaque phase est un increment testable independamment
- Constitution : TDD obligatoire, 80% couverture
- Commit apres chaque tache ou groupe logique
