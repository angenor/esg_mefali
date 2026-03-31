# Implementation Plan: Upload et Analyse Intelligente de Documents

**Branch**: `004-document-upload-analysis` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-document-upload-analysis/spec.md`

## Summary

Implementer le module d'upload et d'analyse intelligente de documents (Module 2.1), brique technique transversale permettant aux utilisateurs PME d'uploader des documents (PDF, images, Word, Excel), d'en extraire le texte (y compris OCR), de les analyser via Claude pour produire des resumes structures et des informations ESG, et de discuter des documents dans le chat avec des blocs visuels adaptes. Les embeddings sont stockes dans pgvector pour le RAG futur.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph, LangChain, SQLAlchemy (async), PyMuPDF, pytesseract, pdf2image, docx2txt, openpyxl, Nuxt 4, Vue Composition API, Pinia, TailwindCSS
**Storage**: PostgreSQL 16 + pgvector (embeddings), stockage fichiers local (/uploads/)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web (serveur Linux, navigateur desktop/mobile)
**Project Type**: Web-service (monolithe modulaire FastAPI + Nuxt)
**Performance Goals**: Analyse complete d'un document 5 pages en < 2 minutes, OCR >= 90% precision
**Constraints**: Fichiers max 10MB, 6 types MIME acceptes, acces restreint au proprietaire
**Scale/Scope**: PME individuelles, ~100 documents par utilisateur

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | Interface en francais, resumes en francais, code en anglais |
| II. Architecture Modulaire | PASS | Module `/modules/documents/` avec frontieres claires, communication via schemas Pydantic/TypeScript |
| III. Conversation-Driven UX | PASS | Upload dans le chat, discussion naturelle sur les documents, blocs visuels |
| IV. Test-First | PASS | TDD obligatoire pour chaque composant (unitaire + integration) |
| V. Securite & Donnees | PASS | Validation MIME serveur, acces par user_id, chemins sanitises, pas de secrets en code |
| VI. Inclusivite | PASS | Messages d'erreur en francais, progression temps reel, interface simple |
| VII. Simplicite & YAGNI | PASS | Stockage local, traitement synchrone, pas d'abstraction prematuree. RAG complet hors perimetre |

**Post-Phase 1 Re-check**: Tous les principes restent satisfaits. L'ajout de nouvelles dependances (PyMuPDF, pytesseract, pdf2image, docx2txt, openpyxl) est justifie par des besoins utilisateur concrets (FR-003).

## Project Structure

### Documentation (this feature)

```text
specs/004-document-upload-analysis/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-endpoints.md # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── document.py           # NEW: Document, DocumentAnalysis, DocumentChunk
│   ├── modules/
│   │   └── documents/
│   │       ├── __init__.py       # NEW
│   │       ├── router.py         # NEW: endpoints CRUD + upload + reanalyze + preview
│   │       ├── service.py        # NEW: upload, extraction, analyse, embeddings
│   │       └── schemas.py        # NEW: schemas Pydantic request/response
│   ├── chains/
│   │   └── analysis.py           # NEW: chaine d'analyse documentaire
│   ├── graph/
│   │   ├── nodes.py              # MODIFIED: ajout document_node
│   │   ├── graph.py              # MODIFIED: ajout route conditionnelle
│   │   └── state.py              # MODIFIED: ajout champs document
│   ├── prompts/
│   │   └── system.py             # MODIFIED: instructions blocs visuels documents
│   └── main.py                   # MODIFIED: include documents router
├── alembic/
│   └── versions/
│       └── xxx_add_documents.py  # NEW: migration tables documents
├── tests/
│   ├── test_document_upload.py   # NEW
│   ├── test_document_analysis.py # NEW
│   ├── test_document_api.py      # NEW
│   └── test_document_node.py     # NEW
└── uploads/                      # NEW: stockage local fichiers

frontend/
├── app/
│   ├── pages/
│   │   └── documents.vue         # NEW: page liste et detail
│   ├── components/
│   │   └── documents/
│   │       ├── DocumentUpload.vue    # NEW: drag-and-drop
│   │       ├── DocumentList.vue      # NEW: liste avec filtres
│   │       ├── DocumentDetail.vue    # NEW: vue detail
│   │       └── DocumentPreview.vue   # NEW: previsualisation
│   │   └── chat/
│   │       └── ChatInput.vue         # MODIFIED: ajout bouton trombone
│   ├── composables/
│   │   └── useDocuments.ts       # NEW
│   ├── stores/
│   │   └── documents.ts          # NEW
│   ├── types/
│   │   └── documents.ts          # NEW
│   └── components/layout/
│       └── AppSidebar.vue        # MODIFIED: ajout lien Documents
```

**Structure Decision**: Le module documents suit exactement le pattern du module company existant (`modules/documents/` avec router, service, schemas). Les modeles sont dans `models/document.py` comme les autres modeles. Le pattern est eprouve dans le projet.

## Implementation Phases

### Phase 1 : Modeles et migration BDD

**Objectif** : Creer les modeles SQLAlchemy (Document, DocumentAnalysis, DocumentChunk) et la migration Alembic.

**Fichiers** :
- `backend/app/models/document.py` — modeles avec enums, relations, indexes
- `backend/app/models/__init__.py` — import des nouveaux modeles
- `backend/alembic/versions/xxx_add_documents_tables.py` — migration

**Points d'attention** :
- Utiliser les mixins existants (UUIDMixin, TimestampMixin)
- DocumentChunk.embedding utilise `pgvector.sqlalchemy.Vector(1536)`
- Index HNSW sur le champ embedding
- Cascade delete sur Document → DocumentAnalysis et Document → DocumentChunks

---

### Phase 2 : Service d'upload et stockage local

**Objectif** : Implementer la validation, le stockage local, et les operations CRUD sur les documents.

**Fichiers** :
- `backend/app/modules/documents/schemas.py` — schemas Pydantic
- `backend/app/modules/documents/service.py` — upload_document, delete_document, list_documents, get_document
- `backend/app/modules/documents/router.py` — POST /upload, GET /, GET /{id}, DELETE /{id}
- `backend/app/main.py` — inclusion du router

**Points d'attention** :
- Validation MIME type cote serveur via `python-magic` ou verification manuelle
- Sanitisation du nom de fichier
- Creation du dossier `/uploads/{user_id}/{document_id}/`
- Suppression physique du fichier lors du DELETE

---

### Phase 3 : Extraction de texte

**Objectif** : Extraire le texte de chaque type de fichier supporte.

**Fichiers** :
- `backend/app/modules/documents/service.py` — extract_text(document) avec dispatch par MIME type

**Loaders par type** :
- PDF textuel : PyMuPDFLoader → si texte vide, fallback OCR
- PDF scanne / Images : pdf2image + pytesseract
- Word : docx2txt
- Excel : openpyxl (lecture directe des cellules)

**Points d'attention** :
- Detection PDF scanne vs textuel : si PyMuPDF retourne < 50 chars, traiter comme scanne
- Tesseract avec lang='fra+eng' pour le bilinguisme
- Gestion des erreurs (PDF protege, image corrompue)

---

### Phase 4 : Chaine d'analyse LangChain

**Objectif** : Analyser le texte extrait avec Claude pour produire un resume structure.

**Fichiers** :
- `backend/app/chains/analysis.py` — chaine d'analyse avec prompt specialise
- `backend/app/modules/documents/schemas.py` — DocumentAnalysisOutput (schema structured output)

**Design** :
- Prompt unique avec instructions adaptees au type de document
- `with_structured_output()` pour obtenir un DocumentAnalysisOutput Pydantic
- Fallback : si l'analyse echoue, stocker le texte brut et passer en statut erreur

---

### Phase 5 : Embeddings et stockage vectoriel

**Objectif** : Decouper le texte et stocker les embeddings dans pgvector.

**Fichiers** :
- `backend/app/modules/documents/service.py` — store_embeddings(document_id, text)

**Design** :
- RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
- Modele d'embedding via OpenRouter/OpenAI (text-embedding-3-small)
- Stockage dans DocumentChunk avec index HNSW

---

### Phase 6 : Integration LangGraph (document_node)

**Objectif** : Ajouter le noeud document dans le graphe LangGraph pour l'upload chat.

**Fichiers** :
- `backend/app/graph/state.py` — ajout `document_upload`, `document_analysis_summary`
- `backend/app/graph/nodes.py` — ajout `document_node`
- `backend/app/graph/graph.py` — ajout routing conditionnel
- `backend/app/api/chat.py` — modification pour accepter multipart (fichier + message)
- `backend/app/prompts/system.py` — instructions pour blocs visuels documents

**Flow** :
```
START → router_node → [has_document] → document_node → chat_node → END
                    → [no_document]  → chat_node → END
```

---

### Phase 7 : Frontend — Page Documents

**Objectif** : Creer la page /documents avec upload, liste, detail, previsualisation.

**Fichiers** :
- `frontend/app/types/documents.ts`
- `frontend/app/stores/documents.ts`
- `frontend/app/composables/useDocuments.ts`
- `frontend/app/pages/documents.vue`
- `frontend/app/components/documents/DocumentUpload.vue`
- `frontend/app/components/documents/DocumentList.vue`
- `frontend/app/components/documents/DocumentDetail.vue`
- `frontend/app/components/documents/DocumentPreview.vue`
- `frontend/app/components/layout/AppSidebar.vue` — ajout lien

---

### Phase 8 : Frontend — Integration Chat

**Objectif** : Ajouter le bouton trombone dans le chat et gerer l'upload inline.

**Fichiers** :
- `frontend/app/components/chat/ChatInput.vue` — bouton trombone, input file
- `frontend/app/composables/useChat.ts` — gestion upload + nouveaux SSE events
- `frontend/app/components/chat/ChatMessage.vue` — rendu documents dans les messages

---

### Phase 9 : Tests et polish

**Objectif** : Tests complets, gestion d'erreurs, reanalyze, et polish UI.

**Fichiers** :
- Tests unitaires : extraction, analyse, embeddings, schemas
- Tests integration : endpoints API, upload flow complet
- Tests E2E : upload depuis page documents, upload dans chat
- `backend/app/modules/documents/router.py` — POST /{id}/reanalyze
- Dark mode sur tous les composants documents

## Complexity Tracking

Aucune violation de constitution a justifier. Le plan suit les principes existants.
