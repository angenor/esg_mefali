# Research: Upload et Analyse Intelligente de Documents

**Date**: 2026-03-30
**Feature**: 004-document-upload-analysis

## R1: Extraction de texte par type de fichier

### Decision
Utiliser les document loaders LangChain pour l'extraction, avec fallback OCR Tesseract pour les PDF scannes et images.

### Rationale
- LangChain fournit des loaders unifies (PyMuPDFLoader, Docx2txtLoader, UnstructuredExcelLoader) qui s'integrent nativement avec le pipeline existant.
- PyMuPDF (fitz) est rapide et fiable pour les PDF textuels.
- Tesseract (via pytesseract) est le standard open-source OCR le plus mature, avec bon support du francais.
- Pour detecter si un PDF est scanne vs textuel : tenter d'abord PyMuPDF, si le texte extrait est vide ou trop court, fallback vers OCR.

### Alternatives considered
- **pdf2image + Google Vision API** : meilleure qualite OCR mais cout par appel et dependance cloud. Rejete pour principe YAGNI et couts.
- **EasyOCR** : bonne qualite mais plus lourd (modeles PyTorch). Rejete pour simplicite.
- **Amazon Textract** : excellent mais payant et non local. Rejete pour principe stockage local d'abord.
- **Unstructured.io** : trop lourd en dependances pour ce stade. Pourra etre considere plus tard.

### Dependencies
- `pymupdf` (PyMuPDF) pour PDF textuels
- `pytesseract` + Tesseract-OCR (systeme) pour OCR
- `Pillow` pour conversion PDF scanne → image
- `pdf2image` + `poppler` pour conversion PDF → images (requis par OCR)
- `docx2txt` pour Word
- `openpyxl` pour Excel (via UnstructuredExcelLoader ou direct)

---

## R2: Chaine d'analyse LangChain

### Decision
Creer une chaine d'analyse dans `/backend/app/chains/analysis.py` qui envoie le texte extrait a Claude avec un prompt specialise par type de document.

### Rationale
- Le pattern chaine LangChain est deja utilise dans le projet (extraction.py, summarization.py).
- Un prompt specialise par type de document maximise la pertinence de l'extraction.
- Utiliser `with_structured_output()` pour obtenir un schema Pydantic en sortie (meme pattern que ProfileExtraction).

### Design
- Premiere passe : identification du type de document (classification).
- Deuxieme passe : extraction structuree adaptee au type detecte.
- Alternative : une seule passe avec prompt adaptatif. Choisie pour reduire les appels LLM et la latence.

### Prompt Strategy
Un prompt unique qui :
1. Recoit le texte + le type de document (si connu via upload, sinon auto-detecte)
2. Produit : `DocumentAnalysisOutput(document_type, summary, key_findings, structured_data, esg_relevant_info)`

---

## R3: Stockage des embeddings pgvector

### Decision
Utiliser `RecursiveCharacterTextSplitter` de LangChain pour le decoupage, et `pgvector` (deja installe) pour le stockage des embeddings.

### Rationale
- pgvector est deja dans le stack (requirements.txt).
- RecursiveCharacterTextSplitter est le standard LangChain pour le decoupage intelligent (respecte les paragraphes, phrases).
- Modele d'embedding : utiliser l'API OpenRouter/OpenAI embeddings (text-embedding-3-small) ou un modele local leger.

### Configuration
- Chunk size : 1000 caracteres
- Chunk overlap : 200 caracteres
- Separators : ["\n\n", "\n", ". ", " "]

### Table
- `document_chunks` : id, document_id, chunk_index, content (text), embedding (vector(1536)), metadata (jsonb)

---

## R4: Integration LangGraph pour le chat

### Decision
Ajouter un `document_node` dans le graphe LangGraph existant. Le `router_node` detecte la presence d'un upload et route vers `document_node` avant `chat_node`.

### Rationale
- Le pattern existant (router_node → chat_node) est extensible par design.
- Le document_node analyse le document, stocke les resultats, et injecte le resume dans le contexte pour chat_node.

### Flow
```
START → router_node → [si upload] → document_node → chat_node → END
                    → [sinon] → chat_node → END
```

### Implementation
- Le router_node detecte `has_document_upload` dans le state.
- Le document_node appelle le service d'analyse, stocke en BDD, et ajoute le resume au state.
- Le chat_node recoit le resume enrichi dans son contexte et repond avec des blocs visuels.

---

## R5: Upload multipart et stockage local

### Decision
Stockage local dans `/uploads/{user_id}/{document_id}/{filename}` avec endpoints FastAPI multipart.

### Rationale
- Principe constitution : stockage local avant S3/MinIO.
- FastAPI supporte nativement `UploadFile` pour le multipart.
- Organisation par user_id + document_id assure l'isolation et evite les collisions de noms.

### Securite
- Validation MIME type cote serveur (ne pas se fier a l'extension seule).
- Taille max 10MB via `UploadFile` + validation manuelle.
- Chemins sanitises pour prevenir le path traversal.
- Acces uniquement via API authentifiee, pas de serving statique direct.

---

## R6: Progression en temps reel

### Decision
Utiliser le meme pattern SSE que le chat existant pour emettre les evenements de progression.

### Rationale
- Le pattern SSE est deja en place et maitrise (tokens, profile_update, profile_completion).
- Nouveaux types d'evenements SSE : `document_status` avec les etapes (uploaded, extracting, analyzing, done, error).

### Events SSE supplementaires
```
{"type": "document_upload", "document_id": "uuid", "filename": "rapport.pdf"}
{"type": "document_status", "document_id": "uuid", "status": "extracting"}
{"type": "document_status", "document_id": "uuid", "status": "analyzing"}
{"type": "document_analysis", "document_id": "uuid", "summary": "...", "document_type": "bilan_financier"}
```
