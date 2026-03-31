# Tasks: Financements Verts — BDD, Matching & Parcours d'Acces

**Input**: Design documents from `/specs/008-green-financing-matching/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Inclus (Constitution principe IV — Test-First NON-NEGOTIABLE, couverture 80%+)

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1, US2, US3, US4, US5, US6)
- Chemins exacts inclus dans chaque description

---

## Phase 1: Setup

**Purpose**: Initialisation du module financing et infrastructure partagee

- [X] T001 Creer la structure du module backend dans backend/app/modules/financing/__init__.py
- [X] T002 [P] Creer les enumerations dans backend/app/models/financing.py (FundType, FundStatus, AccessType, IntermediaryType, OrganizationType, MatchStatus, FinancingSourceType)
- [X] T003 [P] Creer le modele Fund dans backend/app/models/financing.py (table funds, tous les champs du data-model)
- [X] T004 [P] Creer le modele Intermediary dans backend/app/models/financing.py (table intermediaries)
- [X] T005 [P] Creer le modele FundIntermediary dans backend/app/models/financing.py (table fund_intermediaries, contrainte unique fund_id+intermediary_id)
- [X] T006 [P] Creer le modele FundMatch dans backend/app/models/financing.py (table fund_matches, contrainte unique user_id+fund_id)
- [X] T007 [P] Creer le modele FinancingChunk dans backend/app/models/financing.py (table financing_chunks, Vector(1536), index HNSW)
- [X] T008 Ajouter les imports des modeles financing dans backend/app/models/__init__.py
- [X] T009 Generer la migration Alembic 008_add_financing_tables et appliquer avec alembic upgrade head
- [X] T010 Creer les schemas Pydantic de base dans backend/app/modules/financing/schemas.py (FundResponse, FundSummary, FundCreate, IntermediaryResponse, IntermediarySummary, FundIntermediaryResponse, FundMatchResponse, FundMatchSummary, MatchStatusUpdate, MatchIntermediaryUpdate, FundListResponse, IntermediaryListResponse, MatchListResponse)
- [X] T011 Creer les interfaces TypeScript dans frontend/app/types/financing.ts (Fund, FundSummary, Intermediary, IntermediarySummary, FundMatch, MatchSummary, AccessType, MatchStatus)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Seed data et infrastructure RAG — DOIVENT etre complets avant les user stories

- [X] T012 Creer le script de seed dans backend/app/modules/financing/seed.py avec les 12 fonds reels (GCF, FEM, Fonds Adaptation, BOAD Ligne Verte, BAD SEFA, BIDC, SUNREF, FNDE, Gold Standard, Verra, IFC Green Bond, BCEAO refinancement vert) incluant tous les champs (access_type, intermediary_type, eligibility_criteria, sectors_eligible, esg_requirements, application_process, typical_timeline_months, success_tips)
- [X] T013 [P] Ajouter les 14+ intermediaires dans backend/app/modules/financing/seed.py (SIB, SGBCI, Banque Atlantique CI, Bridge Bank CI, Coris Bank CI, Ecobank CI, BOAD, BAD, PNUD CI, ONUDI CI, ANDE, South Pole Africa, EcoAct Afrique, FNDE) avec coordonnees reelles
- [X] T014 Ajouter les liaisons fund_intermediaries dans backend/app/modules/financing/seed.py (~50 liaisons avec roles, is_primary, geographic_coverage)
- [X] T015 Implementer la generation et le stockage des embeddings pour les fonds et intermediaires dans backend/app/modules/financing/seed.py (reutiliser OpenAIEmbeddings text-embedding-3-small, stocker dans financing_chunks)
- [X] T016 Implementer les fonctions CRUD de base dans backend/app/modules/financing/service.py (get_funds, get_fund_by_id, get_intermediaries, get_intermediary_by_id, get_fund_intermediaries, create_fund)
- [X] T017 Implementer la fonction de recherche semantique dans backend/app/modules/financing/service.py (search_financing_chunks : recherche par cosine_distance sur financing_chunks, filtrage par source_type)
- [X] T018 Creer le router de base dans backend/app/modules/financing/router.py (APIRouter, dependency get_current_user)
- [X] T019 Enregistrer le router financing dans backend/app/main.py (prefix=/api/financing, tags=["financing"])
- [X] T020 Ecrire les tests unitaires des modeles dans tests/backend/test_financing/test_models.py (creation Fund, Intermediary, FundIntermediary, FundMatch, enums, contraintes)
- [X] T021 Executer le seed et verifier que les 12 fonds, 14+ intermediaires et liaisons sont en base

**Checkpoint**: Infrastructure prete — les user stories peuvent commencer

---

## Phase 3: User Story 1 — Decouvrir les financements verts recommandes (Priority: P1) MVP

**Goal**: L'utilisateur voit les fonds verts recommandes pour son profil, tries par compatibilite, avec badges d'acces

**Independent Test**: Creer un profil PME (agriculture, Abidjan, CA 500M, ESG 65/100), verifier que les fonds recommandes sont tries par pertinence avec badges corrects

### Tests US1

- [X] T022 [P] [US1] Ecrire les tests du service de matching dans tests/backend/test_financing/test_matching.py (score par critere, ponderation, tri, cas limites : profil incomplet, aucun match, sans ESG)
- [X] T023 [P] [US1] Ecrire les tests des endpoints matching dans tests/backend/test_financing/test_router_matches.py (GET /matches, GET /matches/{fund_id}, redirection ESG manquant)

### Implementation US1

- [X] T024 [US1] Implementer le calcul de score de compatibilite dans backend/app/modules/financing/service.py (compute_compatibility_score : secteur 30%, ESG 25%, taille 15%, localisation 10%, documents 20%, chaque sous-score 0-100, moyenne ponderee)
- [X] T025 [US1] Implementer la fonction de matching dans backend/app/modules/financing/service.py (get_fund_matches : calcule le score pour chaque fonds actif, trie par score decroissant, identifie les criteres remplis et manquants)
- [X] T026 [US1] Implementer les endpoints matching dans backend/app/modules/financing/router.py (GET /matches liste paginee triee par compatibilite, GET /matches/{fund_id} detail du matching)
- [X] T027 [US1] Implementer la verification ESG dans backend/app/modules/financing/service.py (check_esg_prerequisite : verifie que l'utilisateur a un score ESG, retourne un message de redirection sinon)
- [X] T028 [US1] Creer le store Pinia dans frontend/app/stores/financing.ts (matches, funds, intermediaries, currentFund, loading, error, activeTab)
- [X] T029 [US1] Creer le composable useFinancing dans frontend/app/composables/useFinancing.ts (fetchMatches, fetchFunds, fetchIntermediaries, fetchFundDetail, updateMatchStatus, updateMatchIntermediary, fetchPreparationSheet)
- [X] T030 [US1] Creer la page principale frontend/app/pages/financing/index.vue avec l'onglet "Recommandations" par defaut (liste des matches avec : nom, organisation, score compatibilite en badge colore, badge d'acces vert/bleu/orange, montant eligible, timeline estimee, intermediaire principal recommande si via intermediaire)
- [X] T031 [US1] Ajouter l'entree "Financement" dans frontend/app/components/layout/AppSidebar.vue (navItems + icone SVG)

**Checkpoint**: L'onglet Recommandations affiche les fonds tries par compatibilite avec badges d'acces. MVP fonctionnel.

---

## Phase 4: User Story 2 — Comprendre le parcours d'acces via intermediaire (Priority: P1)

**Goal**: L'utilisateur voit le parcours d'acces complet pour chaque fonds (direct vs intermediaire), avec diagramme visuel et coordonnees des intermediaires

**Independent Test**: Consulter le detail SUNREF → voir banques partenaires avec adresses, diagramme Mermaid du parcours. Consulter le FNDE → voir "acces direct" sans intermediaire.

### Tests US2

- [X] T032 [P] [US2] Ecrire les tests du service parcours d'acces dans tests/backend/test_financing/test_service_pathway.py (generation parcours direct, intermediaire requis, mixte, intermediaires tries par proximite geographique)
- [X] T033 [P] [US2] Ecrire les tests des endpoints fonds dans tests/backend/test_financing/test_router_funds.py (GET /funds/{id} avec intermediaires, GET /funds avec filtres)

### Implementation US2

- [X] T034 [US2] Implementer la generation du parcours d'acces dans backend/app/modules/financing/service.py (generate_access_pathway : identifie access_type, trouve les intermediaires disponibles dans la zone, genere le parcours en 5 etapes via appel LLM Claude)
- [X] T035 [US2] Implementer la recommandation d'intermediaires dans backend/app/modules/financing/service.py (recommend_intermediaries : filtre par fund_id + zone geographique, trie par is_primary puis ville)
- [X] T036 [US2] Implementer les endpoints fonds dans backend/app/modules/financing/router.py (GET /funds liste avec filtres fund_type/sector/amount/access_type/status, GET /funds/{id} detail avec intermediaires lies, POST /funds admin)
- [X] T037 [US2] Creer la page detail fonds frontend/app/pages/financing/[id].vue avec : description, criteres d'eligibilite, documents requis, section "Votre compatibilite" (criteres remplis/manquants), section "Comment acceder" (direct: etapes simples / intermediaire: explication + liste intermediaires avec coordonnees + diagramme Mermaid du parcours), timeline estimee
- [X] T038 [US2] Integrer le parcours d'acces dans le endpoint GET /matches/{fund_id} dans backend/app/modules/financing/router.py (appeler generate_access_pathway et recommend_intermediaries, inclure dans la reponse)

**Checkpoint**: La page detail affiche le parcours complet. SUNREF montre les banques partenaires, FNDE montre l'acces direct.

---

## Phase 5: User Story 3 — Catalogue complet des fonds (Priority: P2)

**Goal**: L'utilisateur parcourt tous les fonds avec filtres par type, secteur, montant et mode d'acces

**Independent Test**: Verifier que les 12 fonds s'affichent, filtrer par "acces direct" → seul FNDE, filtrer par "regional" → BOAD + BIDC

### Implementation US3

- [X] T039 [US3] Ajouter l'onglet "Tous les fonds" dans frontend/app/pages/financing/index.vue avec liste complete des 12 fonds + filtres (type de fonds, secteur, montant min/max, mode d'acces, statut) + cartes avec nom, organisation, type, montants, badge acces, statut

**Checkpoint**: Les 3 onglets de la page sont visibles, l'onglet Fonds affiche les 12 fonds filtrables.

---

## Phase 6: User Story 4 — Consulter les intermediaires disponibles (Priority: P2)

**Goal**: L'utilisateur voit les intermediaires de sa zone avec leurs services et fonds couverts

**Independent Test**: Onglet Intermediaires affiche 14+ intermediaires, filtre par "banque" → 6 banques, clic sur un intermediaire → detail complet

### Tests US4

- [X] T040 [P] [US4] Ecrire les tests des endpoints intermediaires dans tests/backend/test_financing/test_router_intermediaries.py (GET /intermediaries avec filtres, GET /intermediaries/{id}, GET /intermediaries/nearby)

### Implementation US4

- [X] T041 [US4] Implementer les endpoints intermediaires dans backend/app/modules/financing/router.py (GET /intermediaries liste avec filtres type/organization_type/country/city/fund_id, GET /intermediaries/{id} detail avec fonds couverts, GET /intermediaries/nearby filtrage par ville + fund_id optionnel)
- [X] T042 [US4] Ajouter l'onglet "Intermediaires" dans frontend/app/pages/financing/index.vue avec liste filtrable par type + cartes avec nom, type organisation, ville, fonds couverts, services offerts + clic vers detail

**Checkpoint**: Les 3 onglets fonctionnent. L'onglet Intermediaires affiche et filtre les intermediaires.

---

## Phase 7: User Story 5 — Exprimer son interet et preparer sa visite (Priority: P2)

**Goal**: L'utilisateur marque son interet, choisit un intermediaire, et genere une fiche de preparation PDF

**Independent Test**: Cliquer "Je suis interesse" sur SUNREF → statut change, choisir SIB → statut "contact intermediaire", generer fiche PDF → contient resume entreprise + scores + raison compatibilite

### Tests US5

- [X] T043 [P] [US5] Ecrire les tests des endpoints statut et intermediaire dans tests/backend/test_financing/test_router_status.py (PATCH /matches/{id}/status, PATCH /matches/{id}/intermediary, transitions valides/invalides)
- [X] T044 [P] [US5] Ecrire les tests de la generation de fiche PDF dans tests/backend/test_financing/test_preparation_sheet.py (contenu, format, cas sans score ESG/carbone)

### Implementation US5

- [X] T045 [US5] Implementer les endpoints de suivi dans backend/app/modules/financing/router.py (PATCH /matches/{id}/status avec validation des transitions, PATCH /matches/{id}/intermediary avec verification que l'intermediaire est lie au fonds)
- [X] T046 [US5] Creer le template Jinja2 dans backend/app/modules/financing/preparation_template.html (resume entreprise, score ESG avec jauge, score carbone, raison compatibilite, documents disponibles, coordonnees intermediaire, etapes suivantes)
- [X] T047 [US5] Implementer la generation PDF dans backend/app/modules/financing/preparation_sheet.py (generate_preparation_sheet : charger template, remplir avec donnees profil/ESG/carbone/match, convertir en PDF via WeasyPrint)
- [X] T048 [US5] Implementer l'endpoint de telechargement dans backend/app/modules/financing/router.py (GET /matches/{match_id}/preparation-sheet retourne application/pdf)
- [X] T049 [US5] Ajouter les interactions dans frontend/app/pages/financing/[id].vue (bouton "Je suis interesse" → modale choix intermediaire → bouton "Preparer ma visite" → telechargement PDF)

**Checkpoint**: Le workflow complet fonctionne : interet → choix intermediaire → fiche PDF telechargee.

---

## Phase 8: User Story 6 — Conseils de financement via le chat (Priority: P3)

**Goal**: Le financing_node LangGraph repond aux questions sur les financements avec des blocs visuels (Mermaid, tableaux, timelines)

**Independent Test**: Demander "Comment acceder au financement SUNREF ?" → diagramme Mermaid avec banques partenaires

### Tests US6

- [X] T050 [P] [US6] Ecrire les tests du financing_node dans tests/backend/test_financing/test_financing_node.py (detection d'intention, generation de reponse avec blocs visuels, redirection ESG manquant, tableau de recommandations)

### Implementation US6

- [X] T051 [US6] Ajouter financing_data et _route_financing au state LangGraph dans backend/app/graph/state.py
- [X] T052 [US6] Ajouter les patterns regex de detection d'intention financement dans backend/app/graph/nodes.py (_FINANCING_KEYWORDS : financement, fonds vert, SUNREF, GCF, credit carbone, intermediaire, banque partenaire, etc.)
- [X] T053 [US6] Implementer financing_node dans backend/app/graph/nodes.py (acces au state complet profil+ESG+carbone, appel RAG sur financing_chunks, generation reponse avec blocs visuels : table pour recommandations, mermaid pour parcours, progress pour criteres, timeline pour processus, chart pour comparaison)
- [X] T054 [US6] Integrer financing_node dans le graphe compile dans backend/app/graph/graph.py (priorite : ESG > carbon > financing > document > chat, ajout du noeud conditionnel _route_financing)
- [X] T055 [US6] Implementer build_initial_financing_state() dans backend/app/modules/financing/service.py (helper pour initialiser financing_data dans le state quand l'utilisateur pose une question financement)

**Checkpoint**: Le chat repond aux questions de financement avec diagrammes visuels. "Comment acceder au SUNREF ?" affiche le parcours Mermaid.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Ameliorations transversales et validation finale

- [X] T056 [P] Dark mode complet sur toutes les pages/composants financing (verifier bg-white dark:bg-dark-card, text dark:text, border dark:border, hover dark:hover sur index.vue et [id].vue)
- [X] T057 [P] Ajouter la gestion des etats vides et erreurs dans frontend/app/pages/financing/index.vue (aucun match, chargement, erreur API, profil incomplet avec lien vers /profile, pas de score ESG avec lien vers /esg)
- [X] T058 [P] Ajouter la mise a jour du CLAUDE.md avec les technologies et changements de la feature 008
- [X] T059 Verification quickstart.md : executer le scenario complet (migration, seed, endpoints, page frontend, chat) et corriger les ecarts
- [X] T060 Revue de code avec l'agent code-reviewer sur les fichiers modifies

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependances — demarre immediatement
- **Foundational (Phase 2)**: Depend de la completion du Setup — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Phase 2 — Pas de dependance sur d'autres stories
- **US2 (Phase 4)**: Depend de Phase 2 — Peut utiliser les endpoints de Phase 3 mais testable independamment
- **US3 (Phase 5)**: Depend de Phase 2 — Independant (utilise GET /funds deja cree en Phase 2)
- **US4 (Phase 6)**: Depend de Phase 2 — Independant (utilise GET /intermediaries)
- **US5 (Phase 7)**: Depend de US1 (necessite les matches) — Testable des que US1 est fait
- **US6 (Phase 8)**: Depend de Phase 2 (donnees seed + RAG) — Independant des phases frontend
- **Polish (Phase 9)**: Depend de toutes les stories souhaitees

### User Story Dependencies

- **US1 (P1)**: Phase 2 → US1 (aucune dependance sur d'autres stories)
- **US2 (P1)**: Phase 2 → US2 (aucune dependance, mais enrichit US1)
- **US3 (P2)**: Phase 2 → US3 (independant)
- **US4 (P2)**: Phase 2 → US4 (independant)
- **US5 (P2)**: Phase 2 + US1 → US5 (necessite les matches de US1)
- **US6 (P3)**: Phase 2 → US6 (independant du frontend)

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant l'implementation
- Modeles avant services
- Services avant endpoints
- Backend avant frontend (pour une meme story)
- Story complete avant de passer a la priorite suivante

### Parallel Opportunities

- T002-T007 (modeles) peuvent tourner en parallele
- T012-T013 (seed fonds + intermediaires) peuvent tourner en parallele
- T022-T023, T032-T033, T040, T043-T044, T050 (tests) peuvent tourner en parallele dans chaque phase
- US3, US4, US6 peuvent etre travaillees en parallele (independantes)

---

## Parallel Example: Phase 1 Setup

```bash
# Lancer tous les modeles en parallele :
Task T002: "Creer les enumerations dans backend/app/models/financing.py"
Task T003: "Creer le modele Fund dans backend/app/models/financing.py"
Task T004: "Creer le modele Intermediary dans backend/app/models/financing.py"
Task T005: "Creer le modele FundIntermediary dans backend/app/models/financing.py"
Task T006: "Creer le modele FundMatch dans backend/app/models/financing.py"
Task T007: "Creer le modele FinancingChunk dans backend/app/models/financing.py"
```

## Parallel Example: User Story 1 Tests

```bash
# Lancer les tests US1 en parallele :
Task T022: "Tests du service de matching dans tests/backend/test_financing/test_matching.py"
Task T023: "Tests des endpoints matching dans tests/backend/test_financing/test_router_matches.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 seulement)

1. Complete Phase 1: Setup (modeles, schemas, types)
2. Complete Phase 2: Foundational (seed 12 fonds + 14 intermediaires + RAG)
3. Complete Phase 3: US1 — Recommandations avec matching (page + onglet)
4. Complete Phase 4: US2 — Parcours d'acces + detail fonds
5. **STOP et VALIDER**: Tester MVP independamment (matching + parcours + intermediaires)

### Incremental Delivery

1. Setup + Foundational → Infrastructure prete
2. US1 → Recommandations fonctionnelles (MVP!)
3. US2 → Parcours d'acces complets (MVP+)
4. US3 + US4 → Catalogue fonds + Intermediaires (en parallele)
5. US5 → Interet + fiche PDF
6. US6 → Integration chat LangGraph
7. Polish → Dark mode, etats vides, revue code

---

## Notes

- Les T002-T007 sont marques [P] car ils modifient le meme fichier financing.py mais des classes differentes — en pratique, les creer sequentiellement dans le meme fichier
- Le seed (T012-T015) est la tache la plus volumineuse (12 fonds detailles + 14 intermediaires + ~50 liaisons + embeddings)
- Le financing_node (US6) peut etre developpe en parallele du frontend car il n'a pas de dependance sur les pages Vue
- La fiche PDF (US5) reutilise le pattern WeasyPrint du module reports — s'en inspirer directement
