# Research: 002-chat-rich-visuals

**Date**: 2026-03-30

## Decisions

### 1. Rendu Markdown dans le chat

**Decision**: Utiliser `marked` pour le parsing markdown.
**Rationale**: `marked` est le parser markdown JS le plus populaire (~34M downloads/semaine npm), rapide, extensible via tokenizers customs. Permet d'intercepter les blocs de code pour le routing vers les composants rich block. Alternative `markdown-it` est aussi viable mais `marked` a une API plus simple pour les custom renderers.
**Alternatives considered**: `markdown-it` (plus modulaire mais plus verbose), rendu markdown natif Vue (`v-html` avec DOMPurify — trop bas niveau).

### 2. Sanitization HTML (prevention XSS)

**Decision**: Utiliser `DOMPurify` pour sanitizer le HTML genere par marked avant insertion dans le DOM.
**Rationale**: Standard de l'industrie pour la sanitization HTML cote client. Compatible avec tous les navigateurs. Empêche l'injection de scripts via le markdown rendu.
**Alternatives considered**: Sanitization manuelle (trop risque), `sanitize-html` (plus lourd, oriente Node.js).

### 3. Parsing des blocs visuels (Rich Blocks)

**Decision**: Parser custom dans `useMessageParser.ts` qui split le contenu en segments texte/bloc. Les blocs sont detectes par regex sur les fenced code blocks (` ```chart `, ` ```mermaid `, etc.). Chaque segment est rendu par le composant Vue correspondant.
**Rationale**: Le streaming envoie du texte brut avec des blocs de code. Le parsing doit etre incremental (attendre la fermeture du bloc avant rendu). Un parser custom est plus previsible qu'un plugin marked pour ce cas precis.
**Alternatives considered**: Plugin marked custom (plus complexe, moins de controle sur le streaming), regex post-marked (risque de conflit avec le rendu HTML).

### 4. Jauge circulaire (GaugeBlock)

**Decision**: Implementer avec un SVG custom (arc path) plutot que Chart.js doughnut reconfigure.
**Rationale**: Un arc SVG est plus leger (~20 lignes de code), entierement customisable (couleurs, seuils, animation), et ne necessite pas de canvas. Chart.js doughnut en mode gauge est un hack (rotation, cutout) qui complexifie le code.
**Alternatives considered**: Chart.js doughnut configuree en gauge (hack, moins propre), librairie tierce gauge (dependance supplementaire non justifiee).

### 5. Generation du titre de conversation

**Decision**: Appel LLM separe (via LangChain) apres le premier echange. Le titre est genere a partir du premier message utilisateur + debut de la reponse assistant. Prompt simple : "Resume cette conversation en un titre court (5 mots max) en francais."
**Rationale**: L'approche est simple et evite de surcharger le noeud chat principal. Le titre est genere en arriere-plan apres la fin du streaming.
**Alternatives considered**: Extraction de mots-cles sans LLM (titres generiques), titre genere dans le meme appel LLM (complique le streaming).

### 6. Rate limiting frontend

**Decision**: Le rate limiting est gere cote backend (30 msg/min). Le frontend affiche le message d'erreur HTTP 429 retourne par le backend. Pas de compteur cote frontend.
**Rationale**: Le rate limiting doit etre autoritatif cote serveur. Un compteur frontend serait une duplication fragile et contournable. Le backend retourne deja un status 429 avec un message explicite.
**Alternatives considered**: Compteur frontend + backend (duplication inutile), uniquement frontend (contournable).

### 7. Librairie de rendu Markdown

**Decision**: Ajouter `marked` + `DOMPurify` comme nouvelles dependances frontend.
**Rationale**: Aucune librairie markdown n'est actuellement installee dans le projet. `marked` (1.2kB gzip) + `DOMPurify` (6kB gzip) sont legers et standards.
**Alternatives considered**: Pas de rendu markdown (mauvaise UX), rendu markdown cote serveur (latence, complexite).

## Aucun NEEDS CLARIFICATION restant

Toutes les decisions techniques sont resolues. Le plan peut avancer vers Phase 1.
