# Quickstart: Upload et Analyse Intelligente de Documents

**Feature**: 004-document-upload-analysis

## Prerequisites

### Systeme
- Tesseract OCR installe : `brew install tesseract` (macOS) ou `apt install tesseract-ocr tesseract-ocr-fra` (Linux)
- Poppler installe : `brew install poppler` (macOS) ou `apt install poppler-utils` (Linux)

### Backend
```bash
cd backend
source venv/bin/activate
pip install pymupdf pytesseract pdf2image Pillow docx2txt openpyxl
```

### Base de donnees
```bash
# Appliquer la migration
alembic upgrade head
```

### Dossier uploads
```bash
mkdir -p uploads
```

## Verification rapide

### 1. Upload d'un document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "files=@test_document.pdf"
```

### 2. Verifier le statut
```bash
curl http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <token>"
```

### 3. Voir l'analyse
```bash
curl http://localhost:8000/api/documents/<document_id> \
  -H "Authorization: Bearer <token>"
```

## Structure des fichiers crees

```
backend/app/
├── modules/documents/
│   ├── __init__.py
│   ├── router.py          # Endpoints REST
│   ├── service.py          # Logique metier (upload, analyse, embeddings)
│   └── schemas.py          # Schemas Pydantic
├── models/
│   └── document.py         # Modeles SQLAlchemy (Document, DocumentAnalysis, DocumentChunk)
├── chains/
│   └── analysis.py         # Chaine LangChain d'analyse documentaire
└── graph/
    ├── nodes.py            # Modifie : ajout document_node
    ├── graph.py            # Modifie : ajout route document_node
    └── state.py            # Modifie : ajout champs document dans state

frontend/app/
├── pages/
│   └── documents.vue       # Page liste et detail documents
├── components/
│   └── documents/
│       ├── DocumentUpload.vue      # Zone drag-and-drop
│       ├── DocumentList.vue        # Liste avec filtres
│       ├── DocumentDetail.vue      # Vue detail (resume, points cles, ESG, texte brut)
│       └── DocumentPreview.vue     # Previsualisation PDF/image
├── composables/
│   └── useDocuments.ts     # Composable API documents
├── stores/
│   └── documents.ts        # Store Pinia documents
└── types/
    └── documents.ts        # Types TypeScript
```
