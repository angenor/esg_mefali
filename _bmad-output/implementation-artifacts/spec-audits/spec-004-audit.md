# Audit Rétrospectif — Spec 004 : Upload et Analyse Intelligente de Documents

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/004-document-upload-analysis/](../../../specs/004-document-upload-analysis/)
**Méthode** : rétrospective post-hoc
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Upload multi-formats (PDF textuel/scanné, image, Word, Excel) + extraction OCR + analyse IA + stockage embeddings pour RAG futur. Intégration page dédiée + chat.

| Dimension | Livré |
|-----------|-------|
| Tâches | 59 / 59 `[x]` (100 %) |
| User Stories | 5 (US1-US2 P1, US3-US4 P2, US5 P3) |
| Phases | 9 |
| Modèles nouveaux | `Document`, `DocumentAnalysis`, `DocumentChunk` (embedding vector(1536)) |
| Nouveau chain | `chains/analysis.py` (prompt par type de document) |
| Nouveau node | `document_node` (nodes.py:468) |
| Types de fichiers supportés | 6 (PDF, PNG, JPG, JPEG, DOCX, XLSX) |
| Types de documents détectés | 7 (statuts, rapport, facture, contrat, politique, bilan, autre) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture solide qui a tenu

- `document_node` wiré dans le graphe (graph.py:130) ✅ — toujours utilisé
- `DOCUMENT_TOOLS` ajoutés en spec 012 **complètent** `document_node` sans le remplacer :
  - `document_node` = déclenchement automatique quand un fichier est uploadé via chat (multipart)
  - `DOCUMENT_TOOLS` (`analyze_uploaded_document`, `get_document_analysis`, `list_user_documents`) = permet au LLM de consulter les analyses existantes
  - **Deux systèmes complémentaires**, pas redondants — contrairement à spec 003 où profiling_node est devenu dead code

### 2.2 Embeddings RAG effectivement utilisés

- `search_similar_chunks()` (service.py:469) est utilisé par `esg/service.py:312` pour enrichir le scoring ESG
- L'assumption de la spec disait *"L'exploitation des embeddings pour enrichir les reponses sera implementee dans un module ulterieur"* → promesse tenue par spec 005
- Index HNSW pgvector configuré (document.py:153) ✅

### 2.3 Garde-fous sécurité/ressources en place

- FR-002 : `MAX_FILE_SIZE = 10 * 1024 * 1024` (service.py:39) ✅
- FR-009 : `MAX_FILES_PER_UPLOAD = 5` (router.py:29) — non spécifié dans la spec mais ajouté intelligemment
- FR-017 : autorisation user_id sur tous les endpoints (T024) ✅

### 2.4 Pipeline d'analyse complet

- 6 formats pris en charge (PDF textuel via PyMuPDF, PDF scanné via pytesseract, image via OCR, Word via docx2txt, Excel via openpyxl)
- Détection automatique PDF textuel vs scanné
- Prompt spécialisé par type de document (7 types)
- Statuts clairs : uploaded → processing → analyzed | error avec option reanalyze (T023b)

### 2.5 TDD respecté

- 6 fichiers de test écrits avant implémentation (T014-T017, T025-T026, T043)
- Couverture ≥ 80% visée (T057) — CLAUDE.md mentionne "81% couverture tests" pour cette feature

---

## 3. Ce qui a posé problème

### 3.1 🟠 RAG sous-exploité : 1 module sur 8 l'utilise

- `search_similar_chunks` n'est appelé QUE par `esg/service.py`
- 7 autres modules pourraient bénéficier du RAG documentaire :
  - `carbon_node` : pourrait extraire des données d'émissions des bilans
  - `financing_node` : utilise déjà un autre RAG (sur catalog fonds) mais pas sur les documents utilisateur
  - `credit_node` : les bilans financiers uploadés sont pertinents pour le scoring crédit
  - `application_node` : les statuts juridiques et rapports d'activité devraient alimenter les dossiers de fonds
  - `action_plan_node` : les politiques internes devraient informer les recommandations
- **Cause racine** : la spec 004 a livré le stockage, mais n'a pas créé de pattern réutilisable pour l'exploitation
- **Impact** : on paie le coût des embeddings (API embedding + stockage) pour 7/8 modules qui ne les exploitent pas
- **Leçon** : quand une feature livre une brique technique "pour futur usage", cadrer un ticket de suivi explicite par module consommateur potentiel

### 3.2 🟠 Pas de limite cumulée sur le stockage par utilisateur

- 10 MB par fichier, 5 fichiers par upload, mais **pas de cap cumulé** par utilisateur
- Un utilisateur peut uploader indéfiniment, saturant `/uploads/`
- Edge case documenté : *"espace disque insuffisant → refuse l'upload"* → traite le symptôme niveau disque, pas la cause niveau utilisateur
- **Impact** : vulnérabilité d'abus ressources, surtout sans rate limiting chat (dette spec 002)
- **Leçon** : tout stockage utilisateur doit avoir un quota par compte (ex: 100 MB total ou 50 documents)

### 3.3 🟠 Pas de détection de malware

- Assumption documentée : *"la detection de malware est hors perimetre mais pourra etre ajoutee ulterieurement"*
- Mais c'est une **vraie faille** : un utilisateur peut uploader un PDF ou DOCX avec macros malveillantes
- Le fichier est stocké, accessible via `/preview`, potentiellement téléchargé par d'autres utilisateurs (si partagé un jour)
- **Leçon** : "hors périmètre" dans les assumptions est parfois un aveu de dette — documenter explicitement comme dette sécurité à résoudre avant production multi-tenant

### 3.4 🟡 `chains/analysis.py` : prompt par type de document, fragilité

- T020 : *"prompt specialise par type de document, structured output DocumentAnalysisOutput"*
- FR-005 : détection automatique parmi 7 types, avec cible SC-003 : "85% des cas"
- Problème : si la détection échoue, on passe à "autre" avec un prompt générique qui perd en qualité
- Pas de trace de métrique de précision de la détection en prod
- **Leçon** : les pipelines LLM à plusieurs étages (détection + analyse spécialisée) doivent avoir des métriques de chaque étage en observation

### 3.5 🟡 Pas de notification de fin d'analyse pour les uploads page (hors chat)

- Upload depuis le chat : SSE events `document_upload`, `document_status`, `document_analysis` (T033) ✅
- Upload depuis la page `/documents` (US1) : polling ou refresh manuel ? — pas de SSE pour cette voie
- T042 mentionne "indicateurs de progression temps reel via SSE" dans `useDocuments.ts`, mais la page n'a pas de connexion SSE ouverte en permanence
- **Impact** : l'utilisateur doit rafraîchir pour voir le statut → UX moins fluide que le chat
- **Leçon** : quand deux points d'entrée (chat + page dédiée) partagent un pipeline, ils devraient partager le même mécanisme de feedback

### 3.6 🟡 OCR : pas de stratégie pour les documents multilingues mixtes

- pytesseract configuré probablement en `fra` (français)
- Edge case non traité : PDF avec pages en français ET en anglais (fréquent dans les PME africaines francophones qui reçoivent des documents de bailleurs anglophones)
- **Leçon** : détecter la langue par page ou utiliser pytesseract avec `fra+eng`

### 3.7 🟡 `DocumentPreview.vue` via `<iframe>` PDF

- T048 : *"iframe PDF, img pour images"*
- Les iframes de PDF dépendent du viewer natif du navigateur — expérience incohérente entre Chrome/Safari/Firefox
- Pas de fallback si le navigateur ne supporte pas l'affichage inline (notamment mobile)
- **Leçon** : utiliser une bibliothèque type `pdf.js` ou `vue-pdf-embed` pour un rendu prévisible

---

## 4. Leçons transversales

1. **Briques techniques "pour futur usage" → documenter explicitement les consommateurs attendus** — sinon on paie les coûts sans la valeur.
2. **Quotas utilisateur obligatoires** sur tout stockage ou ressource cumulative.
3. **"Hors périmètre" dans les assumptions = souvent une dette** — ne pas laisser ambigu.
4. **Pipelines LLM multi-étages → observabilité par étage** — précision de détection, latence d'analyse, taux d'erreur.
5. **Deux points d'entrée → même feedback mechanism** — ou alors accepter explicitement le trade-off UX.
6. **OCR FR+EN** dès le départ pour le contexte PME africaines francophones.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Quota cumulé par utilisateur** (ex: 100 MB ou 50 documents) + message d'erreur approprié | P1 | §3.2 |
| 2 | **Exploiter RAG documentaire dans carbon/credit/application** (3 modules prioritaires) | P2 | §3.1 |
| 3 | **Détection malware** via clamav ou équivalent avant stockage | P2 | §3.3 |
| 4 | **OCR bilingue** `pytesseract.image_to_string(..., lang='fra+eng')` | ~~P2~~ → **P1** (reclassé 2026-04-16) | §3.6 |
| 5 | SSE unifié page `/documents` (aligner sur le chat) | P3 | §3.5 |
| 6 | Remplacer iframe PDF par `pdf.js` ou `vue-pdf-embed` | P3 | §3.7 |
| 7 | Observabilité : métriques de précision détection type de document | P3 | §3.4 |

**Actions déjà en place** :
- ✅ `document_node` + `DOCUMENT_TOOLS` architecturalement propres (pas de dette type spec 003)
- ✅ RAG utilisé par ESG (spec 005) — pattern de référence

---

## 6. Verdict

**Spec 004 livrée à 100 % avec une architecture solide qui a bien vieilli** — pas de dead code, `document_node` toujours central, RAG effectivement exploité par spec 005.

Les dettes sont surtout **opérationnelles** (quota, malware, OCR bilingue) plutôt que architecturales. **§3.2 quota est P1** pour protéger le stockage serveur en prod. **§3.1 RAG sous-exploité** est la dette la plus **stratégique** : on a investi dans une brique utilisée à 12,5 % de son potentiel.

---

## 7. Mise à jour 2026-04-16 — reclassement OCR bilingue P2 → **P1**

**Justification** : l'OCR français uniquement a un **impact métier direct sur le cœur de la value proposition** de la plateforme (« accès aux fonds verts »).

Les fonds climatiques internationaux majeurs — **GCF, FEM, BAD** — publient leurs documents de référence (guidelines, RFPs, requirements) majoritairement en anglais. Un utilisateur qui upload un document GCF anglais subit :

1. OCR dégradé (détection de charset approximative, mots-clés ESG anglais non reconnus)
2. → analyse ESG fausse (critères absents car non détectés dans le texte)
3. → matching financement biaisé (score de compatibilité calculé sur du texte mutilé)
4. → score crédit vert erroné (la composante documentaire est défaillante)
5. → l'entrepreneur conclut « ça ne marche pas » et abandonne

Le changement est **minimal** (un argument `lang='fra+eng'` dans l'appel `pytesseract`) mais l'impact couvre toute la chaîne de valeur de la plateforme.

P1 justifié : bloque l'onboarding d'un utilisateur qui teste avec un document anglophone (cas fréquent dès qu'on parle de financement international).
