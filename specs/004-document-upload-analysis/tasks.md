# Tasks: Upload et Analyse Intelligente de Documents

**Input**: Design documents from `/specs/004-document-upload-analysis/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Inclus (TDD obligatoire par constitution, principe IV)

**Organization**: Tasks groupees par user story pour implementation et tests independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1, US2, US3, US4, US5)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Infrastructure partagee)

**Purpose**: Installation des dependances et creation de la structure de base du module documents.

- [x] T001 Installer les dependances Python : pymupdf, pytesseract, pdf2image, Pillow, docx2txt, openpyxl dans backend/requirements.txt
- [x] T002 Verifier que Tesseract OCR et Poppler sont installes sur le systeme (documenter dans quickstart.md si besoin)
- [x] T003 Creer la structure du module backend/app/modules/documents/ (__init__.py, router.py, service.py, schemas.py)
- [x] T004 Creer le dossier uploads/ a la racine du backend et l'ajouter au .gitignore

---

## Phase 2: Foundational (Prerequis bloquants)

**Purpose**: Modeles BDD, migration et schemas Pydantic partages par toutes les user stories.

**CRITICAL**: Aucune user story ne peut demarrer avant la fin de cette phase.

- [x] T005 Creer les enums DocumentStatus et DocumentType dans backend/app/models/document.py
- [x] T006 Creer le modele Document (SQLAlchemy) avec UUIDMixin, TimestampMixin dans backend/app/models/document.py (depends on T005, meme fichier)
- [x] T007 Creer le modele DocumentAnalysis (SQLAlchemy) dans backend/app/models/document.py (depends on T006)
- [x] T008 Creer le modele DocumentChunk avec champ embedding vector(1536) dans backend/app/models/document.py (depends on T006)
- [x] T009 Mettre a jour backend/app/models/__init__.py pour importer les nouveaux modeles
- [x] T010 Generer et appliquer la migration Alembic pour les tables documents, document_analyses, document_chunks avec index HNSW
- [x] T011 [P] Creer les schemas Pydantic de base (DocumentResponse, DocumentListResponse, DocumentUploadResponse, DocumentDetailResponse, DocumentAnalysisResponse) dans backend/app/modules/documents/schemas.py
- [x] T012 [P] Creer les types TypeScript (Document, DocumentAnalysis, DocumentType, DocumentStatus) dans frontend/app/types/documents.ts
- [x] T013 Inclure le router documents dans backend/app/main.py

**Checkpoint**: Modeles, migration, schemas et types prets. Les user stories peuvent commencer.

---

## Phase 3: User Story 1 - Upload et analyse depuis la page Documents (Priority: P1) MVP

**Goal**: Un utilisateur uploade un document, le texte est extrait (y compris OCR), et l'analyse IA produit un resume structure avec points cles et informations ESG.

**Independent Test**: Uploader un PDF textuel, un PDF scanne, une image, un Word et un Excel, verifier que chaque type produit un resume et des donnees structurees.

### Tests for User Story 1

- [x] T014 [P] [US1] Test unitaire du service d'upload (validation MIME, taille, stockage) dans backend/tests/test_document_upload.py
- [x] T015 [P] [US1] Test unitaire de l'extraction de texte par type de fichier dans backend/tests/test_document_extraction.py
- [x] T016 [P] [US1] Test unitaire de la chaine d'analyse LangChain dans backend/tests/test_document_analysis_chain.py
- [x] T017 [P] [US1] Test d'integration des endpoints POST /upload, GET /, GET /{id}, DELETE /{id} dans backend/tests/test_document_api.py

### Implementation for User Story 1

- [x] T018 [US1] Implementer upload_document() dans backend/app/modules/documents/service.py : validation MIME/taille, sanitisation nom, stockage local /uploads/{user_id}/{document_id}/{filename}
- [x] T019 [US1] Implementer extract_text() dans backend/app/modules/documents/service.py : dispatch par MIME type (PyMuPDF, pytesseract, docx2txt, openpyxl), detection PDF scanne vs textuel
- [x] T020 [US1] Creer la chaine d'analyse dans backend/app/chains/analysis.py : prompt specialise par type de document, structured output DocumentAnalysisOutput
- [x] T021 [US1] Implementer analyze_document() dans backend/app/modules/documents/service.py : orchestration extraction → analyse → sauvegarde DocumentAnalysis en BDD, gestion statuts (processing → analyzed | error)
- [x] T022 [US1] Implementer les endpoints REST dans backend/app/modules/documents/router.py : POST /upload (multipart), GET / (liste paginee + filtres), GET /{id} (detail + analyse), DELETE /{id} (fichier + BDD)
- [x] T023 [US1] Implementer la logique multi-fichiers dans POST /upload : boucle sur les fichiers (max 5), validation individuelle, progression par fichier, reponse agregee dans backend/app/modules/documents/router.py et service.py
- [x] T023b [US1] Implementer le endpoint POST /{id}/reanalyze dans backend/app/modules/documents/router.py
- [x] T024 [US1] Ajouter la verification d'autorisation (user_id) sur tous les endpoints dans backend/app/modules/documents/router.py

**Checkpoint**: Upload, extraction, analyse et CRUD fonctionnent. Testable independamment via les endpoints REST.

---

## Phase 4: User Story 2 - Upload dans le chat et discussion contextuelle (Priority: P1)

**Goal**: Un utilisateur envoie un document dans le chat, le systeme l'analyse et Claude repond avec des blocs visuels adaptes. L'utilisateur peut poser des questions de suivi.

**Independent Test**: Uploader un bilan financier dans le chat, verifier que Claude repond avec un tableau des chiffres cles, puis poser une question de suivi.

### Tests for User Story 2

- [x] T025 [P] [US2] Test unitaire du document_node dans backend/tests/test_document_node.py
- [x] T026 [P] [US2] Test d'integration du flux chat avec upload document dans backend/tests/test_chat_document.py

### Implementation for User Story 2

- [x] T027 [US2] Ajouter les champs document_upload et document_analysis_summary dans backend/app/graph/state.py
- [x] T028 [US2] Implementer document_node() dans backend/app/graph/nodes.py : analyse document, injection resume dans le contexte
- [x] T029 [US2] Modifier router_node() dans backend/app/graph/nodes.py pour detecter les uploads et router vers document_node
- [x] T030 [US2] Modifier le graphe dans backend/app/graph/graph.py : ajout route conditionnelle START → router → [document_node] → chat_node → END
- [x] T031 [US2] Modifier le endpoint POST /messages dans backend/app/api/chat.py pour accepter un fichier multipart en plus du message texte
- [x] T032 [US2] Ajouter les instructions pour blocs visuels documents dans backend/app/prompts/system.py (tableau pour bilan, mermaid pour rapport activite, tableau pour facture)
- [x] T033 [US2] Emettre les evenements SSE document_upload, document_status, document_analysis dans backend/app/api/chat.py
- [x] T033b [US2] Gerer l'auto-creation d'une conversation quand un document est uploade dans le chat sans conversation active dans backend/app/api/chat.py

**Checkpoint**: Upload dans le chat fonctionne, Claude repond avec blocs visuels, questions de suivi possibles.

---

## Phase 5: User Story 3 - Gestion et consultation des documents (Priority: P2)

**Goal**: Liste des documents avec filtrage par type, vue detail (resume, points cles, ESG, texte brut), suppression et relance d'analyse.

**Independent Test**: Verifier que la liste affiche les documents filtres, que le detail montre toutes les sections, que la suppression fonctionne.

### Tests for User Story 3

- [x] T034 [P] [US3] Ecrire les tests du composable useDocuments (mock API : fetchDocuments, uploadDocuments, deleteDocument, reanalyze) dans frontend — les tests DOIVENT echouer avant implementation (T035-T036)

### Implementation for User Story 3

- [x] T035 [P] [US3] Creer le store Pinia documents dans frontend/app/stores/documents.ts
- [x] T036 [P] [US3] Creer le composable useDocuments dans frontend/app/composables/useDocuments.ts (fetchDocuments, uploadDocuments, deleteDocument, reanalyze, fetchDocumentDetail)
- [x] T037 [US3] Creer le composant DocumentUpload.vue (drag-and-drop + bouton classique) dans frontend/app/components/documents/DocumentUpload.vue
- [x] T038 [US3] Creer le composant DocumentList.vue (liste avec filtrage par type, statut, date) dans frontend/app/components/documents/DocumentList.vue
- [x] T039 [US3] Creer le composant DocumentDetail.vue (resume, points cles, ESG, texte brut en accordeon) dans frontend/app/components/documents/DocumentDetail.vue
- [x] T040 [US3] Creer la page /documents dans frontend/app/pages/documents.vue : upload zone, liste, detail, indicateurs de progression
- [x] T041 [US3] Ajouter le lien "Documents" dans frontend/app/components/layout/AppSidebar.vue
- [x] T042 [US3] Implementer les indicateurs de progression temps reel (upload → extraction → analyse → termine) via SSE dans frontend/app/composables/useDocuments.ts

**Checkpoint**: Page documents complete et fonctionnelle, navigation depuis la sidebar.

---

## Phase 6: User Story 4 - Embeddings pour le RAG (Priority: P2)

**Goal**: Apres analyse, le texte est decoupe en segments et les embeddings sont stockes dans pgvector pour la recherche semantique future.

**Independent Test**: Verifier qu'apres analyse d'un document, des chunks avec embeddings existent en BDD et qu'une recherche vectorielle retourne des resultats.

### Tests for User Story 4

- [x] T043 [P] [US4] Test unitaire du text splitting et stockage embeddings dans backend/tests/test_document_embeddings.py

### Implementation for User Story 4

- [x] T044 [US4] Implementer store_embeddings() dans backend/app/modules/documents/service.py : RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200), appel API embedding, stockage DocumentChunk
- [x] T045 [US4] Integrer store_embeddings() dans le pipeline analyze_document() dans backend/app/modules/documents/service.py (apres analyse reussie)
- [x] T046 [US4] Implementer search_similar_chunks() dans backend/app/modules/documents/service.py pour recherche vectorielle (cosine similarity)

**Checkpoint**: Embeddings stockes automatiquement, recherche vectorielle fonctionnelle.

---

## Phase 7: User Story 5 - Previsualisation des documents (Priority: P3)

**Goal**: Previsualisation basique des images et PDFs directement dans l'interface.

**Independent Test**: Verifier qu'un PDF et une image s'affichent dans un visualiseur integre.

### Implementation for User Story 5

- [x] T047 [US5] Implementer le endpoint GET /documents/{id}/preview dans backend/app/modules/documents/router.py (FileResponse avec bon Content-Type, verification autorisation)
- [x] T048 [US5] Creer le composant DocumentPreview.vue dans frontend/app/components/documents/DocumentPreview.vue (iframe PDF, img pour images)
- [x] T049 [US5] Integrer DocumentPreview dans DocumentDetail.vue dans frontend/app/components/documents/DocumentDetail.vue

**Checkpoint**: Previsualisation PDF et images fonctionne depuis la page documents.

---

## Phase 8: Frontend - Integration Chat (Priority: P1)

**Goal**: Bouton trombone dans le chat, upload inline, gestion des nouveaux evenements SSE documents.

### Implementation

- [x] T050 [US2] Modifier ChatInput.vue pour ajouter un bouton trombone (input file hidden) dans frontend/app/components/chat/ChatInput.vue
- [x] T051 [US2] Modifier useChat.ts pour envoyer un fichier en multipart avec le message dans frontend/app/composables/useChat.ts
- [x] T052 [US2] Gerer les evenements SSE document_upload, document_status, document_analysis dans frontend/app/composables/useChat.ts
- [x] T053 [US2] Afficher l'indicateur de progression document dans le chat (uploading → extracting → analyzing → done) dans frontend/app/components/chat/ChatMessage.vue

**Checkpoint**: Upload dans le chat complet avec progression et blocs visuels.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Qualite, securite, dark mode, et tests finaux.

- [x] T054 [P] Appliquer le dark mode sur tous les composants documents (DocumentUpload, DocumentList, DocumentDetail, DocumentPreview) conformement aux conventions CLAUDE.md
- [x] T055 [P] Ajouter la gestion d'erreurs complete : PDF protege, OCR echoue, analyse timeout, espace disque dans backend/app/modules/documents/service.py
- [x] T056 [P] Tests E2E : upload depuis page documents, upload dans chat, filtrage, detail, suppression
- [x] T057 Verifier la couverture de tests >= 80% sur le module documents
- [x] T058 Valider le quickstart.md : executer les commandes de verification rapide
- [x] T059 Mettre a jour CLAUDE.md avec les technologies ajoutees (004-document-upload-analysis)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Pas de dependance — peut commencer immediatement
- **Phase 2 (Foundational)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **Phase 3 (US1 - Upload/Analyse)**: Depend de Phase 2
- **Phase 4 (US2 - Chat Integration Backend)**: Depend de Phase 3 (reutilise le service d'analyse)
- **Phase 5 (US3 - Page Documents Frontend)**: Depend de Phase 3 (les endpoints doivent exister)
- **Phase 6 (US4 - Embeddings)**: Depend de Phase 3 (s'integre dans analyze_document)
- **Phase 7 (US5 - Previsualisation)**: Depend de Phase 5 (s'integre dans DocumentDetail)
- **Phase 8 (Chat Frontend)**: Depend de Phase 4 (le backend chat doit supporter les uploads)
- **Phase 9 (Polish)**: Depend de toutes les phases precedentes

### User Story Dependencies

```
Phase 2 (Foundational)
    ├── US1 (Phase 3) ─── MVP
    │   ├── US2 Backend (Phase 4)
    │   │   └── US2 Frontend (Phase 8)
    │   ├── US3 (Phase 5)
    │   │   └── US5 (Phase 7)
    │   └── US4 (Phase 6)
    └── Polish (Phase 9)
```

- **US1 est le MVP** : upload + extraction + analyse + CRUD
- **US3 et US4 peuvent s'executer en parallele** apres US1
- **US2 (backend) peut demarrer en parallele de US3** apres US1

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant l'implementation
- Modeles avant services
- Services avant endpoints
- Implementation coeur avant integration

### Parallel Opportunities

- T005 → T006 (sequentiel, meme fichier)
- T011, T012 (schemas Pydantic + types TS) en parallele
- T014, T015, T016, T017 (tests US1) en parallele
- T025, T026 (tests US2) en parallele
- T035, T036 (store + composable) en parallele
- T054, T055, T056 (polish) en parallele
- US3 (Phase 5) et US4 (Phase 6) en parallele apres Phase 3

---

## Parallel Example: User Story 1

```bash
# Lancer tous les tests US1 en parallele :
Task: "Test upload service dans backend/tests/test_document_upload.py"
Task: "Test extraction texte dans backend/tests/test_document_extraction.py"
Task: "Test chaine analyse dans backend/tests/test_document_analysis_chain.py"
Task: "Test endpoints API dans backend/tests/test_document_api.py"

# Apres les tests, les schemas sont deja prets (Phase 2)
# Implementation sequentielle : upload → extraction → analyse → endpoints
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (dependances, structure)
2. Complete Phase 2: Foundational (modeles, migration, schemas)
3. Complete Phase 3: User Story 1 (upload, extraction, analyse, CRUD)
4. **STOP and VALIDATE**: Tester via curl/Postman les endpoints upload et analyse
5. Deployer/demo si pret

### Incremental Delivery

1. Setup + Foundational → Infrastructure prete
2. US1 (Upload/Analyse) → Tester → Demo (MVP!)
3. US2 (Chat Backend) + US3 (Page Documents) en parallele → Tester → Demo
4. US4 (Embeddings) + US5 (Previsualisation) → Tester → Demo
5. US2 Frontend (Chat) → Tester → Demo
6. Polish → Release

---

## Notes

- [P] tasks = fichiers differents, pas de dependances
- [Story] label mappe la tache a une user story specifique
- Chaque user story est independamment completable et testable
- Verifier que les tests echouent avant d'implementer
- Commiter apres chaque tache ou groupe logique
- S'arreter a chaque checkpoint pour valider la story
- Le principe IV (Test-First) de la constitution est NON-NEGOTIABLE
