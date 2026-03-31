# Research — 009 Fund Application Generator

**Date**: 2026-03-31

## R1: Generation de contenu adapte au destinataire via LLM

**Decision**: Utiliser des system prompts differencies par target_type, injectes dans la chaine LangChain de generation. Chaque template de dossier definit ses sections, son ton et ses instructions specifiques en Python (dictionnaires de configuration).

**Rationale**: Le projet utilise deja ce pattern dans les nodes existants (financing_node, esg_scoring_node). Les instructions de ton et de vocabulaire sont integrees au system prompt, pas au modele de donnees. Cela permet d'iterer rapidement sur le contenu sans migration BDD.

**Alternatives considered**:
- Templates stockes en BDD : trop complexe pour 5 templates, pas de besoin d'edition dynamique par l'utilisateur.
- Fine-tuning du LLM par type : disproportionne pour le volume d'usage.

## R2: Pattern pour le module applications

**Decision**: Suivre le pattern existant : `backend/app/modules/applications/` avec router.py + service.py + schemas.py + templates.py (configuration des templates par target_type). Modele SQLAlchemy dans `backend/app/models/application.py`. Node LangGraph dans `backend/app/graph/nodes.py` (ajout de application_node dans le fichier existant).

**Rationale**: Coherence avec les 6 modules existants. Le node s'ajoute au fichier nodes.py existant comme les autres nodes. Le routeur est registre dans main.py.

**Alternatives considered**:
- Fichier node separe (backend/app/nodes/application.py) : le repertoire nodes/ est vide, le pattern reel est dans graph/nodes.py.

## R3: Export Word (python-docx)

**Decision**: Utiliser python-docx pour l'export Word. Le PDF continue avec WeasyPrint (deja en place). Le meme contenu HTML/Jinja2 sert de source pour les deux formats : WeasyPrint pour PDF, python-docx construit le document Word a partir des sections JSONB.

**Rationale**: python-docx est la librairie standard Python pour la generation Word, bien maintenue, sans dependances systeme. Le pattern WeasyPrint existe deja (modules reports et financing/preparation_sheet).

**Alternatives considered**:
- docx-template (template-based) : ajoute de la complexite pour un gain minimal.
- LibreOffice headless (HTML→DOCX) : dependance systeme lourde.

## R4: Fiche de preparation intermediaire PDF

**Decision**: Suivre le pattern de `financing/preparation_sheet.py` — generation on-the-fly via WeasyPrint + template Jinja2 HTML dedie. Pas de stockage du PDF en BDD, uniquement les donnees dans le JSONB intermediary_prep.

**Rationale**: Le module financing a deja exactement ce pattern. La fiche est un document compact (2-3 pages) qui peut etre regeneree a la demande.

**Alternatives considered**:
- Stocker le PDF genere sur disque : inutile car le document est petit et peut etre regenere instantanement.

## R5: Simulateur de financement

**Decision**: Calcul cote serveur dans le service, base sur les parametres du fonds (montant min/max, timeline, typical_fees de l'intermediaire). Stockage du resultat dans le JSONB simulation de FundApplication.

**Rationale**: Les donnees necessaires (montants fonds, frais intermediaire) sont deja en BDD. Le calcul est deterministe (pas besoin du LLM).

**Alternatives considered**:
- Calcul cote frontend : risque d'incoherence et de manipulation.
- Appel LLM pour la simulation : disproportionne pour des calculs arithmetiques.

## R6: Integration au graphe LangGraph

**Decision**: Ajouter un `application_node` dans `backend/app/graph/nodes.py` avec un `build_application_prompt()` qui injecte le contexte du dossier (target_type, sections, statut, checklist) dans le system prompt. Le routing dans `graph.py` ajoute une branche "application" au conditional edge du router_node.

**Rationale**: Pattern identique aux nodes financing, carbon, esg_scoring. Les blocs visuels (mermaid, progress, timeline, table, chart, gauge) sont generes par le LLM dans sa reponse textuelle et rendus cote frontend.

**Alternatives considered**:
- Node separe avec son propre graphe : over-engineering pour un seul node.

## R7: Dark mode frontend

**Decision**: Suivre les conventions CLAUDE.md — variantes `dark:` Tailwind sur tous les elements. Reutiliser les tokens existants (dark:bg-dark-card, dark:text-surface-dark-text, etc.).

**Rationale**: Convention obligatoire du projet, pattern deja en place sur toutes les pages existantes.
