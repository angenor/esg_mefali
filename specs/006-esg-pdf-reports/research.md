# Research: Génération de Rapports ESG en PDF

**Feature**: 006-esg-pdf-reports
**Date**: 2026-03-31

## R1: Bibliothèque de génération PDF

**Decision** : WeasyPrint (HTML → PDF)

**Rationale** :
- Approche HTML/CSS → PDF permet de réutiliser les compétences web pour le design du rapport
- Support natif des SVG inline (crucial pour les graphiques matplotlib)
- Support CSS `@page` pour les sauts de page, en-têtes/pieds de page, numérotation
- Bonne qualité typographique pour un rendu professionnel
- Installable via pip avec dépendances système (Pango, Cairo)

**Alternatives considered** :
- **ReportLab** : Plus bas niveau, code Python pour chaque élément visuel, maintenance plus complexe
- **xhtml2pdf** : Plus léger mais support CSS limité, rendu SVG incomplet
- **Puppeteer/Playwright** : Nécessite un navigateur headless, surdimensionné pour du PDF statique
- **PyMuPDF** (déjà installé) : Orienté lecture/extraction PDF, pas génération

## R2: Génération de graphiques

**Decision** : matplotlib avec export SVG en mémoire, intégré dans le HTML Jinja2

**Rationale** :
- matplotlib est le standard Python pour les graphiques
- L'export SVG via `io.BytesIO` + `savefig(format='svg')` produit du SVG inline
- WeasyPrint rend correctement les SVG inline dans le HTML
- Le radar chart de matplotlib (`ax.fill()` sur axes polaires) est bien documenté
- Les barres de progression peuvent être du CSS pur (plus léger que matplotlib)

**Alternatives considered** :
- **Chart.js côté serveur** : Nécessiterait Node.js, complexifie le stack
- **Plotly** : Plus lourd, orienté interactif, export SVG possible mais dépendance lourde
- **SVG pur (dessin manuel)** : Flexible mais complexe à maintenir

## R3: Template HTML du rapport

**Decision** : Jinja2 template avec CSS dédié print (pas Tailwind)

**Rationale** :
- Jinja2 est déjà dans les dépendances (via FastAPI/Starlette)
- CSS print dédié avec `@page` rules pour contrôler le layout A4
- Pas de Tailwind car les classes utilitaires ajoutent du poids CSS et les variantes `dark:` sont inutiles en print
- Structure HTML sémantique avec `<section>` par chapitre du rapport
- Sauts de page explicites avec `break-after: page` entre sections

**Alternatives considered** :
- **Tailwind pour le PDF** : Trop de CSS inutile chargé, pas de support `@page`
- **Template externe (DOCX → PDF)** : Perd la flexibilité HTML, nécessite LibreOffice

## R4: Résumé exécutif par IA

**Decision** : Chaîne LangChain avec prompt structuré, appel Claude via OpenRouter

**Rationale** :
- Le projet utilise déjà LangChain + Claude via OpenRouter pour le chat ESG
- Le résumé exécutif nécessite une génération de texte contextuel (scores, secteur, forces/faiblesses)
- Un prompt structuré avec les données de l'évaluation produit un texte cohérent de 150-300 mots
- L'appel LLM ajoute ~5-10 secondes mais la qualité rédactionnelle est indispensable

**Alternatives considered** :
- **Template statique** : Texte à trous, manque de naturel et de pertinence
- **Résumé pré-généré lors de l'évaluation** : Économise du temps à la génération mais ajoute de la complexité au flow d'évaluation

## R5: Stockage des rapports

**Decision** : Fichier PDF sur disque local (`/uploads/reports/`), métadonnées en base

**Rationale** :
- Cohérent avec le principe VII (Simplicité) de la constitution
- Le module documents utilise déjà `/uploads/` pour le stockage local
- Le modèle `Report` en base stocke le chemin, permettant la migration future vers S3/MinIO
- Pas besoin de re-générer à chaque téléchargement

**Alternatives considered** :
- **Génération à la volée** : Plus simple mais lent (30s à chaque download)
- **S3/MinIO immédiat** : Prématuré selon principe YAGNI

## R6: Performance de génération

**Decision** : Génération synchrone, optimisations CSS, cible < 30 secondes

**Rationale** :
- WeasyPrint génère un PDF 5-10 pages en 2-5 secondes
- L'appel LLM pour le résumé exécutif prend 5-10 secondes
- La génération matplotlib SVG prend < 2 secondes
- Total estimé : 10-20 secondes, bien sous la cible de 30s
- Optimisations : CSS minimal, sauts de page explicites, images SVG (pas bitmap)

**Techniques d'optimisation** :
- `break-after: page` explicite (30-94% plus rapide que pagination implicite)
- CSS minimal sans framework (pas Tailwind)
- Graphiques SVG inline (pas de fichiers externes)
- Dimensions fixes sur les éléments SVG
